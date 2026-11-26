# Segurança, LGPD e limitações | Pense como alguém tentando quebrar o sistema: o que protege, onde está, como provar e o que ainda falta.

## mecanismos | Mecanismos implementados | Ameaça, funcionamento, prova e limite.

| Mecanismo | Ameaça | Onde | Como demonstrar | Limite |
| bcrypt custo 12 | vazamento do banco revelar senhas | `autenticacao.js` `gerarHash` | abrir `users` e ver `$2b$12$` | senha fraca ainda pode ser adivinhada |
| Regras de senha (8 a 72 bytes, letra e número) | senha trivial | `validacao.js` `validarSenha` | tentar `abc123` | não consulta senhas vazadas |
| Mensagem genérica e hash fictício | descobrir e-mails cadastrados no login | `autenticacao.js` `entrar` | errar senha e usar e-mail inexistente | o **cadastro** informa `EMAIL_EM_USO` |
| JWT HS256 com emissor e público | token forjado | `sessao.js` | alterar um caractere do token | roubado, vale até expirar (8 h) |
| `sessionVersion` | sessões antigas após redefinir senha | `middleware/autenticacao.js` | redefinir e reusar o token antigo | logout e mudança de 2FA não revogam |
| 2FA TOTP cifrado | senha vazada | `doisFatores.js`, `segredos.js` | ativar e logar | opcional |
| Token de uso único com hash e TTL | reutilizar link de e-mail | `tokensUsoUnico.js` | abrir o link duas vezes | depende da caixa de e-mail |
| Autorização por papel e por grupo | acessar dados alheios | middlewares e `grupos.js` | outro usuário recebe `403` | perfil público e presença visíveis a qualquer usuário verificado |
| Lista de campos editáveis | virar admin pelo corpo | `contas.js` | `PATCH` com `role` | — |
| Validação de tipos | NoSQL Injection | `validacao.js` | enviar `{"$ne":null}` | validação manual, campo a campo |
| Chaves com formato rígido | injetar caminho em `$set` | `partidas.js` `ID_CHAVE` | objeto com ponto no nome | — |
| `textContent` | XSS | `Chat.js`, painéis | mandar `<img onerror>` | sem CSP como segunda barreira |
| CORS restrito | site de terceiros ler a API no navegador | `app.js` | `Origin` estranho → `403` | não protege contra scripts fora do navegador |
| Rate limit | força bruta | `limites.js` | 21ª tentativa → `429` | em memória e por IP |
| Limite do chat e de grupos | spam | `chat.js`, `grupos.js` | mensagem imediata → `429` | chat furado por envios simultâneos |
| Relógio e estado no servidor | ganhar tempo, pular etapa | `partidas.js` | resolver antes da pista → `409` | não valida a resposta |
| Variáveis de ambiente | segredo no repositório | `ambiente.js`, `.gitignore`, `render.yaml` | abrir `.env.example` | depende de disciplina local |
| Erro 500 genérico | vazar detalhes internos | `middleware/erros.js` | teste unitário local | o log do servidor guarda o erro inteiro |
| Auditoria | não saber quem fez | `auditoria.js` | `auditoria.html` como admin | falha de log não bloqueia a ação |

### CSRF

A API autentica pelo cabeçalho `Authorization`, que o navegador **não** envia sozinho. Por isso um formulário em outro site não age em nome do usuário. O único cookie é o `state` do login com Google (`httpOnly`, `sameSite=lax`, 10 minutos).

### Onde fica o token e o risco

`localStorage`, chave `escape-sessao`. Front e API ficam em domínios diferentes e muitos navegadores bloqueiam cookies de terceiros. O custo: um XSS conseguiria ler o token. Mitigações atuais: `textContent` para dados de usuários e validade curta.

### Segredos

`server.js` recusa iniciar sem `MONGODB_URI`, `MONGODB_DB_NAME`, `JWT_SECRET` (32+), `FRONTEND_URL` e `TOTP_ENCRYPTION_KEY` (32 bytes). No histórico do Git só encontramos a string de exemplo (`mongodb+srv` com valores fictícios) e nenhum arquivo `.env` versionado. Atenção: a chave **pública** do Firebase antigo aparece no front legado; chaves web do Firebase não são segredo, mas o projeto antigo deve ter regras revisadas.

{{codigo|backend/src/config/ambiente.js|export function lerAmbiente}}

{{codigo|backend/src/utils/segredos.js|12-25}}

## provas | Vulnerabilidades comprovadas | Resultados obtidos em 26/11/2026 contra a API do commit documentado, com banco em memória.

> ! Digam isso **antes** de a banca descobrir, junto com a correção planejada. Não demonstrem contra o servidor de produção.

