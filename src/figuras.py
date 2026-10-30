"""Exporta os gráficos do dashboard como PNG para a apresentação e o relatório.

Uso: python src/figuras.py   (requer Chrome/Chromium; aponte BROWSER_PATH se não achar)
"""
import json
from pathlib import Path

import pandas as pd
from PIL import Image, ImageChops

import graficos as g

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"
FIG = RAIZ / "figuras"


def aparar(caminho: Path, folga: int = 16) -> None:
    """Remove a borda branca que sobra em volta do gráfico."""
    im = Image.open(caminho).convert("RGB")
    caixa = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    if caixa:
        l, t, r, b = caixa
        im.crop((max(l - folga, 0), max(t - folga, 0), min(r + folga, im.width), min(b + folga, im.height))).save(caminho)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    mun = pd.read_csv(PROC / "municipios_indicadores.csv", dtype={"codigo_ibge": str})
    reg = pd.read_csv(PROC / "regioes_indicadores.csv")
    qual = json.loads((PROC / "qualidade.json").read_text())
    nomes = pd.read_csv(PROC / "atendimentos_enriquecidos.csv", usecols=["primeiro_nome"], keep_default_na=False)
    taxa = qual["taxa_estado_100k"]

    figs = {
        "01_volume_regiao": (g.volume_regiao(reg), 1000, 520),
        "02_participacao_regiao": (g.participacao_regiao(reg), 1000, 560),
        "03_top_volume": (g.top_volume(mun, 12), 1000, 560),
        "04_taxa_regiao": (g.taxa_regiao(reg, taxa), 1000, 520),
        "05_taxa_porte": (g.taxa_porte(mun), 1000, 520),
        "06_ranking_maiores": (g.ranking(mun, 10, True), 900, 520),
        "07_ranking_menores": (g.ranking(mun, 10, False), 900, 520),
        "08_mapa_taxa": (g.mapa(mun, "taxa_100k", tiles=False), 760, 820),
        "09_dispersao_pop": (g.dispersao_pop(mun, taxa), 1000, 640),
        "10_representatividade": (g.representatividade(mun), 1000, 460),
        "11_idhm_taxa": (g.idhm_taxa(mun), 1000, 560),
        "12_taxa_faixa_idhm": (g.taxa_faixa_idhm(mun), 900, 520),
        "13_top_nomes": (g.top_nomes(nomes["primeiro_nome"].value_counts(), 10), 900, 520),
        "14_distribuicao_taxa": (g.distribuicao_taxa(mun), 1000, 460),
    }
    for nome, (fig, w, h) in figs.items():
        fig.update_layout(height=h, width=w, font_size=15)
        fig.write_image(FIG / f"{nome}.png", width=w, height=h, scale=2)
        aparar(FIG / f"{nome}.png")
        print("ok", nome)


if __name__ == "__main__":
    main()
