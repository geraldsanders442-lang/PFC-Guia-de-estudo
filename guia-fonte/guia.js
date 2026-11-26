// Interações do guia: tema, menu, busca, cópia, diagramas e simulado
(() => {
  const $ = (s, raiz = document) => raiz.querySelector(s);
  const $$ = (s, raiz = document) => [...raiz.querySelectorAll(s)];
  const ler = (chave) => { try { return localStorage.getItem(chave); } catch { return null; } };
  const gravar = (chave, valor) => { try { localStorage.setItem(chave, valor); } catch { /* navegação privada */ } };
  const semAcento = (t) => t.toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[̀-ͯ]/g, '');

  const body = document.body;
  const tema = $('#tema-toggle');
  if (ler('escape-guia-tema') === 'escuro') document.documentElement.dataset.tema = 'escuro';
  const rotularTema = () => {
    const escuro = document.documentElement.dataset.tema === 'escuro';
    tema.textContent = escuro ? 'Tema: escuro' : 'Tema: claro';
    $('meta[name="theme-color"]').content = escuro ? '#171b18' : '#f6f5f1';
  };
  rotularTema();
  tema.addEventListener('click', () => {
    const novo = document.documentElement.dataset.tema === 'escuro' ? 'claro' : 'escuro';
    document.documentElement.dataset.tema = novo;
    gravar('escape-guia-tema', novo);
    rotularTema();
  });
  $('#imprimir').addEventListener('click', () => window.print());

  const menu = $('#menu-toggle');
  const fecharMenu = () => { body.classList.remove('menu-open'); menu.setAttribute('aria-expanded', 'false'); };
  menu.addEventListener('click', () => menu.setAttribute('aria-expanded', String(body.classList.toggle('menu-open'))));
  document.addEventListener('click', (e) => { if (!e.target.closest('.sidebar') && !e.target.closest('#menu-toggle')) fecharMenu(); });
  $('#sidebar').addEventListener('click', (e) => { if (e.target.closest('a')) fecharMenu(); });

  // Busca em todas as páginas
  const campo = $('#busca');
  const achados = $('#achados');
  const indice = (window.INDICE || []).map((i) => ({ ...i, n: semAcento(`${i.t} ${i.x}`) }));
  campo.addEventListener('input', () => {
    const termos = semAcento(campo.value.trim()).split(/\s+/).filter(Boolean);
    achados.textContent = '';
    achados.hidden = !termos.length;
    if (!termos.length) return;
    const lista = indice.filter((i) => termos.every((t) => i.n.includes(t)))
      .sort((a, b) => Number(semAcento(b.t).includes(termos[0])) - Number(semAcento(a.t).includes(termos[0])));
    if (!lista.length) { achados.appendChild(Object.assign(document.createElement('p'), { textContent: 'Nada encontrado.' })); return; }
    lista.slice(0, 12).forEach((i) => {
      const a = Object.assign(document.createElement('a'), { href: i.u, textContent: i.t });
      a.appendChild(Object.assign(document.createElement('small'), { textContent: i.p }));
      achados.appendChild(a);
    });
    if (lista.length > 12) achados.appendChild(Object.assign(document.createElement('p'), { textContent: `+ ${lista.length - 12} resultados. Refine a busca.` }));
  });

  const links = $$('#locais a');
  const observador = new IntersectionObserver((entradas) => entradas.forEach((e) => {
    if (e.isIntersecting) links.forEach((l) => l.classList.toggle('active', l.hash === `#${e.target.id}`));
  }), { rootMargin: '-18% 0px -70% 0px' });
  $$('.section').forEach((s) => observador.observe(s));

  $$('.copy').forEach((botao) => botao.addEventListener('click', async () => {
    const codigo = $('code', botao.parentElement).cloneNode(true);
    $$('.ln', codigo).forEach((n) => n.remove());
    try { await navigator.clipboard.writeText(codigo.textContent); botao.textContent = 'Copiado'; }
    catch { botao.textContent = 'Selecione o código'; }
    setTimeout(() => { botao.textContent = 'Copiar'; }, 1400);
  }));

  // Diagramas começam em tamanho legível (com rolagem); o botão alterna a escala
  const escalar = (figura) => {
    const grande = figura.classList.contains('grande');
    const svg = $('pre.mermaid svg', figura);
    if (svg && svg.viewBox.baseVal.width) {
      const largura = svg.viewBox.baseVal.width;
      svg.style.maxWidth = 'none';
      svg.style.width = grande ? `${Math.round(largura * 1.1)}px` : '100%';
      svg.style.minWidth = grande ? '' : `${Math.round(Math.min(largura * 0.72, 1250))}px`;
    }
    $('.ampliar', figura).textContent = grande ? 'Reduzir' : 'Ampliar';
  };
  $$('.ampliar').forEach((b) => b.addEventListener('click', () => {
    const figura = b.closest('.diagrama');
    figura.classList.toggle('grande');
    escalar(figura);
  }));
  if (window.mermaid) {
    window.mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'strict', sequence: { useMaxWidth: true, wrap: true, width: 140, actorMargin: 30 }, flowchart: { useMaxWidth: true } });
    window.mermaid.run({ querySelector: 'pre.mermaid' }).then(() => $$('pre.mermaid').forEach((p) => escalar(p.closest('.diagrama')))).catch((e) => console.error('diagrama', e));
  }

  // Simulado
  const perguntas = $$('.pergunta');
  if (!perguntas.length) return;
  let sabidas = new Set();
  try { sabidas = new Set(JSON.parse(ler('escape-guia-sabidas') || '[]')); } catch { /* dado antigo */ }
  let sorteada = null;
  const filtrar = () => {
    const cat = $('#f-cat').value;
    const pri = $('#f-pri').value;
    let visiveis = 0;
    perguntas.forEach((p) => {
      const id = $('input[data-q]', p).dataset.q;
      const mostra = sorteada ? p === sorteada : (!cat || p.dataset.cat === cat) && (!pri || p.dataset.pri === pri)
        && (!$('#f-dificil').checked || p.dataset.dificil === '1') && (!$('#f-faltam').checked || !sabidas.has(id));
      p.hidden = !mostra;
      visiveis += mostra ? 1 : 0;
    });
    $$('.grupo-q').forEach((g) => { g.hidden = !$('.pergunta:not([hidden])', g); });
    $('#nenhuma').style.display = visiveis ? 'none' : 'block';
    $('#mostrar-todas').hidden = !sorteada;
    $('#placar').textContent = `${visiveis} na tela · você marcou ${perguntas.filter((p) => sabidas.has($('input[data-q]', p).dataset.q)).length} de ${perguntas.length} como dominadas (salvo neste navegador).`;
  };
  $$('input[data-q]').forEach((c) => {
    c.checked = sabidas.has(c.dataset.q);
    c.addEventListener('change', () => {
      if (c.checked) sabidas.add(c.dataset.q); else sabidas.delete(c.dataset.q);
      gravar('escape-guia-sabidas', JSON.stringify([...sabidas]));
      filtrar();
    });
  });
  ['#f-cat', '#f-pri', '#f-dificil', '#f-faltam'].forEach((s) => $(s).addEventListener('change', () => { sorteada = null; filtrar(); }));
  const fechar = () => $$('.pergunta details').forEach((d) => { d.open = false; });
  $('#fechar-todas').addEventListener('click', fechar);
  $('#sortear').addEventListener('click', () => {
    sorteada = null;
    filtrar();
    const opcoes = perguntas.filter((p) => !p.hidden);
    if (!opcoes.length) return;
    sorteada = opcoes[Math.floor(Math.random() * opcoes.length)];
    fechar();
    filtrar();
    sorteada.scrollIntoView({ block: 'start' });
  });
  $('#mostrar-todas').addEventListener('click', () => { sorteada = null; filtrar(); });
  // Um link direto para uma pergunta vence filtros anteriores
  window.addEventListener('hashchange', () => { sorteada = null; filtrar(); document.getElementById(location.hash.slice(1))?.scrollIntoView(); });
  filtrar();
})();
