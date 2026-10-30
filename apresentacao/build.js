// Gera Apresentacao_Atendimentos_SUS_Ceara.pptx no mesmo visual da apresentação OndaRent.
// Uso: node build.js   (antes: python src/etl.py, src/figuras.py e src/dados_apresentacao.py)
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.PPTX_SKILL
  ? path.join(process.env.PPTX_SKILL, "scripts/apply_theme.js")
  : "./apply_theme.js");

const D = JSON.parse(fs.readFileSync(path.join(__dirname, "dados.json"), "utf8"));
const FIG = path.join(__dirname, "..", "figuras");
const OUT = path.join(__dirname, "Apresentacao_Atendimentos_SUS_Ceara.pptx");

const THEME = {
  name: "OndaRent",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "0B2530", lt1: "FFFFFF", dk2: "3A525C", lt2: "F3F7F8",
    accent1: "0E7C86", accent2: "B5761F", accent3: "7FD4DC", accent4: "6B7F87",
    accent5: "067647", accent6: "B42318", hlink: "0E7C86", folHlink: "3A525C",
  },
};
// Hex para opções que não aceitam cor de esquema (grades, gráficos)
const HX = {
  ink: "0B2530", ink2: "3A525C", muted: "6B7F87", line: "D9E2E5", soft: "F3F7F8",
  teal: "0E7C86", teal2: "7FD4DC", tealSoft: "E3F2F3", sand: "C98A2B", sandBar: "B5761F", sandSoft: "FBF1E1",
  green: "067647", greenSoft: "E7F6EE", amber: "B54708", amberSoft: "FEF0E6",
  card: "1D3640", lightInk: "BFD6DB", footDark: "7FA6B0",
};

const EQUIPE = [
  ["Davi Salgueiro", "2315072"], ["Diego Benevides", "2310381"], ["Eduardo Jorge", "2310384"],
  ["Ian Sampaio", "2310398"], ["Larissa Elias", "2315032"],
];

const br = (v, c = 0) =>
  Number(v).toLocaleString("pt-BR", { minimumFractionDigits: c, maximumFractionDigits: c });

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
// Encaixa a imagem dentro da caixa mantendo a proporção; alinha ao topo e centraliza na horizontal
function fit(file, x, y, w, h) {
  const s = pngSize(file);
  const r = Math.min(w / s.w, h / s.h);
  return { path: file, x: x + (w - s.w * r) / 2, y, w: s.w * r, h: s.h * r };
}

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13,333 x 7,5 pol
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Atendimentos SUS no Ceará: análise enriquecida";
pres.author = EQUIPE.map((e) => e[0]).join(", ");
const C = pres.SchemeColor;

const MX = 0.76; // margem lateral
const CW = 13.333 - 2 * MX;
const RODAPE = "Atendimentos SUS no Ceará · Análise Enriquecida";

// ------------------------------------------------------------------ layouts
const eyebrowPh = (cor) => ({
  placeholder: {
    options: { name: "eyebrow", type: "body", x: MX, y: 0.5, w: CW, h: 0.32, fontSize: 11, bold: true,
      charSpacing: 2.5, color: cor, margin: 0, valign: "middle" },
    text: "",
  },
});
const titlePh = (cor) => ({
  placeholder: {
    options: { name: "title", type: "title", x: MX, y: 0.84, w: CW, h: 0.62, fontSize: 30, bold: true,
      color: cor, margin: 0, valign: "middle", align: "left" },
    text: "",
  },
});

pres.defineSlideMaster({
  title: "Conteudo",
  background: { color: "FFFFFF" },
  objects: [
    eyebrowPh(C.accent1), titlePh(C.text1),
    { text: { text: RODAPE, options: { x: MX, y: 7.0, w: 8, h: 0.25, fontSize: 9, color: C.accent4, margin: 0 } } },
  ],
  slideNumber: { x: 13.333 - MX - 0.6, y: 7.0, w: 0.6, h: 0.25, fontSize: 9, color: HX.muted, align: "right", margin: 0 },
});
pres.defineSlideMaster({
  title: "Escuro",
  background: { color: HX.ink },
  objects: [
    eyebrowPh(C.accent3), titlePh(C.background1),
    { text: { text: RODAPE, options: { x: MX, y: 7.0, w: 8, h: 0.25, fontSize: 9, color: HX.footDark, margin: 0 } } },
  ],
  slideNumber: { x: 13.333 - MX - 0.6, y: 7.0, w: 0.6, h: 0.25, fontSize: 9, color: HX.footDark, align: "right", margin: 0 },
});
pres.defineSlideMaster({ title: "Capa", background: { color: HX.ink }, objects: [] });

function novo(secao, eyebrow, titulo, master = "Conteudo") {
  const s = pres.addSlide({ masterName: master, sectionTitle: secao });
  s.addText(eyebrow.toUpperCase(), { placeholder: "eyebrow" });
  s.addText(titulo, { placeholder: "title" });
  return s;
}
let secaoAtual = null;
function secao(t) { pres.addSection({ title: t }); secaoAtual = t; }

