"""Gráficos Plotly compartilhados entre o dashboard Streamlit e as figuras do relatório/apresentação.

Paleta segue a identidade visual da equipe (mesma do projeto OndaRent):
teal para a série principal, areia para destaque, escala sequencial teal clara -> escura.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

RAIZ = Path(__file__).resolve().parents[1]

INK, INK2, MUTED, LINE, SOFT = "#0B2530", "#3A525C", "#6B7F87", "#D9E2E5", "#F3F7F8"
TEAL, TEAL2, TEAL_SOFT, SAND = "#0E7C86", "#7FD4DC", "#E3F2F3", "#B5761F"
SEQ = [[0, "#E3F2F3"], [0.35, "#7FD4DC"], [0.7, "#0E7C86"], [1, "#0B2530"]]
DIV = [[0, SAND], [0.5, "#E6E9EA"], [1, TEAL]]
FONTE = "Inter, Segoe UI, Arial, sans-serif"

ROTULOS = {
    "atendimentos": "Atendimentos",
    "taxa_100k": "Atendimentos por 100 mil hab.",
    "populacao_2022": "População (Censo 2022)",
    "idhm_2010": "IDHM 2010",
    "densidade_hab_km2": "Densidade (hab./km²)",
    "mesorregiao": "Mesorregião",
    "municipio": "Município",
    "pct_populacao": "% da população atendida",
    "indice_representatividade": "Índice de representatividade",
}


def br(v: float, casas: int = 0) -> str:
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def estilo(fig: go.Figure, altura: int = 420, legenda: bool = False) -> go.Figure:
    for tr in fig.data:
        if tr.type == "bar" and tr.orientation == "h" and tr.text is not None:
            fig.update_xaxes(range=[0, max(tr.x) * 1.16])
            break
    fig.update_layout(
        height=altura,
        font=dict(family=FONTE, color=INK2, size=13),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=10, r=20, t=30, b=10),
        showlegend=legenda,
        separators=",.",
        hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(family=FONTE, color=INK)),
        legend=dict(orientation="h", y=1.08, x=0, title=None),
    )
    fig.update_xaxes(gridcolor=SOFT, linecolor=LINE, zeroline=False, title_font=dict(color=MUTED))
    fig.update_yaxes(gridcolor=SOFT, linecolor=LINE, zeroline=False, title_font=dict(color=MUTED))
    return fig


def _area(anel: list) -> float:
    return sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(anel, anel[1:] + anel[:1])) / 2


def malha() -> dict:
    """GeoJSON do IBGE com anéis reorientados: o mapa geo do Plotly (d3) espera o contorno externo
    em sentido horário; sem isso ele pinta o "lado de fora" do polígono e o mapa sai vazio."""
    geo = json.loads((RAIZ / "dados" / "ibge" / "malha.json").read_text())
    for f in geo["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            for i, anel in enumerate(poly):
                externo = i == 0
                if (_area(anel) > 0) == externo:  # anti-horário no externo ou horário no buraco
                    anel.reverse()
    return geo


# ---------------------------------------------------------------- 1. volume
def volume_regiao(reg: pd.DataFrame) -> go.Figure:
    d = reg.sort_values("atendimentos")
    fig = go.Figure(go.Bar(
        x=d["atendimentos"], y=d["mesorregiao"], orientation="h",
        marker=dict(color=TEAL, cornerradius=4),
        text=[br(v) for v in d["atendimentos"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=13),
        customdata=np.c_[d["municipios"], d["participacao_atend_pct"]],
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} atendimentos<br>%{customdata[0]} municípios"
                      "<br>%{customdata[1]:.1f}% do total<extra></extra>",
    ))
    fig.update_xaxes(title="Atendimentos", showgrid=True)
    return estilo(fig, 380)


def participacao_regiao(reg: pd.DataFrame) -> go.Figure:
    """Peso na população vs. peso nos atendimentos, mesma unidade (%), barras lado a lado."""
    d = reg.sort_values("participacao_pop_pct")
    fig = go.Figure()
    fig.add_bar(y=d["mesorregiao"], x=d["participacao_pop_pct"], name="% da população",
                orientation="h", marker=dict(color=LINE, cornerradius=4),
                hovertemplate="<b>%{y}</b><br>%{x:.1f}% da população do CE<extra></extra>")
    fig.add_bar(y=d["mesorregiao"], x=d["participacao_atend_pct"], name="% dos atendimentos",
                orientation="h", marker=dict(color=TEAL, cornerradius=4),
                hovertemplate="<b>%{y}</b><br>%{x:.1f}% dos atendimentos<extra></extra>")
    fig.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
    fig.update_xaxes(title="Participação no estado (%)", ticksuffix="%")
    return estilo(fig, 400, legenda=True)


def top_volume(mun: pd.DataFrame, n: int = 15) -> go.Figure:
    d = mun.nlargest(n, "atendimentos").sort_values("atendimentos")
    cores = [SAND if m == "Fortaleza" else TEAL for m in d["municipio"]]
    fig = go.Figure(go.Bar(
        x=d["atendimentos"], y=d["municipio"], orientation="h",
        marker=dict(color=cores, cornerradius=4),
        text=[br(v) for v in d["atendimentos"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=12),
        customdata=np.c_[d["mesorregiao"], d["taxa_100k"]],
        hovertemplate="<b>%{y}</b> · %{customdata[0]}<br>%{x:,.0f} atendimentos"
                      "<br>%{customdata[1]:,.0f} por 100 mil hab.<extra></extra>",
    ))
    fig.update_xaxes(title="Atendimentos")
    return estilo(fig, 34 * n + 60)


def treemap(mun: pd.DataFrame) -> go.Figure:
    fig = px.treemap(
        mun, path=[px.Constant("Ceará"), "mesorregiao", "municipio"], values="atendimentos",
        color="taxa_100k", color_continuous_scale=SEQ,
        hover_data={"taxa_100k": ":,.0f"},
    )
    fig.update_traces(
        marker=dict(line=dict(color="white", width=2)), root_color=SOFT,
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} atendimentos"
                      "<br>%{color:,.0f} por 100 mil hab.<extra></extra>",
    )
    fig.update_layout(coloraxis_colorbar=dict(title="por 100 mil", thickness=12))
    return estilo(fig, 520)


# ---------------------------------------------------------------- 2. taxa
def taxa_regiao(reg: pd.DataFrame, taxa_estado: float) -> go.Figure:
    d = reg.sort_values("taxa_100k")
    fig = go.Figure(go.Bar(
        x=d["taxa_100k"], y=d["mesorregiao"], orientation="h",
        marker=dict(color=TEAL, cornerradius=4),
        text=[br(v) for v in d["taxa_100k"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=13),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} atendimentos por 100 mil hab.<extra></extra>",
    ))
    fig.add_vline(x=taxa_estado, line=dict(color=INK, width=1.5, dash="dot"))
    fig.add_annotation(x=taxa_estado, y=1.04, yref="paper", showarrow=False, xanchor="left",
                       text=f" Ceará: {br(taxa_estado)}", font=dict(color=INK, size=12))
    fig.update_xaxes(title="Atendimentos por 100 mil habitantes")
    return estilo(fig, 380)


def taxa_porte(mun: pd.DataFrame) -> go.Figure:
    ordem = ["Até 20 mil", "20 a 50 mil", "50 a 100 mil", "100 a 500 mil", "Acima de 500 mil"]
    g = mun.groupby("porte").agg(at=("atendimentos", "sum"), pop=("populacao_2022", "sum"),
                                 n=("municipio", "size")).reindex(ordem).dropna()
    g["taxa"] = g["at"] / g["pop"] * 1e5
    fig = go.Figure(go.Bar(
        x=g.index, y=g["taxa"], marker=dict(color=TEAL, cornerradius=4),
        text=[br(v) for v in g["taxa"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=13), customdata=g["n"],
        hovertemplate="<b>%{x}</b><br>%{y:,.0f} por 100 mil hab.<br>%{customdata:.0f} municípios<extra></extra>",
    ))
    fig.update_yaxes(title="Atendimentos por 100 mil hab.")
    fig.update_xaxes(title="Porte do município (habitantes)")
    return estilo(fig, 380)


def distribuicao_taxa(mun: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Histogram(
        x=mun["taxa_100k"], xbins=dict(size=500), marker=dict(color=TEAL, line=dict(color="white", width=2)),
        hovertemplate="%{x} por 100 mil<br>%{y} municípios<extra></extra>",
    ))
    med = mun["taxa_100k"].median()
    fig.add_vline(x=med, line=dict(color=INK, width=1.5, dash="dot"))
    fig.add_annotation(x=med, y=1.04, yref="paper", showarrow=False, xanchor="left",
                       text=f" mediana: {br(med)}", font=dict(color=INK, size=12))
    fig.update_xaxes(title="Atendimentos por 100 mil hab.")
    fig.update_yaxes(title="Municípios")
    return estilo(fig, 340)


# ---------------------------------------------------------------- 3. ranking
def ranking(mun: pd.DataFrame, n: int = 10, maiores: bool = True) -> go.Figure:
    d = (mun.nlargest(n, "taxa_100k") if maiores else mun.nsmallest(n, "taxa_100k"))
    d = d.sort_values("taxa_100k", ascending=maiores)  # barras horizontais: a 1ª linha fica embaixo
    cor = TEAL if maiores else SAND
    fig = go.Figure(go.Bar(
        x=d["taxa_100k"], y=d["municipio"], orientation="h",
        marker=dict(color=cor, cornerradius=4),
        text=[br(v) for v in d["taxa_100k"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=12),
        customdata=np.c_[d["atendimentos"], d["populacao_2022"], d["mesorregiao"]],
        hovertemplate="<b>%{y}</b> · %{customdata[2]}<br>%{x:,.0f} por 100 mil hab."
                      "<br>%{customdata[0]:,.0f} atendimentos · %{customdata[1]:,.0f} hab.<extra></extra>",
    ))
    fig.update_xaxes(title="Atendimentos por 100 mil hab.")
    return estilo(fig, 34 * n + 70)


# ---------------------------------------------------------------- 4. mapa
def mapa(mun: pd.DataFrame, medida: str = "taxa_100k", tiles: bool = True) -> go.Figure:
    geo = malha()
    rot = ROTULOS.get(medida, medida)
    hover = ("<b>%{customdata[0]}</b> · %{customdata[1]}<br>%{customdata[2]:,.0f} atendimentos"
             "<br>%{customdata[3]:,.0f} por 100 mil hab.<br>%{customdata[4]:,.0f} habitantes"
             "<br>IDHM %{customdata[5]:.3f}<extra></extra>")
    cd = np.c_[mun["municipio"], mun["mesorregiao"], mun["atendimentos"], mun["taxa_100k"],
               mun["populacao_2022"], mun["idhm_2010"]]
    kw = dict(geojson=geo, locations=mun["codigo_ibge"].astype(str), featureidkey="properties.codarea",
              z=mun[medida], colorscale=SEQ, marker=dict(line=dict(color="white", width=0.8)),
              customdata=cd, hovertemplate=hover,
              colorbar=dict(title=dict(text=rot.replace(" por ", "<br>por "), side="top"), thickness=12, len=0.7))
    if tiles:
        fig = go.Figure(go.Choroplethmap(**kw, marker_opacity=0.9))
        fig.update_layout(map=dict(style="carto-positron", center=dict(lat=-5.2, lon=-39.5), zoom=5.6))
    else:
        fig = go.Figure(go.Choropleth(**kw))
        fig.update_geos(fitbounds="locations", visible=False, projection_type="mercator")
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return estilo(fig, 620)


def mapa_bolhas(mun: pd.DataFrame) -> go.Figure:
    tam = np.sqrt(mun["atendimentos"]) / np.sqrt(mun["atendimentos"].max()) * 45 + 4
    fig = go.Figure(go.Scattermap(
        lat=mun["latitude"], lon=mun["longitude"], mode="markers",
        marker=dict(size=tam, color=mun["taxa_100k"], colorscale=SEQ, opacity=0.85,
                    colorbar=dict(title=dict(text="por 100 mil", side="top"), thickness=12, len=0.7)),
        customdata=np.c_[mun["municipio"], mun["atendimentos"], mun["taxa_100k"]],
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]:,.0f} atendimentos"
                      "<br>%{customdata[2]:,.0f} por 100 mil hab.<extra></extra>",
    ))
    fig.update_layout(map=dict(style="carto-positron", center=dict(lat=-5.2, lon=-39.5), zoom=5.6))
    return estilo(fig, 620)


# ---------------------------------------------------------------- 5. coerência
def dispersao_pop(mun: pd.DataFrame, taxa_estado: float) -> go.Figure:
    """Log-log: cada ponto é um município; a linha tracejada é a taxa média do estado."""
    fig = go.Figure()
    xs = np.array([mun["populacao_2022"].min() * 0.8, mun["populacao_2022"].max() * 1.2])
    fig.add_scatter(x=xs, y=xs * taxa_estado / 1e5, mode="lines", name=f"Taxa do Ceará ({br(taxa_estado)}/100 mil)",
                    line=dict(color=MUTED, dash="dot", width=1.5), hoverinfo="skip")
    fig.add_scatter(x=xs, y=xs, mode="lines", name="Limite: 1 atendimento por habitante",
                    line=dict(color=SAND, dash="dash", width=1.5), hoverinfo="skip")
    cap = mun["municipio"] == "Fortaleza"
    for d, nome, cor in [(mun[~cap], "Municípios", TEAL), (mun[cap], "Fortaleza (capital)", SAND)]:
        fig.add_scatter(
            x=d["populacao_2022"], y=d["atendimentos"], mode="markers", name=nome,
            marker=dict(size=9, color=cor, line=dict(color="white", width=1.5)),
            customdata=np.c_[d["municipio"], d["taxa_100k"]],
            hovertemplate="<b>%{customdata[0]}</b><br>%{x:,.0f} hab.<br>%{y:,.0f} atendimentos"
                          "<br>%{customdata[1]:,.0f} por 100 mil<extra></extra>",
        )
    f = mun[cap].iloc[0]
    fig.add_annotation(x=np.log10(f["populacao_2022"]), y=np.log10(f["atendimentos"]), text="Fortaleza",
                       showarrow=True, arrowcolor=MUTED, ax=-50, ay=-35, font=dict(color=INK, size=12))
    ticks = [10, 100, 1_000, 10_000, 100_000, 1_000_000]
    rot = ["10", "100", "1 mil", "10 mil", "100 mil", "1 milhão"]
    fig.update_xaxes(type="log", title="População (Censo 2022, escala log)", tickvals=ticks, ticktext=rot)
    fig.update_yaxes(type="log", title="Atendimentos (escala log)", tickvals=ticks, ticktext=rot,
                     range=[1.4, 6.6])
    return estilo(fig, 460, legenda=True)


def representatividade(mun: pd.DataFrame) -> go.Figure:
    d = mun.sort_values("indice_representatividade")
    fig = go.Figure(go.Bar(
        x=d["municipio"], y=d["indice_representatividade"] - 1, base=1,
        marker=dict(color=d["indice_representatividade"], colorscale=DIV, cmid=1, line=dict(width=0)),
        customdata=np.c_[d["participacao_pop_pct"], d["participacao_atend_pct"]],
        hovertemplate="<b>%{x}</b><br>índice %{y:.2f}<br>%{customdata[0]:.2f}% da população"
                      "<br>%{customdata[1]:.2f}% dos atendimentos<extra></extra>",
    ))
    fig.add_hline(y=1, line=dict(color=INK, width=1))
    fig.update_xaxes(showticklabels=False, title="184 municípios, do menor para o maior índice")
    fig.update_yaxes(title="Índice (1 = proporcional à população)")
    return estilo(fig, 360)


# ---------------------------------------------------------------- extra: IDHM
def idhm_taxa(mun: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=mun["idhm_2010"], y=mun["taxa_100k"], mode="markers",
        marker=dict(size=np.sqrt(mun["populacao_2022"]) / 40 + 5, color=TEAL, opacity=0.75,
                    line=dict(color="white", width=1.5)),
        customdata=np.c_[mun["municipio"], mun["populacao_2022"]],
        hovertemplate="<b>%{customdata[0]}</b><br>IDHM %{x:.3f}<br>%{y:,.0f} por 100 mil hab."
                      "<br>%{customdata[1]:,.0f} hab.<extra></extra>",
    ))
    b = np.polyfit(mun["idhm_2010"], mun["taxa_100k"], 1)
    xs = np.linspace(mun["idhm_2010"].min(), mun["idhm_2010"].max(), 2)
    fig.add_scatter(x=xs, y=np.polyval(b, xs), mode="lines", line=dict(color=SAND, width=2), hoverinfo="skip")
    f = mun[mun["municipio"] == "Fortaleza"].iloc[0]
    fig.add_annotation(x=f["idhm_2010"], y=f["taxa_100k"], text="Fortaleza", showarrow=True,
                       arrowcolor=MUTED, ax=-40, ay=-40, font=dict(color=INK, size=12))
    fig.update_xaxes(title="IDHM 2010")
    fig.update_yaxes(title="Atendimentos por 100 mil hab.")
    return estilo(fig, 420)


def taxa_faixa_idhm(mun: pd.DataFrame) -> go.Figure:
    ordem = ["Baixo", "Médio", "Alto"]
    g = mun.groupby("faixa_idhm").agg(at=("atendimentos", "sum"), pop=("populacao_2022", "sum"),
                                      n=("municipio", "size")).reindex(ordem).dropna()
    g["taxa"] = g["at"] / g["pop"] * 1e5
    fig = go.Figure(go.Bar(
        x=[f"{i}<br><span style='font-size:11px;color:{MUTED}'>{int(n)} municípios</span>" for i, n in zip(g.index, g["n"])],
        y=g["taxa"], marker=dict(color=TEAL, cornerradius=4),
        text=[br(v) for v in g["taxa"]], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=13),
        hovertemplate="%{y:,.0f} por 100 mil hab.<extra></extra>",
    ))
    fig.update_yaxes(title="Atendimentos por 100 mil hab.")
    fig.update_xaxes(title="Faixa de IDHM 2010 (PNUD)")
    return estilo(fig, 380)


def top_nomes(df_nomes: pd.Series, n: int = 12) -> go.Figure:
    d = df_nomes.head(n)[::-1]
    fig = go.Figure(go.Bar(
        x=d.values, y=d.index, orientation="h", marker=dict(color=TEAL, cornerradius=4),
        text=[br(v) for v in d.values], textposition="outside", cliponaxis=False,
        textfont=dict(color=INK, size=12),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} registros<extra></extra>",
    ))
    fig.update_xaxes(title="Registros")
    return estilo(fig, 30 * n + 60)
