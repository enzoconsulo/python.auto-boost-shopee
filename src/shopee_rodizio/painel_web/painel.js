"use strict";

// Painel dos pesos do rodízio. Sem framework e sem polling: só fala com o Pi quando a
// página abre, quando o usuário salva ou quando pede para atualizar o catálogo.

const PESO_PADRAO_NOVO = 10;
const SIMULACOES = 4000;

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const $ = (id) => document.getElementById(id);

let dados = null;            // última resposta do servidor (/api/estado)
const edicoes = new Map();   // id -> { no: bool, peso: int } — só o que difere do salvo
const cartoes = new Map();   // id -> elemento <article>

// --- servidor ------------------------------------------------------------------------------

async function api(metodo, caminho, corpo) {
  const opcoes = { method: metodo, headers: {}, credentials: "same-origin" };
  if (metodo === "POST") {
    // header próprio + JSON: o navegador exige preflight, que o servidor nunca autoriza
    // para outra origem — é a proteção contra CSRF
    opcoes.headers["Content-Type"] = "application/json";
    opcoes.headers["X-Painel"] = "1";
    opcoes.body = JSON.stringify(corpo || {});
  }
  const resposta = await fetch(caminho, opcoes);
  const tipo = resposta.headers.get("Content-Type") || "";
  const conteudo = tipo.includes("json") ? await resposta.json() : { erro: await resposta.text() };
  if (!resposta.ok) {
    const erro = new Error(conteudo.erro || `HTTP ${resposta.status}`);
    erro.status = resposta.status;
    throw erro;
  }
  return conteudo;
}

async function carregar() {
  try {
    aplicarDados(await api("GET", "/api/estado"));
  } catch (erro) {
    avisar(`Não foi possível carregar: ${erro.message}`, true);
  }
}

async function atualizarCatalogo() {
  const botao = $("btn-atualizar");
  botao.disabled = true;
  botao.textContent = "Atualizando…";
  try {
    aplicarDados(await api("POST", "/api/catalogo/atualizar"));
  } catch (erro) {
    avisar(`Falha ao atualizar o catálogo: ${erro.message}`, true);
  } finally {
    botao.disabled = false;
    botao.textContent = "Atualizar da Shopee";
  }
}

async function salvar() {
  const botao = $("btn-salvar");
  botao.disabled = true;
  try {
    const itens = estadoAtual()
      .filter((item) => item.no)
      .map((item) => ({ id: item.id, peso: item.peso }));
    const novo = await api("POST", "/api/pesos", { versao: dados.versao, itens });
    edicoes.clear();
    aplicarDados(novo);
    avisar("Salvo. Vale a partir do próximo ciclo — não precisa reiniciar nada.", false);
  } catch (erro) {
    if (erro.status === 409) {
      avisar("O config.toml foi alterado por outro lugar desde que a página abriu. " +
        "Suas mudanças não foram gravadas: recarregue a página e refaça.", true);
    } else {
      avisar(`Não salvo: ${erro.message}`, true);
    }
  } finally {
    botao.disabled = false;
  }
}

// --- modelo --------------------------------------------------------------------------------

function itensBase() {
  const salvo = new Map(dados.rodizio.map((item) => [item.id, item.peso]));
  const vistos = new Set();
  const lista = [];
  for (const produto of dados.catalogo.itens) {
    vistos.add(produto.id);
    lista.push({ ...produto, ativo: true, pesoSalvo: salvo.get(produto.id) ?? null });
  }
  // no rodízio mas fora do catálogo ativo (pausado/excluído na Shopee, ou catálogo vazio)
  for (const item of dados.rodizio) {
    if (vistos.has(item.id)) continue;
    lista.push({
      id: item.id,
      nome: dados.nomes_config[item.id] || "",
      imagem_url: null,
      ativo: dados.catalogo.itens.length === 0,
      pesoSalvo: item.peso,
    });
  }
  return lista;
}

function estadoAtual() {
  return itensBase().map((item) => {
    const edicao = edicoes.get(item.id);
    const no = edicao ? edicao.no : item.pesoSalvo !== null;
    const peso = edicao ? edicao.peso : (item.pesoSalvo ?? PESO_PADRAO_NOVO);
    return { ...item, no, peso };
  });
}