// ------------------------------------------------------------------ componentes
function box(s, x, y, w, h, fill, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill },
    rectRadius: 0.12, objectName: name });
}
function card(s, x, y, w, h, name) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: "FFFFFF" },
    line: { color: HX.line, width: 1.25 }, rectRadius: 0.12, objectName: name });
}
function pill(s, x, y, texto, fg, bg, w = null, fs = 11) {
  const ww = w || Math.max(0.7, texto.length * 0.095 + 0.35);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: ww, h: 0.3, fill: { color: bg }, line: { color: bg }, rectRadius: 0.15 });
  s.addText(texto, { x, y, w: ww, h: 0.3, fontSize: fs, bold: true, color: fg, align: "center", valign: "middle",
    margin: 0, isTextBox: true });
  return ww;
}
function txt(s, texto, o) { s.addText(texto, { margin: 0, isTextBox: true, color: HX.ink2, fontSize: 14, ...o }); }
function hline(s, x, y, w, cor = HX.line) { s.addShape(pres.shapes.LINE, { x, y, w, h: 0, line: { color: cor, width: 1.25 } }); }

// Estat. grande + legenda (estilo "99,5%" do slide de SLAs)
function stat(s, x, y, w, valor, legenda, { cor = HX.ink, leg = HX.ink2, tam = 40 } = {}) {
  txt(s, valor, { x, y, w, h: 0.7, fontSize: tam, bold: true, color: cor, valign: "bottom" });
  txt(s, legenda, { x, y: y + 0.78, w, h: 0.6, fontSize: 13, color: leg, valign: "top" });
}

const eixo = {
  catAxisLabelColor: HX.ink2, valAxisLabelColor: HX.muted, catAxisLabelFontSize: 12, valAxisLabelFontSize: 10,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  catAxisLineShow: false, valGridLine: { style: "none" }, catGridLine: { style: "none" },
  dataLabelColor: HX.ink, dataLabelFontSize: 11, showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "#,##0", showLegend: false, valAxisHidden: true,
};
function barrasH(s, labels, valores, x, y, w, h, cores, extra = {}) {
  s.addChart(pres.charts.BAR, [{ name: "valor", labels, values: valores }], {
    x, y, w, h, barDir: "bar", catAxisOrientation: "maxMin", barGapWidthPct: 45,
    chartColors: cores, ...eixo, ...extra,
  });
}
function colunas(s, labels, valores, x, y, w, h, cores, extra = {}) {
  s.addChart(pres.charts.BAR, [{ name: "valor", labels, values: valores }], {
    x, y, w, h, barDir: "col", barGapWidthPct: 40, chartColors: cores, ...eixo, ...extra,
  });
}

const q = D.qualidade;
const cap = D.capital;
const reg = [...D.regioes].sort((a, b) => b.atendimentos - a.atendimentos);
const noroesteNorte = reg.filter((r) => /Noroeste|Norte Cearense/.test(r.mesorregiao) && !/Sul/.test(r.mesorregiao))
  .reduce((a, r) => a + r.participacao_atend_pct, 0);
const porteAte20 = D.porte[0].taxa;

// ================================================================== 1. capa
secao("Abertura");
{
  const s = pres.addSlide({ masterName: "Capa", sectionTitle: "Abertura" });
  s.addImage({ path: path.join(__dirname, "ondas.png"), x: 0, y: 0, w: 13.333, h: 7.5, objectName: "ondas" });
  txt(s, "BUSINESS INTELLIGENCE · SAÚDE PÚBLICA NO CEARÁ", { x: 0.9, y: 1.25, w: 10, h: 0.35, fontSize: 12,
    bold: true, charSpacing: 2.5, color: HX.teal2 });
  s.addText("Atendimentos SUS:\no interior atende mais\ndo que a capital", { x: 0.9, y: 1.7, w: 11, h: 2.35,
    fontSize: 44, bold: true, color: "FFFFFF", margin: 0, valign: "top", lineSpacingMultiple: 0.95, isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.9, y: 4.32, w: 0.83, h: 0.05, fill: { color: HX.sand },
    line: { color: HX.sand }, rectRadius: 0.02, objectName: "traco" });
  txt(s, "Análise Enriquecida de Atendimentos SUS com Informações Municipais", { x: 0.9, y: 4.6, w: 11, h: 0.4,
    fontSize: 16, color: HX.lightInk });
  EQUIPE.forEach(([n, m], i) => {
    const x = 0.9 + i * 2.05;
    txt(s, n, { x, y: 6.45, w: 2.0, h: 0.25, fontSize: 11, bold: true, color: "FFFFFF" });
    txt(s, m, { x, y: 6.72, w: 2.0, h: 0.22, fontSize: 9, color: HX.lightInk, fontFace: "Courier New" });
  });
  s.addNotes("Apresentação da equipe e do tema. Mensagem principal: proporcionalmente à população, o interior do " +
    "Ceará registra muito mais atendimentos do que Fortaleza e a Região Metropolitana.");
}

