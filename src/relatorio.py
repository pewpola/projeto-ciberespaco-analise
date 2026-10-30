"""Gera o relatório (HTML e PDF) no mesmo estilo do relatório OndaRent.

Uso: python src/relatorio.py   (requer Playwright com Chromium; aponte CHROME_PATH se preciso)
"""
import asyncio
import json
import os
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
REL = RAIZ / "relatorio"
D = json.loads((RAIZ / "apresentacao" / "dados.json").read_text())
Q = D["qualidade"]
CAP = D["capital"]
SAIDA_PDF = REL / "Relatorio_Analise_Enriquecida_SUS_Ceara.pdf"


def br(v: float, c: int = 0) -> str:
    return f"{v:,.{c}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fig(nome: str, legenda: str, largura: str = "100%") -> str:
    return (f'<div class="figure"><img src="../figuras/{nome}.png" style="width:{largura};display:block;margin:0 auto"></div>'
            f'<p class="caption">{legenda}</p>')


reg = sorted(D["regioes"], key=lambda r: -r["atendimentos"])
nn = sum(r["participacao_atend_pct"] for r in reg if r["mesorregiao"] in ("Noroeste Cearense", "Norte Cearense"))
porte = D["porte"]
idhm = {f["faixa"]: f for f in D["idhm"]}
mai, men = D["maiores_taxa"], D["menores_taxa"]
rmf_base = sum(1 for r in men if "Metropolitana" in r["mesorregiao"])
ita = next(r for r in D["top_volume"] if r["municipio"] == "Itapipoca")

linhas_reg = "".join(
    f'<tr><td class="k">{r["mesorregiao"]}</td><td class="num">{r["municipios"]}</td>'
    f'<td class="num">{br(r["atendimentos"])}</td><td class="num">{br(r["participacao_atend_pct"], 1)}%</td>'
    f'<td class="num">{br(r["participacao_pop_pct"], 1)}%</td><td class="num">{br(r["taxa_100k"])}</td></tr>'
    for r in reg
)
linhas_check = "".join(
    f'<tr><td class="k">{c["verificacao"]}</td><td>{c["detalhe"]}</td>'
    f'<td><span class="pill {"ok" if c["status"] == "OK" else "p2"}">{c["status"]}</span></td></tr>'
    for c in Q["verificacoes"]
)
linhas_porte = "".join(
    f'<tr><td class="k">{p["porte"]}</td><td class="num">{int(p["n"])}</td><td class="num">{br(p["at"])}</td>'
    f'<td class="num">{br(p["pop"])}</td><td class="num">{br(p["taxa"])}</td></tr>'
    for p in porte
)


def ranking_tab(lista):
    return "".join(
        f'<tr><td class="num">{i}</td><td class="k">{r["municipio"]}</td><td>{r["mesorregiao"].replace(" Cearense", "").replace("Metropolitana de Fortaleza", "RMF").replace("Sertões Cearenses", "Sertões")}</td>'
        f'<td class="num">{br(r["atendimentos"])}</td><td class="num">{br(r["taxa_100k"])}</td></tr>'
        for i, r in enumerate(lista, 1)
    )


HTML = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Atendimentos SUS no Ceará - Análise Enriquecida</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="estilo.css">
<style>
.steps{{ grid-template-columns:repeat(4,1fr); }}
.formula{{ font-family:"JetBrains Mono",monospace; font-size:8.6pt; color:var(--ink); }}
</style>
</head>
<body>