function editar(id, mudanca) {
  const item = estadoAtual().find((i) => i.id === id);
  const novo = { no: item.no, peso: item.peso, ...mudanca };
  const salvoNo = item.pesoSalvo !== null;
  if (novo.no === salvoNo && (!novo.no || novo.peso === item.pesoSalvo)) {
    edicoes.delete(id);
  } else {
    edicoes.set(id, novo);
  }
  atualizarCartao(id);
  atualizarResumo();
}

// chance de cada item entrar num ciclo: sorteio ponderado SEM reposição até limite_slots,
// igual ao selecao.py — por simulação, porque a fórmula fechada não é trivial
function chances(itens, slots) {
  const ativos = itens.filter((item) => item.no);
  const resultado = new Map();
  if (ativos.length <= slots) {
    ativos.forEach((item) => resultado.set(item.id, 1));
    return resultado;
  }
  const contagem = new Map(ativos.map((item) => [item.id, 0]));
  for (let s = 0; s < SIMULACOES; s++) {
    const restantes = ativos.slice();
    let total = restantes.reduce((soma, item) => soma + item.peso, 0);
    for (let k = 0; k < slots; k++) {
      let alvo = Math.random() * total;
      let i = 0;
      while (alvo >= restantes[i].peso && i < restantes.length - 1) {
        alvo -= restantes[i].peso;
        i++;
      }
      const [escolhido] = restantes.splice(i, 1);
      total -= escolhido.peso;
      contagem.set(escolhido.id, contagem.get(escolhido.id) + 1);
    }
  }
  contagem.forEach((n, id) => resultado.set(id, n / SIMULACOES));
  return resultado;
}

// --- tela ----------------------------------------------------------------------------------

function aplicarDados(novo) {
  dados = novo;
  const ciclo = dados.ciclo;
  const proximo = new Date(ciclo.proximo_ciclo_em);
  $("resumo-ciclo").textContent =
    `${ciclo.limite_slots} slot(s) a cada ${ciclo.intervalo_horas}h · próximo ciclo ` +
    (proximo <= new Date() ? "a qualquer momento" : `por volta de ${dataHora(proximo)}`);

  const cat = dados.catalogo;
  $("catalogo-status").textContent = cat.atualizado_em
    ? `catálogo de ${dataHora(new Date(cat.atualizado_em))}${cat.vencido ? " (vencido)" : ""}`
    : "catálogo ainda não baixado";
  if (cat.erro) avisar(cat.erro, true);
  renderizar();
}

function renderizar() {
  const lista = $("lista");
  const busca = $("busca").value.trim().toLowerCase();
  const soRodizio = $("so-rodizio").checked;
  const ordem = $("ordem").value;

  let itens = estadoAtual();
  if (busca) {
    itens = itens.filter((item) =>
      (item.nome || "").toLowerCase().includes(busca) || String(item.id).includes(busca));
  }
  if (soRodizio) itens = itens.filter((item) => item.no);
  itens.sort(comparador(ordem));

  cartoes.clear();
  const fragmento = document.createDocumentFragment();
  for (const item of itens) fragmento.appendChild(criarCartao(item));
  lista.replaceChildren(fragmento);
  if (!itens.length) {
    const vazio = document.createElement("p");
    vazio.className = "sutil";
    vazio.textContent = "Nenhum produto para mostrar.";
    lista.appendChild(vazio);
  }
  atualizarResumo();
}

function comparador(ordem) {
  const ultimo = (item) => (dados.historico[item.id] || {}).ultimo_sucesso_em || "";
  return (a, b) => {
    if (ordem === "nome") return (a.nome || "").localeCompare(b.nome || "", "pt-BR");
    if (ordem === "estoque") return (b.estoque ?? -1) - (a.estoque ?? -1);
    if (ordem === "sucesso") return ultimo(b).localeCompare(ultimo(a));
    return (b.no - a.no) || (b.peso - a.peso) || (a.nome || "").localeCompare(b.nome || "");
  };
}

