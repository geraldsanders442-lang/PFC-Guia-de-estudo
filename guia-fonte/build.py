# Gera o site do guia: python build.py <pasta-do-codigo-do-Escape.py>
# Os trechos de código são lidos do repositório; se um caminho ou padrão sumir, o build falha.
import html, json, pathlib, re, shutil, subprocess, sys

AQUI = pathlib.Path(__file__).resolve().parent
SAIDA = AQUI.parent / "guia-estudos"
CODIGO = pathlib.Path(sys.argv[1]).resolve()
COMMIT = subprocess.check_output(["git", "-C", str(CODIGO), "rev-parse", "HEAD"], text=True).strip()
REPO = "https://github.com/pfcumc2026/Escape-Room-PFC"
GUIA_ANTIGO = AQUI / "base" / "guia-anterior.html"

PAGINAS = [
    ("index.html", "Guia base", "Fundamentos e visão geral"),
    ("codigo.html", "Código por funcionalidade", "Do clique ao resultado"),
    ("api-banco.html", "API, middlewares e banco", "Endpoints, cadeia e MongoDB"),
    ("diagramas.html", "Diagramas e fluxos", "Arquitetura e sequências"),
    ("seguranca.html", "Segurança, LGPD e limites", "Ameaças, provas e lacunas"),
    ("testes.html", "Testes e demonstração", "Comandos e roteiro ao vivo"),
    ("simposio.html", "O que a banca cobrou", "Análise do simpósio"),
    ("simulado.html", "Simulado da banca", "Perguntas e respostas"),
]

TRECHOS = []


def esc(t):
    return html.escape(str(t), quote=True)


def ler(caminho):
    arquivo = CODIGO / caminho
    if not arquivo.is_file():
        raise SystemExit(f"arquivo inexistente: {caminho}")
    return arquivo.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")


def localizar(caminho, alvo):
    """alvo = 'a-b' (linhas) ou um texto: pega o bloco que começa na linha com o texto, até fechar chaves."""
    linhas = ler(caminho)
    faixa = re.fullmatch(r"(\d+)(?:-(\d+))?", alvo)
    if faixa:
        a, b = int(faixa[1]), int(faixa[2] or faixa[1])
        if not 1 <= a <= b <= len(linhas):
            raise SystemExit(f"faixa inválida {caminho}:{alvo}")
        return a, b, linhas
    inicio = next((i for i, l in enumerate(linhas) if alvo in l), None)
    if inicio is None:
        raise SystemExit(f"padrão não encontrado em {caminho}: {alvo}")
    primeira = linhas[inicio]
    recuo = len(primeira) - len(primeira.lstrip())
    if primeira.strip().startswith("def "):  # Python embutido: vai até o recuo voltar
        fim = inicio + 1
        while fim < len(linhas) and (not linhas[fim].strip() or len(linhas[fim]) - len(linhas[fim].lstrip()) > recuo):
            fim += 1
        while not linhas[fim - 1].strip():
            fim -= 1
        return inicio + 1, fim, linhas
    if not primeira.rstrip().endswith(("{", "(", "[")):
        return inicio + 1, inicio + 1, linhas
    for i in range(inicio + 1, len(linhas)):
        l = linhas[i]
        if l.strip() and len(l) - len(l.lstrip()) <= recuo and l.lstrip()[0] in "})]":
            return inicio + 1, i + 1, linhas
    raise SystemExit(f"bloco sem fim em {caminho}: {alvo}")


def link(caminho, a=None, b=None):
    ancora = f"#L{a}-L{b}" if a else ""
    return f"{REPO}/blob/{COMMIT}/{caminho}{ancora}"


def trecho(caminho, alvo):
    a, b, linhas = localizar(caminho, alvo)
    corpo = linhas[a - 1:b]
    recuo = min((len(l) - len(l.lstrip()) for l in corpo if l.strip()), default=0)
    texto = "\n".join(f'<span class="ln">{n}</span>{esc(l[recuo:])}' for n, l in zip(range(a, b + 1), corpo))
    TRECHOS.append(f"{caminho}:{a}-{b}  {corpo[0].strip()[:70]}")
    return (f'<div class="codebox"><div class="code-label"><a href="{link(caminho, a, b)}" target="_blank" rel="noopener">'
            f'{esc(caminho)} · linhas {a}–{b}</a></div><button class="copy" type="button">Copiar</button>'
            f"<pre><code>{texto}</code></pre></div>")