// ================================================================== 2. ponto de partida
secao("Dados e método");
{
  const s = novo("Dados e método", "01 · Ponto de partida", "Uma lista de atendimentos com só três colunas");
  txt(s, "O que recebemos:", { x: MX, y: 1.95, w: 5.4, h: 0.35, fontSize: 15 });
  box(s, MX, 2.4, 5.4, 3.0, HX.ink, "tabela_bruta");
  const linhas = [["ID", "MUNICÍPIO", "PRIMEIRO_NOME"], ["1", "ABAIARA      ···", "ADRIANA"],
    ["58.112", "FORTALEZA    ···", "MARIA"], ["196.086", "UBAJARA      ···", "NA"], ["204.579", "VÁRZEA ALEGRE ···", "…"]];
  linhas.forEach((l, i) => {
    const y = 2.62 + i * 0.5;
    const cor = i === 0 ? HX.teal2 : "E6F0F2";
    txt(s, l[0], { x: MX + 0.3, y, w: 1.0, h: 0.4, fontSize: 12, color: cor, fontFace: "Courier New", bold: i === 0 });
    txt(s, l[1], { x: MX + 1.35, y, w: 2.3, h: 0.4, fontSize: 12, color: cor, fontFace: "Courier New", bold: i === 0 });
    txt(s, l[2], { x: MX + 3.7, y, w: 1.6, h: 0.4, fontSize: 12, color: cor, fontFace: "Courier New", bold: i === 0 });
  });
  s.addText([
    { text: br(D.total), options: { bold: true, color: HX.ink } },
    { text: " atendimentos em " },
    { text: `${D.municipios} municípios`, options: { bold: true, color: HX.ink } },
    { text: ": todo o Ceará." },
  ], { x: MX, y: 5.65, w: 5.4, h: 0.4, fontSize: 15, color: HX.ink2, margin: 0, isTextBox: true });

  const x0 = MX + 6.0, w0 = CW - 6.0;
  txt(s, "O que acrescentamos, por município:", { x: x0, y: 1.95, w: w0, h: 0.35, fontSize: 15 });
  const itens = [
    ["População", "Censo 2022 e estimativa 2026"], ["Área e densidade", "km² e hab./km² (Censo 2022)"],
    ["Região", "mesorregião e região intermediária"], ["IDHM 2010", "Atlas do Desenv. Humano (PNUD)"],
    ["Mapa", "malha municipal e coordenadas"], ["Código IBGE", "chave única de 7 dígitos"],
  ];
  const cw = (w0 - 0.25) / 2;
  itens.forEach(([t, d], i) => {
    const x = x0 + (i % 2) * (cw + 0.25), y = 2.4 + Math.floor(i / 2) * 1.08;
    box(s, x, y, cw, 0.92, HX.soft, "enriq_" + i);
    txt(s, t, { x: x + 0.22, y: y + 0.14, w: cw - 0.4, h: 0.35, fontSize: 16, bold: true, color: HX.ink });
    txt(s, d, { x: x + 0.22, y: y + 0.5, w: cw - 0.4, h: 0.3, fontSize: 12 });
  });
  s.addNotes("A base original não permite comparar municípios: 9 mil atendimentos em Fortaleza e 7 mil em " +
    "Itapipoca parecem parecidos, mas as populações são muito diferentes. Por isso buscamos dados do IBGE.");
}

// ================================================================== 3. pipeline
{
  const s = novo("Dados e método", "02 · Como fizemos", "Do arquivo bruto ao painel em quatro etapas");
  const etapas = [
    ["1", "Tratar", "padronizar nomes, corrigir erros e grafias antigas", "pandas"],
    ["2", "Enriquecer", "juntar cada atendimento ao seu município no IBGE", "join por código IBGE"],
    ["3", "Validar", `${q.verificacoes.length} testes de coerência entre as bases`, "regras + estatística"],
    ["4", "Visualizar", "gráficos, ranking e mapa interativo", "Plotly + Streamlit"],
  ];
  const w = 2.62, gap = 0.44, y = 2.25, h = 2.6;
  etapas.forEach(([n, t, d, tool], i) => {
    const x = MX + i * (w + gap);
    const escuro = i === 1;
    box(s, x, y, w, h, escuro ? HX.ink : HX.soft, "etapa_" + n);
    txt(s, n, { x: x + 0.28, y: y + 0.25, w: 1, h: 0.45, fontSize: 24, bold: true, color: escuro ? HX.teal2 : HX.teal });
    txt(s, t, { x: x + 0.28, y: y + 0.78, w: w - 0.5, h: 0.45, fontSize: 21, bold: true, color: escuro ? "FFFFFF" : HX.ink });
    txt(s, d, { x: x + 0.28, y: y + 1.28, w: w - 0.5, h: 0.75, fontSize: 13, color: escuro ? HX.lightInk : HX.ink2, valign: "top" });
    const pw = Math.min(w - 0.5, tool.length * 0.085 + 0.4);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: x + 0.28, y: y + 2.05, w: pw, h: 0.32,
      fill: { color: escuro ? HX.card : HX.tealSoft }, line: { color: escuro ? HX.card : HX.tealSoft }, rectRadius: 0.16 });
    txt(s, tool, { x: x + 0.28, y: y + 2.05, w: pw, h: 0.32, fontSize: 11, bold: true, align: "center", valign: "middle",
      color: escuro ? HX.teal2 : HX.teal });
    if (i < 3) s.addShape(pres.shapes.LINE, { x: x + w + 0.07, y: y + h / 2, w: gap - 0.14, h: 0,
      line: { color: HX.muted, width: 1.5, endArrowType: "triangle" } });
  });
  txt(s, "Fontes oficiais, baixadas por script (src/coleta_ibge.py):", { x: MX, y: 5.35, w: CW, h: 0.3, fontSize: 13, bold: true, color: HX.ink });
  txt(s, "IBGE SIDRA tabelas 4714 (Censo 2022) e 6579 (estimativas) · IBGE API de Localidades e de Malhas · " +
    "Ipeadata série ADH_IDHM (PNUD, IPEA e FJP)", { x: MX, y: 5.7, w: CW, h: 0.5, fontSize: 13 });
  s.addNotes("Todo o trabalho é reproduzível: coleta_ibge.py baixa as bases, etl.py trata, cruza e valida, " +
    "app.py é o painel. Destaque para a etapa 2: a junção é feita pelo código IBGE, não pelo nome.");
}

