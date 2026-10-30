"""Tratamento, enriquecimento e validação de coerência da base de atendimentos SUS.

Entradas:
- dados/brutos/atendimentos_sus.csv (ID, MUNICÍPIO, PRIMEIRO_NOME)
- dados/ibge/*.json e dados/apoio/coordenadas_ce.csv (gerados por coleta_ibge.py)

Saídas em dados/processados:
- atendimentos_enriquecidos.csv: um registro por atendimento, com os dados do município
- municipios_indicadores.csv: um registro por município, com volume, taxa e indicadores
- regioes_indicadores.csv: agregado por mesorregião
- qualidade.json: log do tratamento e resultado das verificações de coerência

Uso: python src/etl.py
"""
import json
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
BRUTOS = RAIZ / "dados" / "brutos"
IBGE = RAIZ / "dados" / "ibge"
APOIO = RAIZ / "dados" / "apoio"
SAIDA = RAIZ / "dados" / "processados"

# Municípios que mudaram de grafia oficial. A chave já está normalizada.
ALIAS_MUNICIPIO = {
    "ITAPAGE": "ITAPAJE",  # grafia antiga; o cadastro atual do IBGE usa Itapajé (2306306)
}


def chave(texto: str) -> str:
    """Maiúsculas, sem acento, sem espaços duplicados: usado só para casar nomes."""
    t = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    t = re.sub(r"[^A-Z ]", " ", t.upper())
    return re.sub(r"\s+", " ", t).strip()


def br(valor: float, casas: int = 0) -> str:
    """Formata número no padrão brasileiro (1.234,5)."""
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def sidra(caminho: Path) -> pd.DataFrame:
    linhas = json.loads(caminho.read_text())[1:]
    df = pd.DataFrame(linhas)[["D1C", "D2C", "V"]]
    df["V"] = pd.to_numeric(df["V"], errors="coerce")
    return df.pivot(index="D1C", columns="D2C", values="V")