function criarCartao(item) {
  const cartao = $("tpl-item").content.firstElementChild.cloneNode(true);
  cartao.dataset.id = item.id;
  const foto = cartao.querySelector(".foto");
  if (item.imagem_url && item.imagem_url.startsWith("https://")) {
    foto.src = item.imagem_url;
  } else {
    // sem foto: um bloco vazio no lugar, em vez do ícone de imagem quebrada
    const vazio = document.createElement("div");
    vazio.className = "foto";
    foto.replaceWith(vazio);
  }
  cartao.querySelector(".nome").textContent = item.nome || `Item ${item.id}`;
  cartao.querySelector(".meta").textContent = textoMeta(item);
  cartao.querySelector(".hist").textContent = textoHistorico(item.id);
  cartao.classList.toggle("inativo", !item.ativo);

  const caixa = cartao.querySelector(".no-rodizio");
  const slider = cartao.querySelector(".peso-slider");
  const numero = cartao.querySelector(".peso-num");
  caixa.addEventListener("change", () => editar(item.id, { no: caixa.checked }));
  slider.addEventListener("input", () => editar(item.id, { peso: Number(slider.value) }));
  numero.addEventListener("change", () => {
    const peso = Math.round(Number(numero.value));
    if (Number.isFinite(peso) && peso >= 1 && peso <= 1000) {
      editar(item.id, { peso });
    } else {
      atualizarCartao(item.id);
    }
  });
  cartoes.set(item.id, cartao);
  preencherControles(cartao, item);
  return cartao;
}

function atualizarCartao(id) {
  const cartao = cartoes.get(id);
  if (!cartao) return;
  preencherControles(cartao, estadoAtual().find((item) => item.id === id));
}

function preencherControles(cartao, item) {
  cartao.querySelector(".no-rodizio").checked = item.no;
  const slider = cartao.querySelector(".peso-slider");
  const numero = cartao.querySelector(".peso-num");
  slider.max = String(Math.max(100, item.peso));
  slider.value = String(item.peso);
  numero.value = String(item.peso);
  slider.disabled = numero.disabled = !item.no;
  cartao.classList.toggle("fora", !item.no);
  cartao.classList.toggle("alterado", edicoes.has(item.id));
}

let agendado = null;
function atualizarResumo() {
  const n = edicoes.size;
  $("barra-salvar").hidden = n === 0;
  $("pendentes").textContent = `${n} alteração(ões) não salva(s)`;
  // simulação é barata, mas não precisa rodar a cada pixel do slider
  clearTimeout(agendado);
  agendado = setTimeout(atualizarChances, 120);
}

function atualizarChances() {
  const itens = estadoAtual();
  const total = itens.filter((i) => i.no).reduce((soma, i) => soma + i.peso, 0);
  const porId = chances(itens, dados.ciclo.limite_slots);
  for (const item of itens) {
    const cartao = cartoes.get(item.id);
    if (!cartao) continue;
    cartao.querySelector(".chance").textContent = item.no
      ? `${pct(item.peso / total)} do peso · entra em ~${pct(porId.get(item.id) || 0)} dos ciclos`
      : "fora do rodízio";
  }
}

function textoMeta(item) {
  if (!item.ativo) return `ID ${item.id} · não está entre os anúncios ativos da loja`;
  const partes = [`ID ${item.id}`];
  if (item.preco_min != null) {
    partes.push(item.preco_max != null && item.preco_max !== item.preco_min
      ? `${brl.format(item.preco_min)} – ${brl.format(item.preco_max)}`
      : brl.format(item.preco_min));
  } else if (item.tem_variacoes) {
    partes.push("preço varia");
  }
  if (item.estoque != null) partes.push(`estoque ${item.estoque}`);
  if (item.status) partes.push(item.status === "NORMAL" ? "ativo" : item.status.toLowerCase());
  return partes.join(" · ");
}

function textoHistorico(id) {
  const h = dados.historico[id];
  if (!h) return "nunca impulsionado";
  const ultimo = h.ultimo_sucesso_em ? `último boost ${dataHora(new Date(h.ultimo_sucesso_em))}` : "sem boost com sucesso";
  return `${ultimo} · 7 dias: ${h.sucessos_7d}/${h.tentativas_7d} com sucesso`;
}

function avisar(texto, erro) {
  const aviso = $("aviso");
  aviso.textContent = texto;
  aviso.classList.toggle("erro", Boolean(erro));
  aviso.hidden = false;
}