// ================================================================== 4. tratamento
{
  const s = novo("Dados e método", "02 · Tratamento", "O que precisou ser corrigido antes do cruzamento");
  const probs = [
    ["Nome do município com 100 caracteres", "campo de largura fixa: espaços sobrando em todos os registros", q.municipio_com_espacos_extras],
    ["Itapagé com a grafia antiga", "no cadastro atual do IBGE o município se chama Itapajé", q.municipio_grafia_antiga.ITAPAGE],
    ["Caractere corrompido no nome", "erro de codificação, como em “�MARIA”", q.nome_caractere_invalido],
    ["Nome “NA” virando vazio", "o pandas lê o texto NA como dado ausente sem avisar", q.nome_ausente],
    ["Número no lugar de letra", "“J0SE” escrito com zero", q.nome_com_digito],
  ];
  const y0 = 1.8, rh = 0.84;
  probs.forEach(([t, d, n], i) => {
    const y = y0 + i * rh;
    txt(s, t, { x: MX, y: y + 0.1, w: 9, h: 0.36, fontSize: 17, bold: true, color: HX.ink });
    txt(s, d, { x: MX, y: y + 0.46, w: 9, h: 0.3, fontSize: 13 });
    const lab = br(n) + (n === 1 ? " registro" : " registros");
    const pw = lab.length * 0.1 + 0.4;
    pill(s, 13.333 - MX - pw, y + 0.27, lab, HX.teal, HX.tealSoft, pw, 12);
    if (i < probs.length - 1) hline(s, MX, y + rh, CW);
  });
  box(s, MX, 6.15, CW, 0.62, HX.tealSoft, "resultado_juncao");
  s.addText([
    { text: "Resultado: ", options: { bold: true, color: HX.ink } },
    { text: `${br(D.total)} de ${br(D.total)} registros ligados a um código IBGE (100%), sem nenhum descarte.` },
  ], { x: MX + 0.25, y: 6.15, w: CW - 0.5, h: 0.62, fontSize: 14, color: HX.ink2, valign: "middle", margin: 0, isTextBox: true });
  s.addNotes("Nenhum registro foi descartado. Os problemas de nome não afetam a contagem por município, " +
    "mas foram corrigidos e marcados na coluna qualidade_nome da base enriquecida.");
}

// ================================================================== 5. volume por região
secao("Análises");
{
  const s = novo("Análises", "03 · Análise 1 · Volume por região", "Noroeste e Norte somam quase metade do volume");
  txt(s, "Atendimentos por mesorregião", { x: MX, y: 1.8, w: 7.3, h: 0.3, fontSize: 13, bold: true, color: HX.ink });
  barrasH(s, reg.map((r) => r.mesorregiao), reg.map((r) => r.atendimentos), MX - 0.1, 2.15, 7.5, 4.6,
    reg.map((r) => /Metropolitana/.test(r.mesorregiao) ? HX.sandBar : HX.teal));
  const x = MX + 7.9, w = CW - 7.9;
  box(s, x, 1.9, w, 2.15, HX.ink, "stat_nn");
  stat(s, x + 0.35, 2.05, w - 0.7, br(noroesteNorte, 1) + "%", "dos atendimentos vêm do Noroeste e do Norte Cearense",
    { cor: "FFFFFF", leg: HX.lightInk });
  box(s, x, 4.25, w, 2.5, HX.sandSoft, "stat_rmf");
  txt(s, "REGIÃO METROPOLITANA", { x: x + 0.35, y: 4.45, w: w - 0.7, h: 0.3, fontSize: 11, bold: true, charSpacing: 1.5, color: "8A5A12" });
  s.addText([
    { text: br(D.rmf.participacao_pop_pct, 1) + "%", options: { bold: true, color: HX.ink, fontSize: 28 } },
    { text: " da população", options: { breakLine: true } },
    { text: br(D.rmf.participacao_atend_pct, 1) + "%", options: { bold: true, color: HX.ink, fontSize: 28 } },
    { text: " dos atendimentos" },
  ], { x: x + 0.35, y: 4.85, w: w - 0.7, h: 1.6, fontSize: 14, color: HX.ink2, margin: 0, valign: "top",
    paraSpaceAfter: 6, isTextBox: true });
  s.addNotes("Em números absolutos, as regiões do interior norte lideram. A Região Metropolitana, que tem 41% " +
    "da população, fica só em 4º lugar em volume.");
}