<!-- CAPA -->
<div class="cover">
  <div class="top">
    <div class="eyebrow">Business Intelligence · Dados Públicos de Saúde</div>
    <h1>Análise Enriquecida de Atendimentos SUS com Informações Municipais do Ceará</h1>
    <div class="sub">Como cruzamos uma lista de atendimentos com dados do IBGE para comparar municípios de tamanhos diferentes e verificar se os dados fazem sentido.</div>
  </div>

  <div class="summary">
    <b>Resumo.</b> Recebemos uma base com {br(D["total"])} atendimentos do SUS em {D["municipios"]} municípios do Ceará, com apenas três colunas: identificador, município e primeiro nome. Tratamos os dados, corrigimos grafias e erros de codificação e <b>enriquecemos cada registro com população, área, densidade, região e IDHM</b> do município, usando fontes oficiais do IBGE e do Atlas do Desenvolvimento Humano. Com isso, calculamos a <b>taxa de atendimentos por 100 mil habitantes</b>, que permite comparar cidades pequenas e grandes. O principal achado é que o interior registra muito mais atendimentos por habitante do que a capital: {br(porte[0]["taxa"])} por 100 mil nas cidades de até 20 mil habitantes contra {br(CAP["taxa_100k"])} em Fortaleza. Nenhum município tem mais atendimentos que habitantes e todos os registros foram ligados ao IBGE, por isso <b>confirmamos a coesão dos dados</b>, com uma ressalva sobre a capital. Todo o trabalho foi feito em Python, com um painel interativo em Streamlit.
  </div>

  <div class="meta">
    <div class="team">
      <h4>Equipe</h4>
      <table>
        <tr><td>Davi Salgueiro</td><td>2315072</td></tr>
        <tr><td>Diego Benevides</td><td>2310381</td></tr>
        <tr><td>Eduardo Jorge</td><td>2310384</td></tr>
        <tr><td>Ian Sampaio</td><td>2310398</td></tr>
        <tr><td>Larissa Elias</td><td>2315032</td></tr>
      </table>
    </div>
    <div class="team">
      <h4>Conteúdo</h4>
      <table>
        <tr><td>1. Objetivo e bases de dados</td><td>p. 2</td></tr>
        <tr><td>2. Como o enriquecimento foi feito</td><td>p. 2</td></tr>
        <tr><td>3. Coesão dos dados</td><td>p. 3</td></tr>
        <tr><td>4. Análises e justificativas</td><td>p. 5</td></tr>
        <tr><td>5. Painel interativo</td><td>p. 8</td></tr>
        <tr><td>6. Conclusões e limitações</td><td>p. 8</td></tr>
      </table>
    </div>
  </div>

  <div class="foot"><span>Business Intelligence · Atendimentos SUS no Ceará</span><span>Fortaleza, outubro de 2026</span></div>
</div>

<!-- 1 -->
<section>
<h2><span class="n">1</span>Objetivo e bases de dados</h2>
<p>A atividade pede que a base de atendimentos seja enriquecida com informações dos municípios para tornar a análise mais significativa, demonstrar a coerência entre atendimentos e população e gerar visualizações de BI. Sozinha, a base não permite comparar municípios: {br(CAP["atendimentos"])} atendimentos em Fortaleza e {br(ita["atendimentos"])} em Itapipoca parecem números próximos, mas Fortaleza tem cerca de {br(CAP["populacao_2022"] / 1e6, 1)} milhões de habitantes e Itapipoca, cerca de 130 mil.</p>
<table class="t">
  <tr><th style="width:26%">Base</th><th style="width:44%">O que traz</th><th>Fonte</th></tr>
  <tr><td class="k">Atendimentos SUS</td><td>{br(D["total"])} registros: ID, município e primeiro nome</td><td>Disciplina (arquivo DADOS.txt)</td></tr>
  <tr><td class="k">Censo 2022</td><td>População residente, área (km²) e densidade (hab./km²)</td><td>IBGE, SIDRA tabela 4714</td></tr>
  <tr><td class="k">Estimativa de população</td><td>População estimada de {Q["ano_estimativa_populacao"]}, usada como teste de sensibilidade</td><td>IBGE, SIDRA tabela 6579</td></tr>
  <tr><td class="k">Divisão territorial</td><td>Código IBGE, mesorregião, microrregião, regiões intermediária e imediata</td><td>IBGE, API de Localidades</td></tr>
  <tr><td class="k">IDHM 2010</td><td>Índice de Desenvolvimento Humano Municipal do último Atlas por município</td><td>PNUD, IPEA e FJP via Ipeadata</td></tr>
  <tr><td class="k">Geografia</td><td>Polígonos dos municípios e coordenadas das sedes, para os mapas</td><td>IBGE, API de Malhas; repositório municipios-brasileiros</td></tr>
