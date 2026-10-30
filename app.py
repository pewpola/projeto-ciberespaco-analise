"""Dashboard: Atendimentos SUS no Ceará enriquecidos com dados do IBGE.

Uso:
    python src/etl.py          # gera dados/processados (só na primeira vez)
    streamlit run app.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "src"))
import graficos as g  # noqa: E402

PROC = RAIZ / "dados" / "processados"

st.set_page_config(page_title="Atendimentos SUS · Ceará", page_icon="🩺", layout="wide")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stMetric {{ font-family: Inter, sans-serif; }}
.block-container {{ padding-top: 3.5rem; max-width: 1400px; }}
.eyebrow {{ font-size: .78rem; font-weight: 700; letter-spacing: .16em; text-transform: uppercase; color: {g.TEAL}; }}
h1.titulo {{ font-size: 2.2rem; font-weight: 800; letter-spacing: -.02em; color: {g.INK}; margin: .2rem 0 .3rem; }}
.lead {{ color: {g.INK2}; font-size: 1.02rem; margin-bottom: 1rem; }}
.kpi {{ background: {g.SOFT}; border-radius: 12px; padding: 16px 18px; height: 100%; }}
.kpi .v {{ font-size: 1.7rem; font-weight: 800; color: {g.INK}; font-variant-numeric: tabular-nums; }}
.kpi .l {{ font-size: .84rem; color: {g.INK2}; line-height: 1.35; }}
.kpi.dark {{ background: {g.INK}; }} .kpi.dark .v {{ color: #fff; }} .kpi.dark .l {{ color: #BFD6DB; }}
.insight {{ border-left: 3px solid {g.TEAL}; background: {g.TEAL_SOFT}; padding: 10px 14px;
           border-radius: 0 8px 8px 0; color: {g.INK}; font-size: .93rem; margin: .4rem 0 1rem; }}
.insight.warn {{ border-color: {g.SAND}; background: #FBF1E1; }}
.pill {{ display: inline-block; font-size: .75rem; font-weight: 700; padding: 2px 10px; border-radius: 20px; }}
.ok {{ background: #E7F6EE; color: #067647; }} .alerta {{ background: #FEF0E6; color: #B54708; }}
.falha {{ background: #FDECEA; color: #B42318; }}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def carregar():
    mun = pd.read_csv(PROC / "municipios_indicadores.csv", dtype={"codigo_ibge": str})
    nomes = pd.read_csv(PROC / "atendimentos_enriquecidos.csv",
                        usecols=["codigo_ibge", "mesorregiao", "primeiro_nome", "sexo_provavel"],
                        dtype={"codigo_ibge": str}, keep_default_na=False)
    qual = json.loads((PROC / "qualidade.json").read_text())
    return mun, nomes, qual


if not (PROC / "municipios_indicadores.csv").exists():
    st.error("Rode `python src/etl.py` antes de abrir o dashboard.")
    st.stop()

mun_todos, nomes_todos, qual = carregar()
ano_est = qual["ano_estimativa_populacao"]

# ---------------------------------------------------------------- filtros
with st.sidebar:
    st.markdown("### Filtros")
    regioes = sorted(mun_todos["mesorregiao"].unique())
    sel_reg = st.multiselect("Mesorregião", regioes, default=regioes)
    portes = ["Até 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "Acima de 500 mil"]
    sel_porte = st.multiselect("Porte do município", portes, default=portes)
    faixas = ["Baixo", "Médio", "Alto"]
    sel_idhm = st.multiselect("Faixa de IDHM 2010", faixas, default=faixas)
    base_pop = st.radio("População usada na taxa", ["Censo 2022", f"Estimativa {ano_est}"],
                        help="O Censo é a contagem oficial; a estimativa é a projeção anual do IBGE.")
    st.divider()
    st.caption("Fontes: base de atendimentos SUS (disciplina); IBGE Censo 2022, Estimativas, "
               "API de Localidades e Malhas; Atlas do Desenvolvimento Humano (PNUD/IPEA/FJP) via Ipeadata.")

mun = mun_todos[mun_todos["mesorregiao"].isin(sel_reg) & mun_todos["porte"].isin(sel_porte)
                & mun_todos["faixa_idhm"].isin(sel_idhm)].copy()
if mun.empty:
    st.warning("Nenhum município com os filtros escolhidos.")
    st.stop()
if base_pop != "Censo 2022":
    mun["taxa_100k"] = mun["taxa_100k_estimada"]
    mun["populacao_2022"] = mun["populacao_estimada"]  # a taxa e os gráficos passam a usar a estimativa
    mun["pct_populacao"] = mun["atendimentos"] / mun["populacao_2022"] * 100

reg = mun.groupby("mesorregiao").agg(municipios=("codigo_ibge", "size"), atendimentos=("atendimentos", "sum"),
                                     populacao_2022=("populacao_2022", "sum")).reset_index()
reg["taxa_100k"] = reg["atendimentos"] / reg["populacao_2022"] * 1e5
reg["participacao_atend_pct"] = reg["atendimentos"] / reg["atendimentos"].sum() * 100
reg["participacao_pop_pct"] = reg["populacao_2022"] / reg["populacao_2022"].sum() * 100
taxa_sel = mun["atendimentos"].sum() / mun["populacao_2022"].sum() * 1e5

# ---------------------------------------------------------------- cabeçalho
st.markdown('<div class="eyebrow">Business Intelligence · Análise enriquecida</div>', unsafe_allow_html=True)
st.markdown('<h1 class="titulo">Atendimentos SUS no Ceará</h1>', unsafe_allow_html=True)
st.markdown('<div class="lead">Base de atendimentos cruzada com população, área, região e IDHM de cada município.</div>',
            unsafe_allow_html=True)

n_alerta = sum(c["status"] != "OK" for c in qual["verificacoes"])
kpis = [
    (g.br(mun["atendimentos"].sum()), "atendimentos no recorte", ""),
    (f"{len(mun)}", f"municípios de {len(mun_todos)}", ""),
    (g.br(taxa_sel), "atendimentos por 100 mil hab.", ""),
    (g.br(mun["pct_populacao"].max(), 1) + "%", "maior proporção da população atendida", ""),
    ("Confirmada", f"coesão dos dados · {n_alerta} alertas", "dark"),
]
for col, (v, l, cls) in zip(st.columns(5), kpis):
    col.markdown(f'<div class="kpi {cls}"><div class="v">{v}</div><div class="l">{l}</div></div>',
                 unsafe_allow_html=True)
st.write("")

abas = st.tabs(["Volume", "Taxa por 100 mil", "Ranking", "Mapa", "Coerência dos dados", "Perfil e IDHM", "Dados"])

# ---------------------------------------------------------------- 1. volume
with abas[0]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Atendimentos por mesorregião**")
        st.plotly_chart(g.volume_regiao(reg), use_container_width=True)
    with c2:
        st.markdown("**Peso na população × peso nos atendimentos**")
        st.plotly_chart(g.participacao_regiao(reg), use_container_width=True)
    st.markdown('<div class="insight">A Região Metropolitana tem a maior população do estado, mas só a '
                '4ª maior fatia dos atendimentos. O Noroeste e o Norte Cearense somam quase metade do volume.</div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns([1, 1.3])
    with c1:
        n = st.slider("Municípios no gráfico", 5, 30, 15, key="nvol")
        st.markdown(f"**Os {n} municípios com mais atendimentos**")
        st.plotly_chart(g.top_volume(mun, n), use_container_width=True)
    with c2:
        st.markdown("**Mesorregião › município** (área = volume, cor = taxa por 100 mil)")
        st.plotly_chart(g.treemap(mun), use_container_width=True)

# ---------------------------------------------------------------- 2. taxa
with abas[1]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Atendimentos por 100 mil habitantes, por mesorregião**")
        st.plotly_chart(g.taxa_regiao(reg, taxa_sel), use_container_width=True)
    with c2:
        st.markdown("**Taxa por porte do município**")
        st.plotly_chart(g.taxa_porte(mun), use_container_width=True)
    st.markdown('<div class="insight">Quanto menor o município, maior a taxa: cidades com até 20 mil habitantes '
                'têm cerca de 10 vezes mais atendimentos por habitante do que Fortaleza.</div>', unsafe_allow_html=True)
    st.markdown("**Como a taxa se distribui entre os municípios**")
    st.plotly_chart(g.distribuicao_taxa(mun), use_container_width=True)

# ---------------------------------------------------------------- 3. ranking
with abas[2]:
    n = st.slider("Tamanho do ranking", 5, 25, 10, key="nrank")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Maior volume proporcional** (top {n})")
        st.plotly_chart(g.ranking(mun, n, True), use_container_width=True)
    with c2:
        st.markdown(f"**Menor volume proporcional** (últimos {n})")
        st.plotly_chart(g.ranking(mun, n, False), use_container_width=True)
    st.markdown('<div class="insight warn">Os municípios com menor taxa estão quase todos na Região Metropolitana '
                '(Fortaleza, Eusébio, Caucaia, Horizonte, Itaitinga): é o achado que mais merece investigação.</div>',
                unsafe_allow_html=True)

# ---------------------------------------------------------------- 4. mapa
with abas[3]:
    c1, c2 = st.columns([1, 3])
    with c1:
        tipo = st.radio("Tipo de mapa", ["Coroplético (municípios)", "Bolhas (volume)"])
        medida = st.radio("Cor do mapa", ["taxa_100k", "atendimentos", "idhm_2010"],
                          format_func=lambda m: g.ROTULOS[m], disabled=tipo.startswith("Bolhas"))
        st.caption("Passe o mouse sobre um município para ver os números. Use a roda do mouse para dar zoom.")
    with c2:
        fig = g.mapa(mun, medida) if tipo.startswith("Coro") else g.mapa_bolhas(mun)
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------- 5. coerência
with abas[4]:
    st.markdown("**Verificações aplicadas na base enriquecida**")
    linhas = "".join(
        f"<tr><td style='padding:8px 10px;font-weight:600'>{c['verificacao']}</td>"
        f"<td style='padding:8px 10px'><span class='pill {c['status'].lower()}'>{c['status']}</span></td>"
        f"<td style='padding:8px 10px;color:{g.INK2}'>{c['detalhe']}</td></tr>"
        for c in qual["verificacoes"]
    )
    st.markdown(f"<table style='width:100%;border-collapse:collapse;font-size:.92rem'>{linhas}</table>",
                unsafe_allow_html=True)
    st.markdown('<div class="insight"><b>Conclusão: coesão confirmada.</b> Nenhum município tem mais atendimentos '
                'que habitantes, todos os registros casaram com o IBGE e o volume cresce com a população '
                f'(Spearman = {g.br(qual["spearman_pop_atend"], 2)}). A ressalva é a capital, muito abaixo do esperado '
                'para o seu tamanho.</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**População × atendimentos** (cada ponto é um município)")
        st.plotly_chart(g.dispersao_pop(mun, taxa_sel), use_container_width=True)
    with c2:
        st.markdown("**Índice de representatividade** (% dos atendimentos ÷ % da população)")
        st.plotly_chart(g.representatividade(mun), use_container_width=True)
        st.caption("Areia: abaixo do peso populacional. Teal: acima. 1 = proporcional.")
    with st.expander("Tratamentos aplicados na base bruta"):
        st.markdown(f"""