def referencia(caminho, alvo=None):
    if alvo:
        a, b, _ = localizar(caminho, alvo)
        return f'<a class="ref" href="{link(caminho, a, b)}" target="_blank" rel="noopener">{esc(caminho)}:{a}</a>'
    ler(caminho)
    return f'<a class="ref" href="{link(caminho)}" target="_blank" rel="noopener">{esc(caminho)}</a>'


def inline(t):
    guardados = []

    def guardar(valor):
        guardados.append(valor)
        return f"\x00{len(guardados) - 1}\x00"

    t = re.sub(r"\{\{ref\|([^|}]+)(?:\|([^}]+))?\}\}", lambda m: guardar(referencia(m[1], m[2])), t)
    t = re.sub(r"`([^`]+)`", lambda m: guardar(f"<code>{esc(m[1])}</code>"), t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: guardar(f'<a href="{esc(m[2])}">{esc(m[1])}</a>'), t)
    t = esc(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    while "\x00" in t:
        t = re.sub("\x00(\\d+)\x00", lambda m: guardados[int(m[1])], t)
    return t


def markdown(texto):
    """Subconjunto de Markdown usado nas páginas."""
    saida, linhas, i = [], texto.split("\n"), 0
    while i < len(linhas):
        l = linhas[i]
        s = l.strip()
        if not s:
            i += 1
        elif s.startswith("```"):
            tipo = s[3:].strip()
            bloco = []
            i += 1
            while linhas[i].strip() != "```":
                bloco.append(linhas[i])
                i += 1
            i += 1
            corpo = "\n".join(bloco)
            if tipo == "mermaid":
                saida.append(f'<figure class="diagrama"><div class="diagrama-acoes"><button type="button" class="ampliar">Ampliar</button></div>'
                             f'<div class="diagrama-rolagem"><pre class="mermaid">{esc(corpo)}</pre></div></figure>')
            else:
                saida.append(f'<div class="codebox"><div class="code-label">{esc(tipo or "exemplo")}</div><button class="copy" type="button">Copiar</button><pre><code>{esc(corpo)}</code></pre></div>')
        elif m := re.fullmatch(r"\{\{codigo\|([^|]+)\|(.+)\}\}", s):
            saida.append(trecho(m[1], m[2]))
            i += 1
        elif s.startswith("<"):
            saida.append(l)
            i += 1
        elif s.startswith("#### "):
            saida.append(f"<h4>{inline(s[5:])}</h4>")
            i += 1
        elif s.startswith("### "):
            saida.append(f"<h3>{inline(s[4:])}</h3>")
            i += 1
        elif s.startswith("|"):
            tab = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                celulas = re.split(r"(?<!\\)\|", linhas[i].strip().strip("|"))
                tab.append([c.strip().replace("\\|", "|") for c in celulas])
                i += 1
            cab = "".join(f"<th>{inline(c)}</th>" for c in tab[0])
            corpo = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in tab[1:])
            saida.append(f'<div class="table-wrap"><table><thead><tr>{cab}</tr></thead><tbody>{corpo}</tbody></table></div>')
        elif re.match(r"(- |\d+\. )", s):
            marca = "ol" if s[0].isdigit() else "ul"
            itens = []
            while i < len(linhas) and re.match(r"(- |\d+\. )", linhas[i].strip()):
                itens.append(re.sub(r"^(- |\d+\. )", "", linhas[i].strip()))
                i += 1
            saida.append(f"<{marca}>" + "".join(f"<li>{inline(x)}</li>" for x in itens) + f"</{marca}>")
        elif s.startswith("> "):
            classe = "note"
            conteudo = s[2:]
            if conteudo.startswith("!"):
                classe, conteudo = "note alerta", conteudo[1:].strip()
            saida.append(f'<div class="{classe}">{inline(conteudo)}</div>')
            i += 1
        elif s.startswith("??? "):
            titulo = s[4:]
            bloco = []
            i += 1
            while linhas[i].strip() != "???":
                bloco.append(linhas[i])
                i += 1
            i += 1
            saida.append(f'<details class="qa fundo"><summary>{inline(titulo)}</summary><div class="answer">{markdown(chr(10).join(bloco))}</div></details>')
        else:
            saida.append(f"<p>{inline(s)}</p>")
            i += 1
    return "\n".join(saida)