</table>
<p class="small">Todas as bases foram baixadas por script (<span class="mono">src/coleta_ibge.py</span>), o que torna o trabalho reproduzível. Usamos o Censo 2022 como população principal por ser contagem e não projeção.</p>
</section>

<!-- 2 -->
<section>
<h2><span class="n">2</span>Como o enriquecimento foi feito</h2>
<div class="steps">
  <div class="step"><div class="n">1</div><b>Tratar</b><span>padronizar textos, corrigir grafias e erros de codificação</span></div>
  <div class="step"><div class="n">2</div><b>Enriquecer</b><span>ligar cada atendimento ao código IBGE do seu município</span></div>
  <div class="step"><div class="n">3</div><b>Validar</b><span>{len(Q["verificacoes"])} verificações de coerência entre as bases</span></div>
  <div class="step"><div class="n">4</div><b>Visualizar</b><span>gráficos, ranking, mapa e painel em Streamlit</span></div>
</div>

<h3>2.1 Tratamento da base de atendimentos</h3>
<p>Antes de cruzar as bases, revisamos cada coluna. Nenhum registro foi descartado: os problemas foram corrigidos ou marcados na coluna <span class="mono">qualidade_nome</span>.</p>
<table class="t">
  <tr><th style="width:30%">Problema</th><th style="width:48%">Tratamento</th><th class="num">Registros</th></tr>
  <tr><td class="k">Município com espaços sobrando</td><td>O campo tem largura fixa de 100 caracteres. Removemos os espaços das pontas.</td><td class="num">{br(Q["municipio_com_espacos_extras"])}</td></tr>
  <tr><td class="k">Grafia antiga: ITAPAGÉ</td><td>Ligado a Itapajé, nome usado no cadastro atual do IBGE (código 2306306).</td><td class="num">{br(Q["municipio_grafia_antiga"]["ITAPAGE"])}</td></tr>
  <tr><td class="k">Caractere corrompido no nome</td><td>O símbolo de erro de codificação (como em "�MARIA") foi removido.</td><td class="num">{Q["nome_caractere_invalido"]}</td></tr>
  <tr><td class="k">Dígito no lugar de letra</td><td>"J0SE" com zero foi corrigido para JOSE.</td><td class="num">{Q["nome_com_digito"]}</td></tr>
  <tr><td class="k">Nome "NA"</td><td>O pandas lê o texto NA como valor ausente sem avisar. Lemos tudo como texto e marcamos o caso como "não informado".</td><td class="num">{Q["nome_ausente"]}</td></tr>
  <tr><td class="k">Nome com uma letra</td><td>Mantido e marcado como abreviado.</td><td class="num">{Q["nome_uma_letra"]}</td></tr>
</table>

<h3>2.2 Junção com os dados do IBGE</h3>
<p>Nomes de município não são uma boa chave: mudam de grafia e têm acentos. Por isso criamos uma <b>chave normalizada</b> (maiúsculas, sem acento e sem espaços extras), comparamos com o cadastro do IBGE e, a partir daí, toda a ligação passa a ser feita pelo <b>código IBGE de 7 dígitos</b>, que é único e estável. As demais bases do IBGE e do Ipeadata já vêm com esse código.</p>
<pre><span class="c"># src/etl.py (trecho)</span>
df[<span class="s">"chave"</span>] = df[<span class="s">"municipio_original"</span>].str.strip().map(chave).replace(ALIAS_MUNICIPIO)
df = df.merge(municipios_ibge, on=<span class="s">"chave"</span>, how=<span class="s">"left"</span>, <span class="k">validate</span>=<span class="s">"many_to_one"</span>)
<span class="c"># validate garante que cada município do IBGE aparece uma única vez do lado direito</span></pre>
<div class="callout"><b>Resultado da junção:</b> {br(D["total"])} de {br(D["total"])} registros (100%) ligados a um código IBGE, cobrindo os {D["municipios"]} municípios do Ceará.</div>