- **Município:** {g.br(qual['municipio_com_espacos_extras'])} registros com espaços à direita (campo de largura fixa, 100 caracteres) foram aparados.
- **Grafia antiga:** {g.br(qual['municipio_grafia_antiga']['ITAPAGE'])} registros com *ITAPAGÉ* foram ligados a *Itapajé* (código 2306306).
- **Chave de junção:** nome em maiúsculas e sem acento, comparado ao cadastro do IBGE; depois a ligação passa a ser pelo código IBGE de 7 dígitos.
- **Nome:** {qual['nome_caractere_invalido']} nomes com caractere corrompido (�) limpos, {qual['nome_com_digito']} com dígito no lugar de letra (J0SE) corrigido, {qual['nome_ausente']} literal "NA" marcado como não informado, {qual['nome_uma_letra']} nomes de uma letra marcados como abreviados.
""")

# ---------------------------------------------------------------- 6. perfil e IDHM
with abas[5]:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**IDHM × taxa de atendimento** (tamanho = população)")
        st.plotly_chart(g.idhm_taxa(mun), use_container_width=True)
    with c2:
        st.markdown("**Taxa por faixa de IDHM**")
        st.plotly_chart(g.taxa_faixa_idhm(mun), use_container_width=True)
    st.markdown('<div class="insight">Municípios com IDHM mais baixo têm mais atendimentos por habitante, '
                'padrão esperado onde a população depende mais do SUS.</div>', unsafe_allow_html=True)
    nm = nomes_todos[nomes_todos["codigo_ibge"].isin(mun["codigo_ibge"])]
    c1, c2 = st.columns([1.3, 1])
    with c1:
        st.markdown("**Primeiros nomes mais frequentes**")
        st.plotly_chart(g.top_nomes(nm["primeiro_nome"].value_counts()), use_container_width=True)
    with c2:
        fem = (nm["sexo_provavel"] == "Feminino").mean() * 100
        st.markdown(f'<div class="kpi dark"><div class="v">{g.br(fem, 1)}%</div>'
                    '<div class="l">dos registros têm nome provavelmente feminino</div></div>', unsafe_allow_html=True)
        st.write("")
        st.caption("Estimativa por heurística de terminação do nome (ex.: -A, -ANE, -IDE). Não é dado de sexo "
                   "registrado; serve para indicar que a base parece vir de um serviço voltado a mulheres.")

# ---------------------------------------------------------------- 7. dados
with abas[6]:
    cols = ["codigo_ibge", "municipio", "mesorregiao", "porte", "populacao_2022", "atendimentos", "taxa_100k",
            "pct_populacao", "idhm_2010", "densidade_hab_km2", "indice_representatividade", "ranking_taxa"]
    st.dataframe(mun[cols].sort_values("taxa_100k", ascending=False), use_container_width=True, hide_index=True,
                 column_config={
                     "taxa_100k": st.column_config.NumberColumn("por 100 mil", format="%.0f"),
                     "pct_populacao": st.column_config.NumberColumn("% pop.", format="%.2f"),
                     "indice_representatividade": st.column_config.NumberColumn("índice", format="%.2f"),
                     "densidade_hab_km2": st.column_config.NumberColumn("hab./km²", format="%.1f"),
                 })
    st.download_button("Baixar indicadores (CSV)", mun[cols].to_csv(index=False).encode("utf-8"),
                       "municipios_indicadores.csv", "text/csv")