def pagina_md(nome):
    """Arquivo: cabeçalho '# Título | subtítulo' e seções '## id | título | resumo'."""
    texto = (AQUI / "conteudo" / nome).read_text(encoding="utf-8")
    cabeca, *partes = re.split(r"(?m)^## ", texto)
    primeira, _, intro = cabeca.partition("\n")
    titulo, sub = [x.strip() for x in primeira.lstrip("# ").split("|")]
    corpo = [f'<header class="intro"><span class="eyebrow">Preparação para a banca</span><h1>{esc(titulo)}</h1><p>{esc(sub)}</p></header>', markdown(intro)]
    secoes = []
    for n, parte in enumerate(partes, 1):
        linha, _, resto = parte.partition("\n")
        ident, t, resumo = [x.strip() for x in linha.split("|")]
        secoes.append((ident, t))
        corpo.append(f'<section class="section" id="{ident}" data-title="{esc(t)}"><div class="section-head"><span class="section-number">{n:02d}</span>'
                     f'<div><h2>{esc(t)}</h2><p class="lede">{inline(resumo)}</p></div></div>\n{markdown(resto)}</section>')
    return titulo, "\n".join(corpo), secoes


def ler_perguntas():
    perguntas = []
    for arquivo in sorted((AQUI / "conteudo").glob("perguntas*.txt")):
        for bloco in re.split(r"(?m)^=== ", arquivo.read_text(encoding="utf-8"))[1:]:
            cabeca, _, resto = bloco.partition("\n")
            campos = [c.strip() for c in cabeca.split("|")]
            p = {"id": campos[0], "cat": campos[1], "pri": campos[2], "dificil": "dificil" in campos[3:], "S": []}
            chave = None
            for linha in resto.split("\n"):
                m = re.match(r"([PQOECSD]): ?(.*)", linha)
                if m:
                    chave = m[1]
                    if chave == "S":
                        p["S"].append(m[2])
                    else:
                        p[chave] = m[2]
                elif chave and chave != "S":
                    p[chave] += "\n" + linha
            faltam = [c for c in "PQOECD" if not p.get(c)]
            if faltam or not p["S"]:
                raise SystemExit(f"pergunta {p['id']} sem campos: {faltam or 'S'}")
            perguntas.append(p)
    ids = [p["id"] for p in perguntas]
    if len(ids) != len(set(ids)):
        raise SystemExit("id de pergunta repetido")
    return perguntas


def simulado():
    perguntas = ler_perguntas()
    categorias = list(dict.fromkeys(p["cat"] for p in perguntas))
    ordem = {"alta": 0, "média": 1, "baixa": 2}
    opcoes = "".join(f'<option value="{esc(c)}">{esc(c)} ({sum(p["cat"] == c for p in perguntas)})</option>' for c in categorias)
    blocos = []
    for c in categorias:
        itens = []
        for p in sorted((x for x in perguntas if x["cat"] == c), key=lambda x: ordem[x["pri"]]):
            provas = []
            for ref in [r.strip() for r in p["C"].split(";;") if r.strip()]:
                caminho, _, alvo = [x.strip() for x in ref.partition("::")]
                provas.append(trecho(caminho, alvo) if alvo else f"<p>{referencia(caminho)}</p>")
            seguintes = "".join(
                f'<details class="seguinte"><summary>{inline(s.split("->", 1)[0].strip())}</summary><p>{inline(s.split("->", 1)[1].strip())}</p></details>'
                for s in p["S"])
            marca = '<span class="selo dura">difícil</span>' if p["dificil"] else ""
            itens.append(f'''<article class="pergunta" id="q-{p["id"]}" data-cat="{esc(c)}" data-pri="{p["pri"]}" data-dificil="{int(p["dificil"])}">
<header><div class="selos"><span class="selo pri-{p["pri"][0]}">prioridade {p["pri"]}</span>{marca}<label class="estudei"><input type="checkbox" data-q="{p["id"]}"> já sei explicar</label></div>
<h3>{inline(p["P"])}</h3><p class="quer"><strong>O que o professor quer descobrir:</strong> {inline(p["Q"])}</p></header>
<details class="nivel n1"><summary>Nível 1 · Resposta oral</summary><div>{markdown(p["O"])}</div></details>
<details class="nivel n2"><summary>Nível 2 · Entendendo a resposta</summary><div>{markdown(p["E"])}</div></details>
<details class="nivel n3"><summary>Nível 3 · Prova no código</summary><div>{"".join(provas)}</div></details>
<details class="nivel demo"><summary>Como demonstrar</summary><div>{markdown(p["D"])}</div></details>
<div class="seguintes"><p>Se a banca aprofundar:</p>{seguintes}</div></article>''')
        slug = re.sub(r"\W+", "-", c.lower()).strip("-")
        blocos.append(f'<section class="section grupo-q" id="cat-{slug}" data-title="{esc(c)}"><h2>{esc(c)}</h2>{"".join(itens)}</section>')
    secoes = [(f"cat-{re.sub(chr(92) + 'W+', '-', c.lower()).strip('-')}", c) for c in categorias]
    cabeca = f'''<header class="intro"><span class="eyebrow">Preparação para a banca</span><h1>Simulado da banca — perguntas e respostas do Escape.py</h1>
<p>{len(perguntas)} perguntas em {len(categorias)} categorias, {sum(p["dificil"] for p in perguntas)} delas marcadas como difíceis. Responda em voz alta antes de abrir cada nível.</p></header>
<div class="filtros" role="search">
<label>Categoria<select id="f-cat"><option value="">Todas</option>{opcoes}</select></label>
<label>Prioridade<select id="f-pri"><option value="">Todas</option><option>alta</option><option>média</option><option>baixa</option></select></label>
<label class="marca"><input type="checkbox" id="f-dificil"> Só difíceis</label>
<label class="marca"><input type="checkbox" id="f-faltam"> Só as que faltam</label>
<button type="button" id="sortear">Sortear pergunta</button><button type="button" id="mostrar-todas" hidden>Mostrar todas</button><button type="button" id="fechar-todas">Fechar respostas</button>
<p id="placar" aria-live="polite"></p></div>
<div class="no-results" id="nenhuma">Nenhuma pergunta com esses filtros.</div>'''
    return "Simulado da banca", cabeca + "\n".join(blocos), secoes


