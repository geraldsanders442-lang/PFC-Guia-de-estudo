# Testes e demonstração | O que existe de verdade, como executar, como ler o resultado e o roteiro ao vivo.

## situacao | Situação real | Números obtidos executando os comandos em 26/11/2026.

| Conjunto | Onde está | Resultado |
| Integração da API | `backend/test/` no GitHub (main) | **109 testes, 109 aprovados**, cerca de 93 s |
| Unitários | `versao-1-etapa1/backend/test/unidade/` (**só na máquina local**) | 64 aprovados em 1,3 s também contra o código atual |
| Interface / ponta a ponta | não existe | testes manuais |
| Carga | não existe | — |
| Integração contínua | não há pasta `.github` | execução manual |

> ! No simpósio um professor afirmou que testes unitários são obrigatórios. Hoje a branch `main` **não** tem a pasta `test/unidade` nem o script `test:unidade`. Decidam antes da banca se vão incorporar os arquivos. Até lá, não digam que "estão no repositório".

> O README informa 104 testes; a execução atual conta 109. Falem o número que o terminal mostrar.

## config | Framework e configuração | Nada além do Node.js e um MongoDB temporário.

- Executor: `node:test`. Asserções: `node:assert/strict`.
- Banco: `mongodb-memory-server` (MongoDB real, temporário). Na primeira vez baixa o binário.
- Script: `node --test --test-concurrency=1 test/` (um arquivo por vez).
- E-mail: objeto falso que guarda as mensagens. Google e Firebase: dublês passados no `ctx`.
- Não é preciso `.env` nem Atlas.

{{codigo|backend/test/ajuda.js|export async function criarAmbiente}}

### Anatomia de um teste real