const pct = (x) => `${(x * 100).toFixed(x < 0.1 ? 1 : 0)}%`;
const dataHora = (d) => d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });

// --- abas "No ar agora" e "Relatório" ------------------------------------------------------
// Carregadas só quando a aba é aberta (uma requisição, agregados prontos do Pi).

const ABAS = ["pesos", "agora", "relatorio"];

function abrirAba(nome) {
  if (!ABAS.includes(nome)) nome = "pesos";
  for (const aba of ABAS) $(`aba-${aba}`).hidden = aba !== nome;
  document.querySelectorAll(".aba").forEach((botao) => {
    botao.setAttribute("aria-selected", String(botao.dataset.aba === nome));
  });
  if (location.hash !== `#${nome}`) history.replaceState(null, "", `#${nome}`);
  if (nome !== "pesos") carregarRelatorio();
}

async function carregarRelatorio() {
  try {
    const r = await api("GET", `/api/relatorio?dias=${$("dias").value}`);
    desenharAgora(r);
    desenharRelatorio(r);
  } catch (erro) {
    avisar(`Não foi possível carregar o relatório: ${erro.message}`, true);
  }
}

function el(tag, classe, texto) {
  const e = document.createElement(tag);
  if (classe) e.className = classe;
  if (texto !== undefined) e.textContent = texto;
  return e;
}

function linhaItem(r, id, direita, progresso) {
  const linha = el("div", "linha-item");
  const url = r.imagens[id];
  if (url && url.startsWith("https://")) {
    const foto = el("img", "foto");
    foto.src = url;
    foto.alt = "";
    foto.loading = "lazy";
    foto.referrerPolicy = "no-referrer";
    linha.appendChild(foto);
  } else {
    linha.appendChild(el("div", "foto"));
  }
  const meio = el("div", "info");
  meio.appendChild(el("p", "nome", r.nomes[id] || `Item ${id}`));
  if (progresso !== undefined) {
    const barra = el("div", "progresso");
    const cheio = el("div");
    cheio.style.width = `${Math.max(0, Math.min(1, progresso)) * 100}%`;
    barra.appendChild(cheio);
    meio.appendChild(barra);
  }
  linha.append(meio, direita);
  return linha;
}

function desenharAgora(r) {
  const agora = r.agora;
  const horas = agora.duracao_boost_horas;
  $("agora-legenda").textContent = agora.no_ar.length
    ? `${agora.no_ar.length} item(ns) com boost ativo (cada boost dura ${horas}h).`
    : `Nenhum boost ativo agora (cada boost dura ${horas}h).`;
  $("agora-lista").replaceChildren(...agora.no_ar.map((item) => {
    const min = item.minutos_restantes;
    const resta = min >= 60 ? `${Math.floor(min / 60)}h${String(min % 60).padStart(2, "0")}` : `${min} min`;
    const direita = el("span", "etiqueta ok", `expira em ${resta}`);
    return linhaItem(r, item.id, direita, min / (horas * 60));
  }));

  const ultimo = agora.ultimo_ciclo;
  if (!ultimo.em) {
    $("ultimo-legenda").textContent = "Nenhum ciclo registrado ainda.";
    $("ultimo-lista").replaceChildren();
    return;
  }
  const ok = ultimo.itens.filter((i) => i.sucesso).length;
  $("ultimo-legenda").textContent =
    `${dataHora(new Date(ultimo.em))} · ${ok} de ${ultimo.itens.length} com sucesso`;
  $("ultimo-lista").replaceChildren(...ultimo.itens.map((item) => {
    const direita = el("span", `etiqueta ${item.sucesso ? "ok" : "falha"}`,
      item.sucesso ? "impulsionado" : "falhou");
    if (!item.sucesso) direita.title = item.mensagem;
    const linha = linhaItem(r, item.id, direita);
    if (!item.sucesso) linha.querySelector(".info").appendChild(el("p", "sutil", item.mensagem));
    return linha;
  }));
}