# ---------------------------------------------------------------- base IBGE
def carregar_municipios() -> tuple[pd.DataFrame, str]:
    loc = json.loads((IBGE / "localidades.json").read_text())
    mun = pd.DataFrame(
        {
            "codigo_ibge": str(m["id"]),
            "municipio": m["nome"],
            "uf": "CE",
            "mesorregiao": m["microrregiao"]["mesorregiao"]["nome"],
            "microrregiao": m["microrregiao"]["nome"],
            "regiao_intermediaria": m["regiao-imediata"]["regiao-intermediaria"]["nome"],
            "regiao_imediata": m["regiao-imediata"]["nome"],
        }
        for m in loc
    )

    censo = sidra(IBGE / "censo4714.json").rename(
        columns={"93": "populacao_2022", "6318": "area_km2", "614": "densidade_hab_km2"}
    )
    est_linhas = json.loads((IBGE / "est6579.json").read_text())
    ano_est = est_linhas[1]["D3N"]
    est = sidra(IBGE / "est6579.json").rename(columns={"9324": "populacao_estimada"})

    idhm = pd.DataFrame(json.loads((IBGE / "idhm_ce.json").read_text()))
    idhm = idhm[idhm.ano == "2010"].set_index("codigo")["idhm"].rename("idhm_2010")

    coord = pd.read_csv(APOIO / "coordenadas_ce.csv", dtype={"codigo_ibge": str})
    coord = coord.set_index("codigo_ibge")[["latitude", "longitude"]]

    mun = (
        mun.join(censo, on="codigo_ibge")
        .join(est, on="codigo_ibge")
        .join(idhm, on="codigo_ibge")
        .join(coord, on="codigo_ibge")
    )
    mun["populacao_2022"] = mun["populacao_2022"].astype(int)
    mun["populacao_estimada"] = mun["populacao_estimada"].astype(int)
    mun["faixa_idhm"] = pd.cut(
        mun["idhm_2010"],
        [0, 0.499, 0.599, 0.699, 0.799, 1],
        labels=["Muito baixo", "Baixo", "Médio", "Alto", "Muito alto"],
    ).astype(str)
    mun["porte"] = pd.cut(
        mun["populacao_2022"],
        [0, 20_000, 50_000, 100_000, 500_000, np.inf],
        labels=["Até 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "Acima de 500 mil"],
    ).astype(str)
    mun["chave"] = mun["municipio"].map(chave)
    return mun, ano_est


# ---------------------------------------------------------------- atendimentos
def tratar_atendimentos(log: dict) -> pd.DataFrame:
    # keep_default_na=False: o pandas leria o nome "NA" como nulo sem avisar
    bruto = pd.read_csv(BRUTOS / "atendimentos_sus.csv", dtype=str, keep_default_na=False)
    bruto.columns = ["id", "municipio_original", "primeiro_nome_original"]
    log["registros_lidos"] = len(bruto)
    log["ids_unicos"] = bool(bruto["id"].is_unique)
    log["ids_sequenciais"] = bool(
        (bruto["id"].astype(int).diff().dropna() == 1).all() and bruto["id"].astype(int).min() == 1
    )

    df = bruto.copy()
    df["id"] = df["id"].astype(int)

    mun_txt = df["municipio_original"].str.strip()
    log["municipio_com_espacos_extras"] = int((df["municipio_original"] != mun_txt).sum())
    df["chave"] = mun_txt.map(chave).replace(ALIAS_MUNICIPIO)
    log["municipio_grafia_antiga"] = {k: int((mun_txt.map(chave) == k).sum()) for k in ALIAS_MUNICIPIO}

    nome = df["primeiro_nome_original"].str.strip().str.upper()
    tem_simbolo = nome.str.contains("�", regex=False)
    tem_digito = nome.str.contains(r"\d")
    nome = nome.str.replace("�", "", regex=False).str.replace("0", "O", regex=False)
    vazio = nome.isin(["", "NA", "NULL", "NAN"])
    curto = (nome.str.len() == 1) & ~vazio
    log["nome_caractere_invalido"] = int(tem_simbolo.sum())
    log["nome_com_digito"] = int(tem_digito.sum())
    log["nome_ausente"] = int(vazio.sum())
    log["nome_uma_letra"] = int(curto.sum())

    df["primeiro_nome"] = nome.where(~vazio, "NÃO INFORMADO")
    df["qualidade_nome"] = np.select(
        [vazio, tem_simbolo | tem_digito, curto],
        ["ausente", "corrigido", "abreviado"],
        default="ok",
    )
    return df


def sexo_provavel(nome: str) -> str:
    """Heurística simples para nomes brasileiros: terminação em A tende a ser feminina."""
    if nome == "NÃO INFORMADO" or len(nome) < 2:
        return "Indefinido"
    excecoes_masc = {"JOSUA", "LUCA", "NOAH", "ELIAS", "JONAS", "MATIAS", "TOBIAS", "ISAIAS"}
    excecoes_fem = {"BEATRIZ", "RAQUEL", "ISABEL", "MIRIAM", "LIZ", "IRIS", "INES", "RUTH", "ESTER",
                    "SUELI", "ELIZABETH", "CARMEN", "LUCIMAR", "ROSIMAR", "LUZIMAR", "ALINE",
                    "CRISTIANE", "DAIANE", "GISELE", "LUCIENE", "SIMONE", "IVONE", "JOSIANE",
                    "ELIANE", "LILIANE", "VIVIANE", "TATIANE", "ROSANE", "ARIANE", "ADRIANE",
                    "MARLENE", "IRENE", "HELENE", "ROSILENE", "JAQUELINE", "FRANCILEIDE"}
    if nome in excecoes_fem or nome.endswith(("ANE", "ENE", "IDE", "INE", "ELE", "ETE", "LY", "Y")):
        return "Feminino"
    if nome in excecoes_masc:
        return "Masculino"
    return "Feminino" if nome.endswith("A") else "Masculino"


# ---------------------------------------------------------------- coerência
def verificar(mun: pd.DataFrame, df: pd.DataFrame, log: dict) -> list[dict]:
    checks = []

    def add(nome, status, detalhe):
        checks.append({"verificacao": nome, "status": status, "detalhe": detalhe})

    add("Identificadores", "OK" if log["ids_unicos"] and log["ids_sequenciais"] else "Alerta",
        f"{br(log['registros_lidos'])} IDs únicos e sequenciais de 1 a {br(log['registros_lidos'])}")

    sem_par = df["codigo_ibge"].isna().sum()
    add("Junção com o IBGE", "OK" if sem_par == 0 else "Falha",
        f"{br(len(df) - sem_par)} de {br(len(df))} registros casados com um código IBGE")

    presentes = mun["atendimentos"].gt(0).sum()
    add("Cobertura territorial", "OK" if presentes == len(mun) else "Alerta",
        f"{presentes} dos {len(mun)} municípios do Ceará têm atendimentos")

    acima = mun[mun["atendimentos"] > mun["populacao_2022"]]
    topo = mun.loc[mun["pct_populacao"].idxmax()]
    add("Atendimentos acima da população", "OK" if acima.empty else "Falha",
        "Nenhum município tem mais atendimentos que habitantes; o maior valor é "
        f"{br(topo['pct_populacao'], 1)}% da população ({topo['municipio']})"
        if acima.empty else f"{len(acima)} municípios acima da população")

    rho = mun[["populacao_2022", "atendimentos"]].corr(method="spearman").iloc[0, 1]
    add("Proporcionalidade à população", "OK" if rho >= 0.7 else "Alerta",
        f"Correlação de Spearman entre população e atendimentos = {br(rho, 2)}")

    q1, q3 = mun["taxa_100k"].quantile([0.25, 0.75])
    lim = q3 + 1.5 * (q3 - q1)
    outl = mun[mun["taxa_100k"] > lim].sort_values("taxa_100k", ascending=False)
    add("Valores atípicos na taxa", "Alerta" if len(outl) else "OK",
        f"Nenhum município acima do limite de {br(lim)} por 100 mil hab. (regra do IQR)" if outl.empty
        else f"{len(outl)} municípios acima de {br(lim)} por 100 mil hab.: " + ", ".join(outl["municipio"].head(6)))

    cap = mun.set_index("municipio").loc["Fortaleza"]
    add("Peso da capital", "Alerta" if cap["indice_representatividade"] < 0.5 else "OK",
        f"Fortaleza tem {br(cap['participacao_pop_pct'], 1)}% da população e "
        f"{br(cap['participacao_atend_pct'], 1)}% dos atendimentos")

    probl = log["nome_caractere_invalido"] + log["nome_com_digito"] + log["nome_ausente"]
    add("Qualidade do nome", "OK" if probl == 0 else "Alerta",
        f"{probl} nomes corrigidos ou ausentes ({br(probl / len(df) * 100, 3)}% da base)")

    log["spearman_pop_atend"] = round(float(rho), 3)
    log["limite_outlier_taxa"] = round(float(lim), 1)
    return checks


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    log: dict = {}

    mun, ano_est = carregar_municipios()
    df = tratar_atendimentos(log)

    # Enriquecimento: junção pela chave normalizada do nome do município
    cols_mun = ["codigo_ibge", "municipio", "uf", "mesorregiao", "regiao_intermediaria", "regiao_imediata",
                "populacao_2022", "idhm_2010", "faixa_idhm", "porte", "densidade_hab_km2", "chave"]
    df = df.merge(mun[cols_mun], on="chave", how="left", validate="many_to_one")
    df["sexo_provavel"] = df["primeiro_nome"].map(sexo_provavel)

    total = len(df)
    agg = df.groupby("codigo_ibge").agg(
        atendimentos=("id", "size"),
        nomes_distintos=("primeiro_nome", "nunique"),
        pct_feminino=("sexo_provavel", lambda s: (s == "Feminino").mean() * 100),
    )
    mun = mun.join(agg, on="codigo_ibge")
    mun["atendimentos"] = mun["atendimentos"].fillna(0).astype(int)
    mun["taxa_100k"] = mun["atendimentos"] / mun["populacao_2022"] * 100_000
    mun["taxa_100k_estimada"] = mun["atendimentos"] / mun["populacao_estimada"] * 100_000
    mun["pct_populacao"] = mun["atendimentos"] / mun["populacao_2022"] * 100
    mun["participacao_atend_pct"] = mun["atendimentos"] / total * 100
    mun["participacao_pop_pct"] = mun["populacao_2022"] / mun["populacao_2022"].sum() * 100
    # >1: o município recebe mais atendimentos do que o seu peso na população do estado
    mun["indice_representatividade"] = mun["participacao_atend_pct"] / mun["participacao_pop_pct"]
    mun["ranking_taxa"] = mun["taxa_100k"].rank(ascending=False, method="min").astype(int)
    mun["ranking_volume"] = mun["atendimentos"].rank(ascending=False, method="min").astype(int)

    reg = mun.groupby("mesorregiao").agg(
        municipios=("codigo_ibge", "size"),
        atendimentos=("atendimentos", "sum"),
        populacao_2022=("populacao_2022", "sum"),
    )
    reg["taxa_100k"] = reg["atendimentos"] / reg["populacao_2022"] * 100_000
    reg["participacao_atend_pct"] = reg["atendimentos"] / total * 100
    reg["participacao_pop_pct"] = reg["populacao_2022"] / reg["populacao_2022"].sum() * 100
    reg = reg.sort_values("atendimentos", ascending=False).reset_index()

    checks = verificar(mun, df, log)

    log["ano_estimativa_populacao"] = ano_est
    log["taxa_estado_100k"] = round(total / mun["populacao_2022"].sum() * 100_000, 1)
    log["populacao_ce_2022"] = int(mun["populacao_2022"].sum())
    log["pct_feminino_heuristica"] = round(float((df["sexo_provavel"] == "Feminino").mean() * 100), 1)
    log["verificacoes"] = checks

    df.drop(columns=["chave"]).to_csv(SAIDA / "atendimentos_enriquecidos.csv", index=False)
    mun.drop(columns=["chave"]).sort_values("atendimentos", ascending=False).to_csv(
        SAIDA / "municipios_indicadores.csv", index=False
    )
    reg.to_csv(SAIDA / "regioes_indicadores.csv", index=False)
    (SAIDA / "qualidade.json").write_text(json.dumps(log, ensure_ascii=False, indent=2))

    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