<h3>2.3 Indicadores calculados</h3>
<table class="t">
  <tr><th style="width:30%">Indicador</th><th style="width:40%">Cálculo</th><th>Para que serve</th></tr>
  <tr><td class="k">Taxa por 100 mil hab.</td><td class="formula">atendimentos ÷ população × 100.000</td><td>Comparar municípios de tamanhos diferentes</td></tr>
  <tr><td class="k">% da população atendida</td><td class="formula">atendimentos ÷ população × 100</td><td>Testar se algum município passa de 100%</td></tr>
  <tr><td class="k">Índice de representatividade</td><td class="formula">% dos atendimentos ÷ % da população</td><td>Igual a 1 quando o município recebe a parte esperada pelo seu tamanho</td></tr>
  <tr><td class="k">Porte e faixa de IDHM</td><td>Faixas de população e faixas do PNUD (baixo, médio, alto)</td><td>Agrupar municípios parecidos</td></tr>
</table>
</section>

<!-- 3 -->
<section>
<h2><span class="n">3</span>Coesão dos dados</h2>
<p>Verificar a coesão é responder se as bases fazem sentido juntas ou se têm contradições. O enunciado pede, em especial, verificar se há municípios com mais atendimentos que habitantes. Aplicamos as verificações abaixo, todas automatizadas no <span class="mono">etl.py</span>:</p>
<div style="break-inside:avoid"><table class="t">
  <tr><th style="width:26%">Verificação</th><th style="width:60%">O que encontramos</th><th>Status</th></tr>
  {linhas_check}
</table></div>
{fig("09_dispersao_pop", "<b>Figura 1.</b> População e atendimentos por município, em escala logarítmica. Todos os pontos estão bem abaixo da linha de 1 atendimento por habitante e seguem a taxa média do estado; Fortaleza fica isolada abaixo dela.", "74%")}
<div class="callout"><b>Conclusão: coesão confirmada.</b> Não há município com mais atendimentos que habitantes (o maior caso é {D["maiores_taxa"][0]["municipio"]}, com {br(D["maiores_taxa"][0]["taxa_100k"] / 1000, 1)}% da população), todos os registros casaram com o IBGE e o volume cresce junto com a população (correlação de Spearman de {br(Q["spearman_pop_atend"], 2)}). Os dois alertas não invalidam a base: os nomes afetados são {Q["nome_caractere_invalido"] + Q["nome_com_digito"] + Q["nome_ausente"]} de {br(D["total"])} registros, e o caso da capital é um achado a investigar, não uma contradição lógica.</div>
<div class="callout warn"><b>Ressalva sobre Fortaleza.</b> A capital tem {br(CAP["participacao_pop_pct"], 1)}% da população do estado e apenas {br(CAP["participacao_atend_pct"], 1)}% dos atendimentos. Hipóteses que a base não permite testar: maior cobertura por planos de saúde privados na capital, rede municipal própria fora deste registro, sub-registro, ou um programa que priorizou o interior.</div>
</section>

<!-- 4 -->
<section>
<h2><span class="n">4</span>Análises e justificativas</h2>
<p>Fizemos cinco análises, as quatro pedidas no enunciado e uma relação com o IDHM, que só é possível graças ao enriquecimento. Para cada uma, explicamos por que ela foi escolhida.</p>