def guia_base():
    texto = GUIA_ANTIGO.read_text(encoding="utf-8").replace("\r\n", "\n")
    artigo = texto[texto.index('<article class="content">') + len('<article class="content">'):texto.index("</article>")]
    css = texto[texto.index("<style>") + 7:texto.index("</style>")]
    ajustes = json.loads((AQUI / "base" / "ajustes.json").read_text(encoding="utf-8"))
    for ident, arquivo in ajustes["secoes"].items():
        novo = (AQUI / "base" / arquivo).read_text(encoding="utf-8")
        linha, _, resto = novo.partition("\n")
        titulo, resumo = [x.strip() for x in linha.split("|")]
        padrao = re.compile(rf'(<section class="section" id="{ident}"[^>]*>\s*<div class="section-head"><span class="section-number">(\d+)</span>).*?</section>', re.S)
        artigo, n = padrao.subn(lambda m: f'{m[1]}<div><h2>{esc(titulo)}</h2><p class="lede">{inline(resumo)}</p></div></div>\n{markdown(resto)}\n</section>', artigo)
        if n != 1:
            raise SystemExit(f"seção não encontrada no guia base: {ident}")
    for antigo, novo in ajustes["trocas"]:
        if antigo.startswith("re:"):
            artigo, n = re.subn(antigo[3:], lambda m: novo, artigo, flags=re.S)
        else:
            n = artigo.count(antigo)
            artigo = artigo.replace(antigo, novo)
        if not n:
            raise SystemExit(f"troca sem efeito: {antigo[:80]}")
    secoes = re.findall(r'<section class="section" id="([^"]+)" data-title="([^"]+)"', artigo)
    return "Guia base", artigo, [(i, html.unescape(t)) for i, t in secoes], css


