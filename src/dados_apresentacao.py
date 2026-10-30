"""Gera apresentacao/dados.json com os números usados nos slides e no relatório (tudo vem do ETL)."""
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"


def main() -> None:
    mun = pd.read_csv(PROC / "municipios_indicadores.csv", dtype={"codigo_ibge": str})
    reg = pd.read_csv(PROC / "regioes_indicadores.csv")
    qual = json.loads((PROC / "qualidade.json").read_text())
    nomes = pd.read_csv(PROC / "atendimentos_enriquecidos.csv", usecols=["primeiro_nome"], keep_default_na=False)

    ordem_porte = ["Até 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "Acima de 500 mil"]
    porte = mun.groupby("porte").agg(at=("atendimentos", "sum"), pop=("populacao_2022", "sum"),
                                     n=("municipio", "size")).reindex(ordem_porte)
    porte["taxa"] = porte["at"] / porte["pop"] * 1e5
    idhm = mun.groupby("faixa_idhm").agg(at=("atendimentos", "sum"), pop=("populacao_2022", "sum"),
                                         n=("municipio", "size")).reindex(["Baixo", "Médio", "Alto"])
    idhm["taxa"] = idhm["at"] / idhm["pop"] * 1e5
    cap = mun.set_index("municipio").loc["Fortaleza"]
    top = mun.nlargest(10, "atendimentos")
    maiores = mun.nlargest(10, "taxa_100k")
    menores = mun.nsmallest(10, "taxa_100k")
    rmf = reg.set_index("mesorregiao").loc["Metropolitana de Fortaleza"]
    nm = nomes["primeiro_nome"].value_counts()

    out = {
        "qualidade": qual,
        "total": int(mun["atendimentos"].sum()),
        "municipios": len(mun),
        "pop_ce": int(mun["populacao_2022"].sum()),
        "taxa_estado": qual["taxa_estado_100k"],
        "mediana_taxa": float(mun["taxa_100k"].median()),
        "regioes": reg.to_dict("records"),
        "porte": [{"porte": i, **r} for i, r in porte.round(1).to_dict("index").items()],
        "idhm": [{"faixa": i, **r} for i, r in idhm.round(1).to_dict("index").items()],
        "spearman_taxa_idhm": float(mun[["taxa_100k", "idhm_2010"]].corr("spearman").iloc[0, 1]),
        "capital": {k: float(cap[k]) for k in ["populacao_2022", "atendimentos", "taxa_100k",
                                               "participacao_pop_pct", "participacao_atend_pct", "idhm_2010"]},
        "rmf": {k: float(rmf[k]) for k in ["participacao_pop_pct", "participacao_atend_pct", "taxa_100k"]},
        "top_volume": top[["municipio", "atendimentos", "taxa_100k"]].to_dict("records"),
        "maiores_taxa": maiores[["municipio", "mesorregiao", "taxa_100k", "atendimentos", "populacao_2022"]].to_dict("records"),
        "menores_taxa": menores[["municipio", "mesorregiao", "taxa_100k", "atendimentos", "populacao_2022"]].to_dict("records"),
        "top_nomes": [{"nome": k, "n": int(v)} for k, v in nm.head(10).items()],
        "pct_top4_nomes": float(nm.head(4).sum() / nm.sum() * 100),
        "top10_pct_volume": float(top["atendimentos"].sum() / mun["atendimentos"].sum() * 100),
    }
    (RAIZ / "apresentacao" / "dados.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print({k: v for k, v in out.items() if k in ["capital", "rmf", "pct_top4_nomes", "top10_pct_volume",
                                                  "spearman_taxa_idhm", "mediana_taxa"]})
    print(out["porte"], out["idhm"], sep="\n")


if __name__ == "__main__":
    main()