<h3>4.1 Volume de atendimentos por região e município</h3>
<p><b>Por quê:</b> é a visão mais direta da base e mostra onde estão os atendimentos em números absolutos. Agrupamos por mesorregião do IBGE, divisão conhecida e com tamanho adequado para comparação (7 regiões).</p>
<table class="t">
  <tr><th>Mesorregião</th><th class="num">Municípios</th><th class="num">Atendimentos</th><th class="num">% atend.</th><th class="num">% pop.</th><th class="num">por 100 mil</th></tr>
  {linhas_reg}
</table>
{fig("02_participacao_regiao", "<b>Figura 2.</b> Participação de cada mesorregião na população do Ceará e nos atendimentos.", "68%")}
<p>O Noroeste e o Norte Cearense somam {br(nn, 1)}% dos atendimentos. A Região Metropolitana tem {br(D["rmf"]["participacao_pop_pct"], 1)}% da população, mas só {br(D["rmf"]["participacao_atend_pct"], 1)}% dos atendimentos. Entre os municípios, Fortaleza lidera em volume ({br(CAP["atendimentos"])}), seguida de Itapipoca ({br(ita["atendimentos"])}); os 10 maiores concentram {br(D["top10_pct_volume"], 1)}% do total.</p>

<h3>4.2 Atendimentos por 100 mil habitantes</h3>
<p><b>Por quê:</b> o volume absoluto favorece cidades grandes. A taxa por 100 mil habitantes, padrão em indicadores de saúde, coloca todos os municípios na mesma régua.</p>
<div class="kpis">
  <div class="kpi"><div class="v">{br(D["taxa_estado"])}</div><div class="l">atendimentos por 100 mil hab. no Ceará</div></div>
  <div class="kpi"><div class="v">{br(D["mediana_taxa"])}</div><div class="l">mediana entre os 184 municípios</div></div>
  <div class="kpi"><div class="v">{br(porte[0]["taxa"])}</div><div class="l">nas cidades de até 20 mil hab.</div></div>
  <div class="kpi"><div class="v">{br(CAP["taxa_100k"])}</div><div class="l">em Fortaleza, a menor do estado</div></div>
</div>
<table class="t">
  <tr><th>Porte do município</th><th class="num">Municípios</th><th class="num">Atendimentos</th><th class="num">População</th><th class="num">por 100 mil</th></tr>
  {linhas_porte}
</table>
<p>A taxa cai de forma contínua conforme o porte aumenta. A taxa do estado ({br(D["taxa_estado"])}) é menor que a mediana dos municípios ({br(D["mediana_taxa"])}) justamente porque Fortaleza, com muita população e poucos atendimentos, puxa a média para baixo.</p>

<h3>4.3 Ranking de maior e menor volume proporcional</h3>
<p><b>Por quê:</b> o ranking mostra os extremos que merecem atenção, seja para entender boas coberturas, seja para investigar possíveis lacunas.</p>
<div class="grid2 avoid">
<div><h4>Maiores taxas</h4><table class="t"><tr><th class="num">#</th><th>Município</th><th>Região</th><th class="num">Atend.</th><th class="num">por 100 mil</th></tr>{ranking_tab(mai)}</table></div>
<div><h4>Menores taxas</h4><table class="t"><tr><th class="num">#</th><th>Município</th><th>Região</th><th class="num">Atend.</th><th class="num">por 100 mil</th></tr>{ranking_tab(men)}</table></div>
</div>
<p>No topo estão municípios pequenos do interior, como Penaforte e Salitre, no Sul, e Tejuçuoca e Itatira, no Norte. Na base, {rmf_base} dos 10 municípios são da Região Metropolitana (RMF). Ereré aparece por ter apenas 39 atendimentos, o menor volume de toda a base.</p>

<h3>4.4 Mapa dos atendimentos</h3>
<p><b>Por quê:</b> o mapa mostra padrões regionais que uma tabela esconde. Usamos a malha municipal oficial do IBGE, colorida pela taxa por 100 mil habitantes, para que municípios grandes em área não pareçam mais importantes só pelo tamanho.</p>
{fig("08_mapa_taxa", "<b>Figura 3.</b> Atendimentos por 100 mil habitantes por município (Censo 2022). No painel, o mapa é interativo, tem zoom e também uma versão em bolhas, com o tamanho proporcional ao volume.", "62%")}