// ================================================================== 6. volume por município
{
  const s = novo("Análises", "03 · Análise 1 · Volume por município", "Em números absolutos, Fortaleza lidera o estado");
  const t = D.top_volume;
  txt(s, "Os 10 municípios com mais atendimentos", { x: MX, y: 1.8, w: 7.3, h: 0.3, fontSize: 13, bold: true, color: HX.ink });
  barrasH(s, t.map((r) => r.municipio), t.map((r) => r.atendimentos), MX - 0.1, 2.15, 7.5, 4.6,
    t.map((r) => (r.municipio === "Fortaleza" ? HX.sandBar : HX.teal)));
  const x = MX + 7.9, w = CW - 7.9;
  txt(s, "Mas o tamanho da cidade engana:", { x, y: 2.0, w, h: 0.4, fontSize: 16, color: HX.ink });
  card(s, x, 2.55, w, 1.85, "cmp_fortaleza");
  txt(s, "FORTALEZA", { x: x + 0.3, y: 2.72, w: w - 0.6, h: 0.3, fontSize: 11, bold: true, charSpacing: 1.5, color: HX.sandBar });
  stat(s, x + 0.3, 2.95, w - 0.6, br(cap.taxa_100k), `por 100 mil hab. · ${br(cap.atendimentos)} para ${br(cap.populacao_2022 / 1e6, 1)} milhões`,
    { tam: 32 });
  const ita = t.find((r) => r.municipio === "Itapipoca");
  card(s, x, 4.6, w, 1.85, "cmp_itapipoca");
  txt(s, "ITAPIPOCA (2º EM VOLUME)", { x: x + 0.3, y: 4.77, w: w - 0.6, h: 0.3, fontSize: 11, bold: true, charSpacing: 1.5, color: HX.teal });
  stat(s, x + 0.3, 5.0, w - 0.6, br(ita.taxa_100k), `por 100 mil hab. · ${br(ita.atendimentos)} atendimentos`, { tam: 32 });
  s.addNotes("Fortaleza tem o maior volume, mas para 2,4 milhões de habitantes. Itapipoca, com cerca de " +
    "130 mil, chega perto em volume: por isso precisamos da taxa por 100 mil.");
}

// ================================================================== 7. taxa por porte
{
  const s = novo("Análises", "03 · Análise 2 · Atendimentos por 100 mil habitantes", "Quanto menor a cidade, mais atendimentos por habitante");
  txt(s, "Atendimentos por 100 mil hab., por porte do município", { x: MX, y: 1.8, w: 7.5, h: 0.3, fontSize: 13, bold: true, color: HX.ink });
  colunas(s, D.porte.map((p) => p.porte), D.porte.map((p) => p.taxa), MX - 0.1, 2.2, 7.6, 4.35,
    D.porte.map((p) => (p.porte === "Acima de 500 mil" ? HX.sandBar : HX.teal)), { catAxisLabelFontSize: 11 });
  txt(s, D.porte.map((p) => `${p.n} ${p.n === 1 ? "município" : "municípios"}`).join("   ·   "),
    { x: MX, y: 6.55, w: 7.4, h: 0.3, fontSize: 10, color: HX.muted, align: "center" });
  const x = MX + 7.9, w = CW - 7.9;
  box(s, x, 1.9, w, 2.15, HX.ink, "stat_estado");
  stat(s, x + 0.35, 2.05, w - 0.7, br(D.taxa_estado), "atendimentos por 100 mil habitantes no Ceará (Censo 2022)",
    { cor: "FFFFFF", leg: HX.lightInk });
  box(s, x, 4.25, w, 2.5, HX.soft, "stat_10x");
  stat(s, x + 0.35, 4.45, w - 0.7, br(porteAte20 / cap.taxa_100k, 1).replace(",0", "") + " vezes",
    `mais atendimentos por habitante nas cidades de até 20 mil (${br(porteAte20)}) do que em Fortaleza (${br(cap.taxa_100k)})`);
  s.addNotes("A taxa por 100 mil = atendimentos ÷ população × 100.000. Ela permite comparar municípios de " +
    "tamanhos diferentes. A queda é contínua conforme o porte cresce.");
}

