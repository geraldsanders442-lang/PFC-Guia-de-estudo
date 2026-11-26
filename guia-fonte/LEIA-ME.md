# Fonte do guia de estudos

- `../guia-estudos/` é o site pronto. Abra `index.html`.
- `conteudo/` tem o texto das páginas e as perguntas. `base/` tem o guia anterior e os ajustes aplicados a ele.
- Os trechos de código são lidos do repositório do Escape.py (usado: branch main, commit 37cd1d6).

## Gerar de novo

```powershell
git clone https://github.com/pfcumc2026/Escape-Room-PFC "$env:TEMP\escape-ref"
```

```powershell
python build.py "$env:TEMP\escape-ref"
```

O build para se um arquivo ou padrão de código não existir, ou se houver link interno quebrado. Trechos indicados por número de linha precisam ser revistos (lista em `trechos-gerados.txt`) quando o código mudar, assim como os textos.

## Publicar no GitHub Pages

Envie **todo o conteúdo** de `guia-estudos/` (as 8 páginas, a pasta `assets/` e o `.nojekyll`) para a raiz do repositório do guia, `geraldsanders442-lang/PFC-Guia-de-estudo`. Nada disto vai para o repositório do Escape.py.

Antes de publicar: o guia descreve falhas reais e como reproduzi-las. Com o site público, qualquer pessoa pode lê-las.