<h3>4.5 Relação com o desenvolvimento humano (IDHM)</h3>
<p><b>Por quê:</b> se a base é coerente, esperamos que municípios mais pobres, onde mais gente depende do SUS, tenham mais atendimentos por habitante. Essa análise só é possível com o enriquecimento.</p>
{fig("11_idhm_taxa", f"<b>Figura 4.</b> IDHM 2010 e atendimentos por 100 mil habitantes; o tamanho do ponto é a população. Correlação de Spearman de {br(D['spearman_taxa_idhm'], 2)}.", "70%")}
<p>A relação é negativa e moderada: municípios de IDHM baixo têm {br(idhm["Baixo"]["taxa"])} atendimentos por 100 mil, os de IDHM médio têm {br(idhm["Médio"]["taxa"])}, e os {int(idhm["Alto"]["n"])} de IDHM alto, entre eles Fortaleza, têm {br(idhm["Alto"]["taxa"])}. Correlação não prova causa, mas o sentido confirma o esperado e reforça a coerência da base.</p>

<h3>4.6 Achado complementar: perfil dos nomes</h3>
<p>Os quatro primeiros nomes mais frequentes (Maria, Francisca, Antônia e Ana) somam {br(D["pct_top4_nomes"], 1)}% dos registros. Por uma heurística simples de terminação do nome, <b>{br(Q["pct_feminino_heuristica"], 1)}% dos registros parecem ser de mulheres</b>. Como a base não tem o campo sexo, isso é só um indício de que os dados podem vir de um serviço voltado à saúde da mulher, o que ajudaria a explicar a distribuição e deve ser confirmado com a fonte.</p>
</section>

<!-- 5 -->
<section>
<h2><span class="n">5</span>Painel interativo</h2>
<p>O painel foi feito em <b>Python com Streamlit e Plotly</b>. Tem filtros por mesorregião, porte e faixa de IDHM, permite trocar a população do Censo 2022 pela estimativa de {Q["ano_estimativa_populacao"]} e se organiza em sete abas: Volume, Taxa por 100 mil, Ranking, Mapa, Coerência dos dados, Perfil e IDHM, e Dados, com exportação em CSV.</p>
{fig("dash_volume", "<b>Figura 5.</b> Aba Volume do painel, com os indicadores principais no topo.", "88%")}
<pre><span class="c"># na pasta do projeto</span>
pip install -r requirements.txt
python src/coleta_ibge.py   <span class="c"># baixa as bases públicas (opcional: já estão em dados/)</span>
python src/etl.py           <span class="c"># trata, cruza e valida</span>
streamlit run app.py        <span class="c"># abre o painel no navegador</span></pre>
</section>

<!-- 6 -->
<section>
<h2><span class="n">6</span>Conclusões e limitações</h2>
<div class="grid2">
  <div class="card"><h4>O interior atende mais</h4><p>Cidades de até 20 mil habitantes têm cerca de {br(porte[0]["taxa"] / CAP["taxa_100k"], 0)} vezes mais atendimentos por habitante do que Fortaleza.</p></div>
  <div class="card"><h4>A base é coerente</h4><p>Nenhum município passa da própria população, todos os registros casaram com o IBGE e o volume acompanha a população.</p></div>
  <div class="card"><h4>IDHM menor, mais atendimentos</h4><p>O sentido da relação é o esperado para um serviço público de saúde.</p></div>
  <div class="card"><h4>A capital merece investigação</h4><p>A distância entre população e atendimentos em Fortaleza é o principal ponto a esclarecer com a fonte dos dados.</p></div>