// ================================================================== 8. ranking
{
  const s = novo("Análises", "03 · Análise 3 · Ranking proporcional", "Cidades pequenas no topo, Grande Fortaleza na base");
  const half = (CW - 0.5) / 2;
  const mai = D.maiores_taxa, men = D.menores_taxa;
  txt(s, "MAIOR VOLUME PROPORCIONAL", { x: MX, y: 1.8, w: half, h: 0.3, fontSize: 11, bold: true, charSpacing: 1.5, color: HX.teal });
  barrasH(s, mai.map((r) => r.municipio), mai.map((r) => r.taxa_100k), MX - 0.1, 2.1, half + 0.1, 4.4, [HX.teal],
    { catAxisLabelFontSize: 11, valAxisMaxVal: 9800 });
  const x2 = MX + half + 0.5;
  txt(s, "MENOR VOLUME PROPORCIONAL", { x: x2, y: 1.8, w: half, h: 0.3, fontSize: 11, bold: true, charSpacing: 1.5, color: HX.sandBar });
  barrasH(s, men.map((r) => r.municipio), men.map((r) => r.taxa_100k), x2 - 0.1, 2.1, half + 0.1, 4.4, [HX.sandBar],
    { catAxisLabelFontSize: 11, valAxisMaxVal: 1550 });
  const rmfBase = men.filter((r) => /Metropolitana/.test(r.mesorregiao)).length;
  txt(s, `Atendimentos por 100 mil hab. Na base, ${rmfBase} dos 10 municípios são da Região Metropolitana. Atenção: as escalas dos dois gráficos são diferentes.`,
    { x: MX, y: 6.62, w: CW, h: 0.3, fontSize: 10, color: HX.muted });
  s.addNotes("Penaforte lidera com 8,4% da população atendida. Na base, Fortaleza e quatro vizinhas da RMF. " +
    "Ereré aparece por ter apenas 39 atendimentos, o menor volume da base.");
}

// ================================================================== 9. mapa
{
  const s = novo("Análises", "03 · Análise 4 · Mapa", "No mapa, a Grande Fortaleza é a área mais clara");
  s.addImage({ ...fit(path.join(FIG, "08_mapa_taxa.png"), MX, 1.75, 6.2, 5.1), objectName: "mapa" });
  const x = MX + 6.6, w = CW - 6.6;
  const pts = [
    ["Cor = atendimentos por 100 mil hab.", "quanto mais escuro, mais atendimentos para o tamanho da população"],
    ["Litoral metropolitano mais claro", `Fortaleza, Caucaia, Eusébio e vizinhas têm as menores taxas do estado`],
    ["Manchas escuras no interior", "Penaforte e Salitre (Cariri), Itatira e Tejuçuoca (sertão norte)"],
    ["No painel, o mapa é interativo", "zoom, filtros por região e os números de cada município ao passar o mouse"],
  ];
  pts.forEach(([t, d], i) => {
    const y = 1.9 + i * 1.22;
    box(s, x, y, w, 1.06, i === 3 ? HX.tealSoft : HX.soft, "mapa_ponto_" + i);
    txt(s, t, { x: x + 0.25, y: y + 0.14, w: w - 0.5, h: 0.35, fontSize: 15, bold: true, color: HX.ink });
    txt(s, d, { x: x + 0.25, y: y + 0.5, w: w - 0.5, h: 0.45, fontSize: 12, valign: "top" });
  });
  s.addNotes("Mapa coroplético com a malha municipal oficial do IBGE. No dashboard há também o mapa de " +
    "bolhas, em que o tamanho é o volume e a cor é a taxa.");
}

// ================================================================== 10. IDHM
{
  const s = novo("Análises", "03 · Análise 5 · Desenvolvimento humano", "Onde o IDHM é menor, há mais atendimentos por habitante");
  txt(s, "IDHM 2010 × atendimentos por 100 mil hab. (tamanho = população)", { x: MX, y: 1.8, w: 6.6, h: 0.3, fontSize: 13, bold: true, color: HX.ink });
  s.addImage({ ...fit(path.join(FIG, "11_idhm_taxa.png"), MX, 2.2, 6.6, 4.6), objectName: "disp_idhm" });
  const x = MX + 7.0, w = CW - 7.0;
  txt(s, "Atendimentos por 100 mil hab., por faixa de IDHM", { x, y: 1.8, w, h: 0.3, fontSize: 13, bold: true, color: HX.ink });
  colunas(s, D.idhm.map((f) => `${f.faixa} (${f.n})`), D.idhm.map((f) => f.taxa), x - 0.1, 2.2, w + 0.1, 3.3, [HX.teal]);
  box(s, x, 5.7, w, 1.1, HX.soft, "nota_idhm");
  s.addText([
    { text: "Correlação de Spearman: " },
    { text: br(D.spearman_taxa_idhm, 2), options: { bold: true, color: HX.ink } },
    { text: ". Padrão esperado: onde a renda é menor, mais gente depende do SUS." },
  ], { x: x + 0.25, y: 5.7, w: w - 0.5, h: 1.1, fontSize: 13, color: HX.ink2, valign: "middle", margin: 0, isTextBox: true });
  s.addNotes("Entre parênteses, o número de municípios de cada faixa. Só 4 municípios têm IDHM alto, " +
    "entre eles Fortaleza, o que puxa a taxa da faixa para baixo. Correlação moderada, não é causa.");
}

