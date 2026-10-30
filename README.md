# Atendimentos SUS no Ceará: análise enriquecida

Atividade de Business Intelligence. Equipe: Davi Salgueiro, Diego Benevides, Eduardo Jorge, Ian Sampaio e Larissa Elias.

## Entregáveis

| Arquivo | O que é |
|---|---|
| `app.py` | Painel interativo em Streamlit (7 abas, filtros, mapa) |
| `apresentacao/Apresentacao_Atendimentos_SUS_Ceara.pptx` | Apresentação (15 slides, com notas do apresentador) |
| `relatorio/Relatorio_Analise_Enriquecida_SUS_Ceara.pdf` | Relatório do enriquecimento, coesão e análises |
| `dados/processados/` | Base enriquecida, indicadores por município e por região, log de qualidade |

## Como rodar o painel

```bash
python -m venv .venv && source .venv/bin/activate   # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Os dados processados já estão na pasta. Para refazer tudo do zero:

```bash
python src/coleta_ibge.py   # baixa IBGE (SIDRA, Localidades, Malhas), IDHM (Ipeadata) e coordenadas
python src/etl.py           # trata, cruza pelo código IBGE e valida a coesão
```

## Regenerar figuras, apresentação e relatório

```bash
python src/figuras.py                # PNGs em figuras/ (Plotly + Kaleido, precisa de Chrome)
python src/dados_apresentacao.py     # números usados nos slides e no relatório
cd apresentacao && npm install && node build.js && cd ..
python src/relatorio.py              # HTML + PDF (Playwright/Chromium)
```

## Estrutura

```
dados/brutos/        base original (DADOS.txt)
dados/ibge/          respostas das APIs do IBGE e IDHM do Ipeadata
dados/apoio/         coordenadas das sedes municipais
dados/processados/   saídas do ETL
src/                 coleta, ETL, gráficos, figuras, relatório
figuras/             gráficos e prints do painel
```