</div>
<h3>Limitações</h3>
<ul>
  <li>A base não informa data, tipo de atendimento nem unidade de saúde, então não é possível separar programas ou períodos.</li>
  <li>Um mesmo paciente pode ter mais de um atendimento; a taxa mede atendimentos, não pessoas atendidas.</li>
  <li>O IDHM mais recente por município é de 2010; usamos por ser a única série oficial completa.</li>
  <li>O sexo foi estimado pelo nome e serve apenas como indício.</li>
</ul>
</section>

<!-- REFERÊNCIAS -->
<section class="refs">
<h2 style="margin-top:6mm">Referências</h2>
<p>IBGE. <b>API de localidades</b>. Rio de Janeiro: IBGE, 2026. Disponível em: https://servicodados.ibge.gov.br/api/docs/localidades. Acesso em: 30 out. 2026.</p>
<p>IBGE. <b>API de malhas geográficas</b>: versão 3. Rio de Janeiro: IBGE, 2026. Disponível em: https://servicodados.ibge.gov.br/api/docs/malhas?versao=3. Acesso em: 30 out. 2026.</p>
<p>IBGE. <b>Censo Demográfico 2022</b>: tabela 4714, população residente, área territorial e densidade demográfica. Rio de Janeiro: IBGE, 2023. Disponível em: https://sidra.ibge.gov.br/tabela/4714. Acesso em: 30 out. 2026.</p>
<p>IBGE. <b>Estimativas da população</b>: tabela 6579, população residente estimada. Rio de Janeiro: IBGE, 2026. Disponível em: https://sidra.ibge.gov.br/tabela/6579. Acesso em: 30 out. 2026.</p>
<p>IPEA. <b>Ipeadata</b>: série ADH_IDHM, Índice de Desenvolvimento Humano Municipal. Brasília: IPEA, 2026. Disponível em: http://www.ipeadata.gov.br. Acesso em: 30 out. 2026.</p>
<p>MCKINNEY, W. Data structures for statistical computing in Python. In: PYTHON IN SCIENCE CONFERENCE, 9., 2010, Austin. <b>Proceedings</b> [...]. Austin: SciPy, 2010. p. 56-61.</p>
<p>PNUD; IPEA; FJP. <b>Atlas do desenvolvimento humano no Brasil</b>. Brasília: PNUD, 2013. Disponível em: http://www.atlasbrasil.org.br. Acesso em: 30 out. 2026.</p>
<p>PLOTLY TECHNOLOGIES. <b>Plotly Python graphing library</b>. Montreal: Plotly, 2026. Disponível em: https://plotly.com/python/. Acesso em: 30 out. 2026.</p>
<p>SNOWFLAKE. <b>Streamlit documentation</b>. 2026. Disponível em: https://docs.streamlit.io. Acesso em: 30 out. 2026.</p>
</section>

</body>
</html>
"""


async def gerar_pdf(html: Path, pdf: Path) -> None:
    from playwright.async_api import async_playwright

    rodape = ('<div style="font-family:Inter,Arial,sans-serif;font-size:7.5pt;color:#6B7F87;width:100%;'
              'padding:0 18mm;display:flex;justify-content:space-between">'
              '<span>Atendimentos SUS no Ceará · Análise Enriquecida</span>'
              '<span>Página <span class="pageNumber"></span> de <span class="totalPages"></span></span></div>')
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROME_PATH"]} if os.environ.get("CHROME_PATH") else {}
        b = await p.chromium.launch(**kw)
        pg = await b.new_page()
        await pg.goto(html.as_uri(), wait_until="networkidle")
        await pg.pdf(path=str(pdf), format="A4", print_background=True, display_header_footer=True,
                     header_template="<span></span>", footer_template=rodape,
                     margin={"top": "20mm", "bottom": "18mm", "left": "18mm", "right": "18mm"})
        await b.close()


def main() -> None:
    html = REL / "relatorio.html"
    html.write_text(HTML)
    asyncio.run(gerar_pdf(html, SAIDA_PDF))
    print("ok", SAIDA_PDF)


if __name__ == "__main__":
    main()