def texto_puro(t):
    t = re.sub(r"(?s)<(pre|svg|select)[^>]*>.*?</\1>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def montar(arquivo, titulo, corpo, secoes):
    paginas = "".join(f'<a href="{a}"{" class=atual aria-current=page" if a == arquivo else ""}><b>{esc(t)}</b><small>{esc(d)}</small></a>' for a, t, d in PAGINAS)
    locais = "".join(f'<a href="#{i}">{esc(t)}</a>' for i, t in secoes)
    mermaid = '<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>' if 'class="mermaid"' in corpo else ""
    return f'''<!doctype html>
<html lang="pt-BR" data-tema="claro">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f6f5f1">
<title>{esc(titulo)} · Escape.py</title>
<link rel="stylesheet" href="assets/guia.css">
</head>
<body>
<div class="layout">
<aside class="sidebar" id="sidebar" aria-label="Navegação do guia">
  <a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">E</span><span><strong>Escape.py</strong><small>Guia de estudos do projeto</small></span></a>
  <label class="small" for="busca" style="display:block;margin-top:14px">Buscar em todo o guia</label>
  <input id="busca" class="nav-search" type="search" placeholder="Ex.: JWT, gameHistory, SSE…" autocomplete="off">
  <div id="achados" hidden></div>
  <nav id="navegacao">
    <div class="nav-group"><p class="nav-title">Páginas</p><div class="nav-list paginas">{paginas}</div></div>
    <div class="nav-group"><p class="nav-title">Nesta página</p><div class="nav-list" id="locais">{locais}</div></div>
  </nav>
  <div class="side-foot">Baseado no código do repositório Escape-Room-PFC, branch main, commit <a href="{REPO}/tree/{COMMIT}">{COMMIT[:7]}</a> (18/11/2026).</div>
</aside>
<main class="main" id="inicio">
  <header class="topbar"><div style="display:flex;align-items:center;gap:10px"><button class="menu-button" id="menu-toggle" aria-label="Abrir navegação" aria-expanded="false">☰</button><span class="crumb">Guia para a banca / {esc(titulo)}</span></div><div class="top-actions"><button class="icon-button" id="tema-toggle" type="button" aria-label="Alternar tema">Tema: claro</button><button class="icon-button" id="imprimir" type="button">Imprimir / PDF</button></div></header>
  <article class="content">
{corpo}
  </article>
</main>
</div>
{mermaid}
<script src="assets/busca.js"></script>
<script src="assets/guia.js"></script>
</body>
</html>
'''


def main():
    (SAIDA / "assets" / "diagramas").mkdir(parents=True, exist_ok=True)
    base_titulo, base_corpo, base_secoes, css = guia_base()
    (SAIDA / "assets" / "guia.css").write_text(css.strip() + "\n" + (AQUI / "extra.css").read_text(encoding="utf-8"), encoding="utf-8")
    shutil.copy(AQUI / "guia.js", SAIDA / "assets" / "guia.js")
    for imagem in (AQUI / "diagramas").glob("*.png"):
        shutil.copy(imagem, SAIDA / "assets" / "diagramas" / imagem.name)

    indice = []
    for arquivo, rotulo, _ in PAGINAS:
        if arquivo == "index.html":
            titulo, corpo, secoes = base_titulo, base_corpo, base_secoes
        elif arquivo == "simulado.html":
            titulo, corpo, secoes = simulado()
        else:
            _, corpo, secoes = pagina_md(arquivo.replace(".html", ".md"))
            titulo = rotulo
        (SAIDA / arquivo).write_text(montar(arquivo, titulo, corpo, secoes), encoding="utf-8")
        if arquivo == "simulado.html":
            for q in re.finditer(r'(?s)<article class="pergunta" id="([^"]+)".*?<h3>(.*?)</h3>(.*?)</article>', corpo):
                indice.append({"u": f"{arquivo}#{q[1]}", "p": titulo, "t": texto_puro(q[2]), "x": texto_puro(q[3]).lower()})
        else:
            for s in re.finditer(r'(?s)<section class="section" id="([^"]+)" data-title="([^"]+)">(.*?)</section>', corpo):
                indice.append({"u": f"{arquivo}#{s[1]}", "p": titulo, "t": html.unescape(s[2]), "x": texto_puro(s[3]).lower()})
    (SAIDA / "assets" / "busca.js").write_text("window.INDICE=" + json.dumps(indice, ensure_ascii=False) + ";\n", encoding="utf-8")
    (SAIDA / ".nojekyll").write_text("", encoding="utf-8")

    # Links internos
    ids = {a: set(re.findall(r'\bid="([^"]+)"', (SAIDA / a).read_text(encoding="utf-8"))) for a, _, _ in PAGINAS}
    quebrados = []
    for a in ids:
        sem_codigo = re.sub(r"(?s)<pre.*?</pre>", "", (SAIDA / a).read_text(encoding="utf-8"))
        for alvo in re.findall(r'(?:href|src)="([^"]+)"', sem_codigo):
            if alvo.startswith(("http", "mailto:")) or "'" in alvo:
                continue
            destino, _, ancora = alvo.partition("#")
            destino = destino or a
            if not (SAIDA / destino).is_file() or (ancora and destino in ids and ancora not in ids[destino]):
                quebrados.append(f"{a} -> {alvo}")
    (AQUI / "trechos-gerados.txt").write_text("\n".join(sorted(set(TRECHOS))), encoding="utf-8")
    print(f"{len(PAGINAS)} páginas, {len(ler_perguntas())} perguntas, {len(set(TRECHOS))} trechos de código")
    if quebrados:
        raise SystemExit("links quebrados:\n" + "\n".join(quebrados))
    print("links internos: ok")


main()