// ================================================================== 11. coerência: verificações
secao("Coesão dos dados");
{
  const s = novo("Coesão dos dados", "04 · Coesão dos dados", "Os dados fazem sentido juntos?");
  const v = q.verificacoes;
  txt(s, "VERIFICAÇÃO", { x: MX, y: 1.72, w: 3.5, h: 0.25, fontSize: 10, bold: true, charSpacing: 1.5, color: HX.muted });
  txt(s, "O QUE ENCONTRAMOS", { x: MX + 3.7, y: 1.72, w: 7, h: 0.25, fontSize: 10, bold: true, charSpacing: 1.5, color: HX.muted });
  hline(s, MX, 2.02, CW, HX.ink);
  const rh = 0.6;
  v.forEach((c, i) => {
    const y = 2.07 + i * rh;
    txt(s, c.verificacao, { x: MX, y, w: 3.5, h: rh, fontSize: 14, bold: true, color: HX.ink, valign: "middle" });
    txt(s, c.detalhe, { x: MX + 3.7, y, w: CW - 3.7 - 1.2, h: rh, fontSize: 12.5, valign: "middle" });
    const ok = c.status === "OK";
    pill(s, 13.333 - MX - 0.95, y + (rh - 0.3) / 2, ok ? "OK" : "Alerta", ok ? HX.green : HX.amber,
      ok ? HX.greenSoft : HX.amberSoft, 0.95, 11);
    if (i < v.length - 1) hline(s, MX, y + rh, CW);
  });
  s.addNotes("O teste central pedido no enunciado: algum município tem mais atendimentos que habitantes? " +
    "Não. O maior caso é Penaforte, com 8,4%. Os dois alertas não invalidam a base: um é a capital, o outro são 18 nomes.");
}

// ================================================================== 12. veredito
{
  const s = novo("Coesão dos dados", "04 · Veredito", "Coesão confirmada, com uma ressalva: a capital", "Escuro");
  const w = 3.6;
  const stats = [
    ["0", "municípios com mais atendimentos do que habitantes"],
    ["100%", "dos registros ligados a um município do IBGE"],
    [br(q.spearman_pop_atend, 2), "de correlação entre população e atendimentos"],
  ];
  stats.forEach(([vv, l], i) => {
    const y = 1.85 + i * 1.3;
    box(s, MX, y, w, 1.15, HX.card, "veredito_" + i);
    txt(s, vv, { x: MX + 0.3, y: y + 0.1, w: 1.5, h: 0.95, fontSize: 32, bold: true, color: HX.teal2, valign: "middle" });
    txt(s, l, { x: MX + 1.75, y: y + 0.1, w: w - 1.95, h: 0.95, fontSize: 12.5, color: HX.lightInk, valign: "middle" });
  });
  box(s, MX, 5.8, w, 0.95, HX.card, "veredito_ressalva");
  s.addText([
    { text: "Ressalva: ", options: { bold: true, color: "F2C879" } },
    { text: `Fortaleza tem ${br(cap.participacao_pop_pct, 1)}% da população e ${br(cap.participacao_atend_pct, 1)}% dos atendimentos.` },
  ], { x: MX + 0.3, y: 5.8, w: w - 0.5, h: 0.95, fontSize: 12.5, color: HX.lightInk, valign: "middle", margin: 0, isTextBox: true });
  const x = MX + w + 0.4, ww = CW - w - 0.4;
  box(s, x, 1.85, ww, 4.9, "FFFFFF", "card_disp");
  s.addImage({ ...fit(path.join(FIG, "09_dispersao_pop.png"), x + 0.15, 1.97, ww - 0.3, 4.66), objectName: "disp_pop" });
  s.addNotes("Cada ponto é um município. Todos estão bem abaixo da linha tracejada de 1 atendimento por habitante, " +
    "e acompanham a linha da taxa média. Fortaleza fica isolada abaixo: hipóteses são maior cobertura por planos " +
    "privados e rede própria do município, sub-registro, ou um recorte do programa que priorizou o interior.");
}