{{codigo|backend/test/historico.test.js|test("o score enviado pelo cliente é ignorado}}

**Preparar** (grupo e partida), **agir** (resolver enviando `score: 5000`), **verificar** (o gravado é o valor calculado) e testar a **falha** (repetir dá 409; valor fora da faixa dá 400).

## comandos | Roteiro de execução | Em um terminal, dentro de `backend/` do repositório atual.

```powershell
npm install
```

```powershell
npm test
```

| Comando | Testes | O que verifica | Requisito |
| `node --test test/autenticacao.test.js` | 36 | saúde, CORS, cadastro, e-mail, login, perfil, senha, 2FA, limite, auditoria | contas e segurança |
| `node --test test/jogo.test.js` | 23 | grupos, convites, chat, partida, salas, SSE, exclusão de conta | jogo colaborativo |
| `node --test test/historico.test.js` | 20 | sessão, transições, pontuação, histórico, índices, estatísticas | persistência e regras |
| `node --test test/legado.test.js` | 13 | migração do Firebase, 2FA antigo | continuidade de contas |
| `node --test test/google.test.js` | 12 | `id_token`, PKCE, vínculo de contas | login Google |
| `node --test test/demo.test.js` | 5 | grupo DEMO e acesso de admin | controle de acesso |

Para mostrar um grupo específico:

```powershell
node --test --test-name-pattern="CORS" test/autenticacao.test.js
```

### Como ler o resultado

- `✔` passou; `✖` falhou. No fim: `tests`, `pass`, `fail`.
- Em uma falha, leia o nome do teste, o `actual` × `expected` e a linha do arquivo indicada.
- Falha antes de qualquer teste costuma ser o download do MongoDB (sem internet) ou Node antigo (`>=20.19`).
- A mensagem `[firebase-legado] INTERNAL` aparece de propósito: um teste simula a falha do serviço.

| Se falhar | Provável significado |
| `autenticacao` | quebrou cadastro, sessão, 2FA ou permissão |
| `jogo` ou `historico` | regra de partida, histórico ou isolamento |
| `google` / `legado` | validação de identidade externa |

## cobertura | O que é testado e o que não é | Para não prometer demais.

**Coberto:** respostas com status e código de erro, efeitos no banco, injeção de operador no cadastro, concorrência no cadastro, score ignorado, isolamento entre grupos, SSE.

**Não coberto:** interface, Pyodide e Worker, gerador procedural (só pelos unitários locais, em parte), `TempoReal.js` do cliente, limite do chat sob concorrência, falsificação de progresso, envio real de e-mail, Atlas, deploy, acessibilidade e responsividade.

### Testes recomendados (ainda não implementados)

1. Resolver enigma sem resposta correta deve ser recusado (hoje **falharia**).
2. Rajada de mensagens respeita o limite (hoje **falharia**).
3. Token após logout é recusado (hoje **falharia**).
4. Exclusão de conta não deixa o `uid` em `games` (hoje **falharia**).
5. Todo modelo de enigma: a solução de referência passa nos próprios testes.
6. `GeradorProcedural` produz sala válida para muitas sementes.
7. Fluxo no navegador com duas sessões (Playwright, por exemplo).

## unitarios | Fundamentos e testes unitários locais | Conceitos que a banca pode pedir, com exemplos da pasta local.

| Tipo | O que verifica |
| Unitário | uma função isolada, dependências substituídas |
| Integração | rotas + services + banco juntos |
| Ponta a ponta | o sistema pela interface |
| Regressão | o que funcionava continua funcionando |

| Arquivo local em `test/unidade/` | Unidade |
| `validacao.test.js` | `utils/validacao.js` |
| `erros.test.js` | erros HTTP e `tratarErros` |
| `autenticacao.test.js` | middlewares |
| `tokensUsoUnico.test.js` | tokens e hash |
| `salas.test.js` | `services/salas.js` com banco falso (`mock.fn`) |
| `jogo.test.js` | pontuação, dificuldade, cronômetro (`mock.timers`), semente |

```javascript
// padrão AAA: preparar, agir, verificar
test("negativo: senha curta", () => {
  assert.throws(() => validarSenha("a1"), { codigo: "SENHA_FRACA" });
});
```

Equivalências para quem estudou JUnit: `@Test` → `test()`; classe de teste → `describe()`; Mockito → `mock.fn()`; H2 → `mongodb-memory-server`; MockMvc → `fetch` na porta local. **Dublê** substitui uma dependência; no unitário ele permite conferir com que filtro o banco foi consultado.

## manual | Roteiro de demonstração ao vivo | Preparem antes: duas contas verificadas, uma conta admin e dois navegadores (normal e anônimo).

> Antes de tudo: abram `https://escape-py-api.onrender.com/api/health` alguns minutos antes (o plano gratuito hiberna) e confirmem o endereço real em `js/config.js`. Este guia não verificou o ambiente publicado.

| Cenário | Passos | Esperado | Prova |
| Login inválido | senha errada | "E-mail ou senha incorretos." | aba Rede: 401 `CREDENCIAIS_INVALIDAS` |
| Aceite dos termos | cadastrar; abrir o Atlas | campos `termsVersion` e `termsAcceptedAt` | documento em `users` e `auditLogs` |
| Senha protegida | abrir o documento | `$2b$12$...` | Atlas |
| Confirmação de senha | digitar com maiúscula diferente | "As senhas não coincidem." | tela |
| Rota protegida | abrir `.../api/groups` direto no navegador | 401 `TOKEN_AUSENTE` | resposta JSON |
| Área de admin | jogador abre `auditoria.html` | volta ao dashboard; API 403 | Rede |
| Outro grupo | usuário B pede `/api/groups/<id de A>` | 403 `NAO_MEMBRO` | console |
| Chat | A envia; B vê sem recarregar | mensagem aparece | Rede de B: `events` e novo `GET messages` |
| XSS | enviar `<img src=x onerror=alert(1)>` | texto literal | tela |
| Entrada e saída | B fecha a aba | A vê B offline | tela do grupo |
| Partida | dono cria, B entra, dono inicia | os dois mudam de tela | duas janelas |
| Python | código errado, laço infinito, código certo | feedback, "demorou demais", mecanismo abre | tela |
| Sincronização | B registra uma pista | caderno de A atualiza | duas janelas |
| Fim | resolver o final (grupo DEMO é o caminho curto) | painel de resultado | tela |
| Histórico | abrir dashboard e `gameHistory` | números atualizados | Atlas |

### Chamada pronta para o console (usuário B)

```javascript
await fetch("<URL_DA_API>/groups/<ID_DO_GRUPO_DE_A>", {
  headers: { Authorization: "Bearer " + localStorage.getItem("escape-sessao") }
}).then(r => r.json())
```

### Plano B

- Sem internet: rodar API e front localmente exige o Atlas; o **`npm test` funciona offline** depois do primeiro download.
- E-mail atrasado: usem contas já verificadas.
- Evitem errar senha várias vezes: o limite é por IP.
- Ensaiem com cronômetro: no simpósio houve desconto por apresentação abaixo do tempo mínimo.
