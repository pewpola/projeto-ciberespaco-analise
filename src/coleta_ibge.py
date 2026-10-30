"""Baixa as bases públicas usadas no enriquecimento e salva em dados/ibge e dados/apoio.

Fontes:
- IBGE API de Localidades: municípios do CE com mesorregião, microrregião e regiões geográficas.
- IBGE SIDRA tabela 4714 (Censo 2022): população residente, área e densidade.
- IBGE SIDRA tabela 6579: estimativa de população mais recente.
- IBGE API de Malhas v3: polígonos dos municípios do CE (GeoJSON) para o mapa.
- Ipeadata série ADH_IDHM (Atlas do Desenvolvimento Humano, PNUD/IPEA/FJP): IDHM 1991, 2000 e 2010.
- kelvins/municipios-brasileiros (GitHub): latitude e longitude da sede de cada município.

Uso: python src/coleta_ibge.py
"""
import json
import urllib.request
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
IBGE = RAIZ / "dados" / "ibge"
APOIO = RAIZ / "dados" / "apoio"

URLS = {
    "localidades.json": "https://servicodados.ibge.gov.br/api/v1/localidades/estados/23/municipios",
    "censo4714.json": "https://apisidra.ibge.gov.br/values/t/4714/n6/in%20n3%2023/v/93,6318,614/p/2022",
    "est6579.json": "https://apisidra.ibge.gov.br/values/t/6579/n6/in%20n3%2023/v/9324/p/last",
    "malha.json": "https://servicodados.ibge.gov.br/api/v3/malhas/estados/23"
                  "?formato=application/vnd.geo%2Bjson&intrarregiao=municipio&qualidade=intermediaria",
}
URL_IDHM = "http://www.ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='ADH_IDHM')"
URL_COORD = "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"


def baixar(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=180) as r:
        return r.read()


def main() -> None:
    IBGE.mkdir(parents=True, exist_ok=True)
    APOIO.mkdir(parents=True, exist_ok=True)

    for nome, url in URLS.items():
        print("baixando", nome)
        (IBGE / nome).write_bytes(baixar(url))

    print("baixando IDHM (Ipeadata)")
    serie = json.loads(baixar(URL_IDHM))["value"]
    ce = [
        {"codigo": x["TERCODIGO"], "ano": x["VALDATA"][:4], "idhm": x["VALVALOR"]}
        for x in serie
        if str(x["TERCODIGO"]).startswith("23") and len(str(x["TERCODIGO"])) == 7
    ]
    (IBGE / "idhm_ce.json").write_text(json.dumps(ce))

    print("baixando coordenadas")
    coord = pd.read_csv(URL_COORD)
    coord[coord.codigo_uf == 23][["codigo_ibge", "nome", "latitude", "longitude", "capital"]].to_csv(
        APOIO / "coordenadas_ce.csv", index=False
    )
    print("ok")


if __name__ == "__main__":
    main()