// ================================================================== 13. perfil nominal
secao("Achados e painel");
{
  const s = novo("Achados e painel", "05 · Achado extra", "A base parece vir de um serviço voltado a mulheres");
  const t = D.top_nomes;
  txt(s, "Primeiros nomes mais frequentes", { x: MX, y: 1.8, w: 7.3, h: 0.3, fontSize: 13, bold: true, color: HX.ink });
  barrasH(s, t.map((r) => r.nome), t.map((r) => r.n), MX - 0.1, 2.15, 7.5, 4.65, [HX.teal], { catAxisLabelFontSize: 11 });
  const x = MX + 7.9, w = CW - 7.9;
  box(s, x, 1.9, w, 2.15, HX.ink, "stat_fem");
  stat(s, x + 0.35, 2.05, w - 0.7, br(q.pct_feminino_heuristica, 1) + "%", "dos registros têm nome provavelmente feminino",
    { cor: "FFFFFF", leg: HX.lightInk });
  box(s, x, 4.25, w, 1.6, HX.soft, "stat_top4");
  stat(s, x + 0.35, 4.35, w - 0.7, br(D.pct_top4_nomes, 0) + "%", "são Maria, Francisca, Antônia ou Ana", { tam: 32 });
  txt(s, "Estimado pela terminação do nome; a base não traz o sexo registrado.", { x, y: 6.05, w, h: 0.6, fontSize: 11, color: HX.muted });
  s.addNotes("Não temos o campo sexo, então usamos uma heurística simples de terminação do nome. A predominância " +
    "feminina sugere um programa como saúde da mulher ou pré-natal, o que precisaria ser confirmado com a fonte.");
}

// ================================================================== 14. painel
{
  const s = novo("Achados e painel", "06 · Painel interativo", "Tudo isso está em um painel feito em Python e Streamlit");
  const img = fit(path.join(FIG, "dash_volume.png"), MX, 1.8, 8.2, 4.95);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: img.x - 0.06, y: img.y - 0.06, w: img.w + 0.12, h: img.h + 0.12,
    fill: { color: "FFFFFF" }, line: { color: HX.line, width: 1.25 }, rectRadius: 0.08, objectName: "moldura" });
  s.addImage({ ...img, objectName: "print_painel" });
  const x = MX + 8.6, w = CW - 8.6;
  txt(s, "7 abas", { x, y: 1.85, w, h: 0.4, fontSize: 18, bold: true, color: HX.ink });
  txt(s, "Volume · Taxa por 100 mil · Ranking · Mapa · Coerência · Perfil e IDHM · Dados", { x, y: 2.28, w, h: 0.75, fontSize: 12.5, valign: "top" });
  txt(s, "Filtros", { x, y: 3.2, w, h: 0.4, fontSize: 18, bold: true, color: HX.ink });
  txt(s, "mesorregião, porte, faixa de IDHM e população do Censo 2022 ou da estimativa 2026", { x, y: 3.63, w, h: 0.75, fontSize: 12.5, valign: "top" });
  box(s, x, 4.65, w, 1.25, HX.ink, "comando");
  txt(s, "pip install -r requirements.txt\nstreamlit run app.py", { x: x + 0.2, y: 4.65, w: w - 0.3, h: 1.25, fontSize: 11,
    fontFace: "Courier New", color: "E6F0F2", valign: "middle" });
  txt(s, "Também exporta a tabela de indicadores em CSV.", { x, y: 6.1, w, h: 0.5, fontSize: 11, color: HX.muted });
  s.addNotes("Demonstração ao vivo do painel, se houver tempo: filtrar só a Região Metropolitana e trocar a cor do mapa para IDHM.");
}

// ================================================================== 15. encerramento
{
  const s = novo("Achados e painel", "07 · Conclusões", "O que os dados nos dizem", "Escuro");
  const ins = [
    ["O interior atende mais", `cidades de até 20 mil hab. têm ${br(porteAte20)} atendimentos por 100 mil; Fortaleza, ${br(cap.taxa_100k)}`],
    ["A base é coerente", "nenhum município passa da própria população e todos os registros casaram com o IBGE"],
    ["IDHM menor, mais SUS", "municípios menos desenvolvidos têm taxas mais altas"],
    ["Capital merece investigação", "a diferença pode ser cobertura privada, sub-registro ou recorte do programa"],
  ];
  const w = (CW - 0.25) / 2;
  ins.forEach(([t, d], i) => {
    const x = MX + (i % 2) * (w + 0.25), y = 1.85 + Math.floor(i / 2) * 1.5;
    box(s, x, y, w, 1.3, HX.card, "conclusao_" + i);
    txt(s, t, { x: x + 0.35, y: y + 0.22, w: w - 0.7, h: 0.4, fontSize: 18, bold: true, color: "FFFFFF" });
    txt(s, d, { x: x + 0.35, y: y + 0.65, w: w - 0.7, h: 0.5, fontSize: 12.5, color: HX.lightInk, valign: "top" });
  });
  hline(s, MX, 5.95, CW, "2A4651");
  txt(s, "Obrigado. Perguntas?", { x: MX, y: 6.15, w: 6, h: 0.6, fontSize: 28, bold: true, color: "FFFFFF", valign: "middle" });
  txt(s, EQUIPE.slice(0, 3).map((e) => e[0]).join(" · ") + "\n" + EQUIPE.slice(3).map((e) => e[0]).join(" · "),
    { x: 13.333 - MX - 5, y: 6.15, w: 5, h: 0.6, fontSize: 11, color: HX.lightInk, align: "right", valign: "middle" });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("ok", OUT);
})();