function desenharRelatorio(r) {
  const rel = r.relatorio;
  const res = rel.resumo;
  const taxa = res.tentativas ? res.sucessos / res.tentativas : 0;
  const numeros = [
    ["boosts com sucesso", res.sucessos],
    ["falhas", res.falhas],
    ["taxa de sucesso", pct(taxa)],
    ["ciclos", `${res.ciclos_com_sucesso}/${res.ciclos}`],
    ["itens impulsionados", res.itens_impulsionados],
  ];
  $("rel-resumo").replaceChildren(...numeros.map(([rotulo, valor]) => {
    const caixa = el("div", "numero");
    caixa.append(el("strong", "", String(valor)), el("span", "sutil", rotulo));
    return caixa;
  }));

  const maximo = Math.max(1, ...rel.por_dia.map((d) => d.sucessos + d.falhas));
  const barras = $("rel-dias");
  barras.replaceChildren(...rel.por_dia.map((d) => {
    const coluna = el("div", "barra");
    coluna.title = `${dia(d.dia)}: ${d.sucessos} ok, ${d.falhas} falha(s)`;
    const ok = el("div", "ok");
    ok.style.height = `${(d.sucessos / maximo) * 100}%`;
    const falha = el("div", "falha");
    falha.style.height = `${(d.falhas / maximo) * 100}%`;
    coluna.append(ok, falha);
    return coluna;
  }));
  const eixo = el("div", "eixo sutil");
  eixo.append(el("span", "", dia(rel.por_dia[0].dia)),
    el("span", "", `máx. ${maximo}/dia · verde ok, vermelho falha`),
    el("span", "", dia(rel.por_dia[rel.por_dia.length - 1].dia)));
  barras.after(eixo);
  if (eixo.nextElementSibling && eixo.nextElementSibling.classList.contains("eixo")) {
    eixo.nextElementSibling.remove();
  }

  const tabela = $("rel-itens");
  const cabecalho = el("tr");
  for (const [titulo, classe] of [["Item", ""], ["Peso", "num"], ["OK", "num"], ["Falhas", "num"],
    ["% boosts", "num"], ["% peso", "num"], ["Último boost", ""]]) {
    cabecalho.appendChild(el("th", classe, titulo));
  }
  const linhas = rel.por_item.map((item) => {
    const tr = el("tr");
    const desvio = item.parte_dos_boosts - item.parte_do_peso;
    const classeDesvio = item.peso && Math.abs(desvio) >= 0.05
      ? (desvio > 0 ? "num desvio-acima" : "num desvio-abaixo") : "num";
    const nome = el("td", "nome-item", r.nomes[item.id] || `Item ${item.id}`);
    nome.title = `${r.nomes[item.id] || ""} (ID ${item.id})`;
    tr.append(
      nome,
      el("td", "num", item.peso ?? "—"),
      el("td", "num", item.sucessos),
      el("td", "num", item.falhas),
      el("td", classeDesvio, pct(item.parte_dos_boosts)),
      el("td", "num", item.peso ? pct(item.parte_do_peso) : "fora"),
      el("td", "", item.ultimo_sucesso_em ? dataHora(new Date(item.ultimo_sucesso_em)) : "—"),
    );
    return tr;
  });
  tabela.replaceChildren(cabecalho, ...linhas);

  $("rel-erros").replaceChildren(...(rel.erros.length ? rel.erros.map((e) => {
    const p = el("p", "sutil");
    p.append(el("strong", "", `${e.vezes}× `), document.createTextNode(e.mensagem));
    return p;
  }) : [el("p", "sutil", "Nenhuma falha no período.")]));
}

const dia = (iso) => new Date(`${iso}T12:00:00`).toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" });

// --- eventos -------------------------------------------------------------------------------

$("btn-atualizar").addEventListener("click", atualizarCatalogo);
$("btn-salvar").addEventListener("click", salvar);
$("btn-descartar").addEventListener("click", () => { edicoes.clear(); renderizar(); });
$("busca").addEventListener("input", () => dados && renderizar());
$("so-rodizio").addEventListener("change", () => dados && renderizar());
$("ordem").addEventListener("change", () => dados && renderizar());
window.addEventListener("beforeunload", (evento) => {
  if (edicoes.size) evento.preventDefault();
});
document.querySelectorAll(".aba").forEach((botao) => {
  botao.addEventListener("click", () => abrirAba(botao.dataset.aba));
});
$("dias").addEventListener("change", carregarRelatorio);
window.addEventListener("hashchange", () => abrirAba(location.hash.slice(1)));

carregar();
abrirAba(location.hash.slice(1));