| # | Gravidade | O que acontece | Resultado observado | Correção recomendada |
| 1 | Alta | Concluir a partida sem executar Python: só `POST clues` e `POST puzzles` | partida `COMPLETED`, 824 pontos | servidor avaliar a resposta (ex.: conferir o código do mecanismo recalculado por modelo e semente) |
| 2 | Alta | Dicas e tentativas são informadas pelo cliente e ficam só na memória | enviar `0` é aceito; recarregar zera | contar dicas e tentativas no servidor |
| 3 | Média | Logout não invalida o JWT | `GET /users/me` com o mesmo token → `200` | incrementar `sessionVersion` no logout ou lista de revogação |
| 4 | Média | Limite do chat com condição de corrida | 8 envios simultâneos → 8 × `201` | contador atômico por usuário |
| 5 | Média (LGPD) | Exclusão de conta deixa dados | `uid` permanece em `games`; 8 mensagens continuam até o TTL; 7 logs com e-mail | limpar `games` e `messages`; anonimizar logs |
| 6 | Média | Limite de autenticação por IP e compartilhado | após 20 logins errados, "esqueci a senha" também dá `429` | combinar IP + conta; limitadores separados |
| 7 | Baixa | `difficulty: ["facil"]` é aceito | `201` com lista gravada | exigir `typeof === "string"` |

O item 6 afeta a banca: numa rede de universidade, **todos saem pelo mesmo IP**. Não fiquem errando senha ao vivo antes de fazer o login principal.

### Como reproduzir o item 1

```sequência (dono do grupo, partida DEMO ou comum já iniciada)
POST /api/games/{gid}/clues/{objetoDaPista}        -> 204
POST /api/games/{gid}/puzzles/p1  {"hints":0,"attempts":0}  -> 204
... demais pistas e enigmas ...
POST /api/games/{gid}/puzzles/pf  {"hints":0,"attempts":0}  -> 204, status COMPLETED
```

Os nomes das pistas vêm em `config` na resposta de `GET /api/games/{gid}`.

## outros | Outros riscos identificados na leitura do código | Não foram explorados na prática.

- **Dependências de CDN sem integridade:** `lucide@latest` e `qrcodejs@master` sem versão fixa; nenhum `integrity`; sem Content-Security-Policy. Uma biblioteca comprometida leria o token.
- **Pyodide não é sandbox:** o Python do Worker pode usar a rede do navegador. Não há isolamento além do próprio navegador.
- **Respostas no cliente:** a configuração e os modelos permitem calcular o código esperado no console.
- **Geração da sala no cliente do dono:** o servidor não confere se é solucionável.
- **SSE:** o token é conferido só na abertura; a conexão segue aberta após expirar (só recebe nomes de canais).
- **Callback do Google** sem limitador.
- **Operações em várias coleções sem transação:** exclusão de conta, de grupo e arquivamento.
- **Sem backup, monitoramento ou alerta** descritos no repositório.
- **Administrador vê e-mail e ações de todos** nos logs; o papel é concedido manualmente no banco.

## lgpd | Dados pessoais e LGPD | O que é coletado, onde fica, para quê e por quanto tempo.

> ! Este guia descreve medidas **técnicas** encontradas no código. Não afirma conformidade com a LGPD; isso depende de avaliação jurídica e organizacional.

| Dado | Onde | Finalidade | Quem vê | Fim do ciclo |
| nome, e-mail | `users` | conta e e-mails | o próprio; admin vê o e-mail nos logs | apagado na exclusão |
| hash da senha | `users` | autenticação | ninguém pela API | idem |
| segredo TOTP cifrado, hash dos códigos | `users` | 2FA | ninguém pela API | idem ou ao desativar |
| `googleSub`, `firebaseUid` | `users` | vínculo de conta | — | idem (conta no Firebase **permanece**) |
| username, avatar | `users` | identificação no jogo | usuários verificados | idem; copiado em mensagens e convites |
| aceite: versão e data | `users` e `auditLogs` | comprovação | admin | o log permanece |
| mensagens | `messages` | colaboração | membros do grupo | 24 h |
| partidas | `games`, `gameHistory` | jogo e estatísticas | membros; o próprio | sai do histórico; fica em `games` |
| ações com e-mail e uid | `auditLogs` | segurança | admin | política diz 6 meses; **não há rotina de exclusão** |
| IP | memória do limitador e provedores | proteção | provedores | volátil na API |
| tema e token | navegador | funcionamento | o próprio | logout apaga o token |

### Comprovação do aceite (a pergunta que derrubou um grupo no simpósio)

Temos o campo no banco, com **versão, data e hora do servidor**, e o registro `termos_aceitos` na auditoria.

{{codigo|backend/src/services/autenticacao.js|44-56}}

```consulta no MongoDB Atlas ou Compass
db.users.findOne({ email: "..." }, { termsVersion: 1, termsAcceptedAt: 1 })
db.auditLogs.find({ action: "termos_aceitos" }).sort({ at: -1 }).limit(1)
```

Lacunas verificadas:

- **Contas migradas do Firebase** são criadas sem `termsVersion` nem `termsAcceptedAt`.
- **Conta criada pelo botão Google na tela de login** grava o aceite com base no texto "Ao continuar, você concorda", sem caixa de marcação. Na tela de cadastro a caixa é exigida pelo front.
- Mudou o termo? Não há fluxo para pedir novo aceite.
- A idade não é perguntada; a política apenas orienta sobre menores.

### Direitos do titular

| Direito | Situação |
| Acesso | parcial: Configurações mostra os dados principais; não há exportação |
| Correção | username, avatar e nome pela API; senha pelo link de e-mail |
| Exclusão | implementada, com os restos citados no item 5 |
| Contato | e-mail publicado nos termos e na política |

### Textos que precisam de revisão

- `termos.html` e `index.html` ainda dizem que **as salas estão em desenvolvimento**.
- A política promete excluir logs após 6 meses: alguém precisa fazer isso (ou criar um índice TTL em `auditLogs.at`).
- A política diz que a exclusão remove a participação nos grupos; convém mencionar mensagens, logs e Firebase.

## respostas | Respostas curtas para as perguntas obrigatórias | Treinem até sair natural; as versões completas estão no [simulado](simulado.html).

| Pergunta | Resposta |
| Como protegem os dados? | HTTPS, senha em bcrypt, sessão assinada, autorização no servidor, 2FA cifrado, chat expira em 24 h. |
| Um usuário acessa outro grupo? | Não pela API: toda operação confere se o id do token está em `members`; teste devolve 403. |
| O que impede manipular a pontuação? | O valor é calculado no servidor; mas dicas, tentativas e a própria resolução vêm do cliente. Hoje dá para trapacear. |
| NoSQL Injection? | Todo campo usado em consulta passa por checagem de tipo; objeto no lugar de texto vira 400. |
| Rota sem autenticação? | 401 `TOKEN_AUSENTE`, antes de chegar ao controller. |
| Rate limiting? | 20 por 15 min nas rotas de autenticação e 600 por 5 min no geral, por IP, em memória. |
| Credenciais? | Variáveis de ambiente; `.env` ignorado; no Render são cadastradas no painel. |
| Dados pessoais? | Coleta mínima, finalidade descrita na política, exclusão de conta; com lacunas conhecidas. |
| Código malicioso? | Roda no navegador de quem escreveu, com limite de 6 s; não chega ao servidor. |
| Pyodide é risco? | Para o servidor, não executa nada lá. No navegador, não alcança o DOM nem o token, mas alcança a rede. |

## melhorias | Limitações e melhorias recomendadas | Em ordem de prioridade. Nada disto foi alterado no Escape.py.

| Prioridade | Melhoria | Esforço estimado |
| 1 | Validar a resolução e contar dicas/tentativas no servidor | médio |
| 2 | Trazer os 64 testes unitários para o GitHub (passam no código atual) | baixo |
| 3 | Completar a exclusão de conta e criar a retenção dos logs | baixo |
| 4 | Revisar termos, landing, BPMN, diagramas de classe e README (104 → 109 testes) | baixo |
| 5 | Remover o código Firebase não utilizado | baixo |
| 6 | Revogar sessão no logout; limite de chat atômico; checar tipo de `difficulty` | baixo |
| 7 | Fixar versões de CDN, `integrity` e CSP | médio |
| 8 | Botão "mostrar senha" no cadastro | baixo |
| 9 | Testes de interface, de carga e integração contínua | médio |
| 10 | Transações e canal compartilhado (ex.: Redis) para várias instâncias | alto |

### Código antigo ainda no repositório

Nenhuma página carrega estes arquivos (todas usam só `js/main.js`): `js/cadastro.js`, `configuracoes.js`, `dashboard.js`, `entrar.js`, `esqueci-senha.js`, `firebase.js`, `grupo.js`, `guard.js`, `login.js`, `perfil.js`, `presenca.js`, `ui.js`, `verificar-email.js` e `js/nucleo/Firebase.js`; além de `firestore.rules`, `firestore.indexes.json` e `database.rules.json`, que o README mantém porque o projeto Firebase segue ativo. No simpósio, código sem uso foi criticado.

> ! **Fora do GitHub, no computador:** na cópia local antiga (`placeholder`), o arquivo `backend/.env` **não está coberto pelo `.gitignore`**. Não executem `git add .` ali; o conteúdo desse arquivo não foi aberto na preparação deste guia.
