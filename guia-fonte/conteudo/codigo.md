# Código por funcionalidade | O caminho real de cada ação, do clique ao resultado na tela, com os arquivos e as linhas.

> **Como estudar:** para cada funcionalidade, decore o quadro (quem inicia, o que entra, onde grava, o que volta), depois abra o trecho e explique linha por linha em voz alta. Os links dos trechos abrem o GitHub na linha exata.

## mapa | Mapa do projeto | Quatro lugares onde o código roda.

| Onde roda | Arquivos | Responsabilidade |
| Navegador (tela) | `*.html`, `js/main.js`, `js/paginas/`, `js/componentes/` | capturar eventos e desenhar o DOM |
| Navegador (regras e rede) | `js/servicos/`, `js/modelos/`, `js/nucleo/` | chamar a API, manter o estado, gerar a sala |
| Web Worker | `js/nucleo/PyodideWorker.js` | executar o Python do jogador |
| Servidor Node.js | `backend/src/` | autenticar, autorizar, aplicar regras, gravar e avisar |

Não existe camada "repository": os arquivos de `backend/src/services/` contêm as regras **e** as chamadas ao driver do MongoDB. Também não há classes de model no back-end; o formato dos documentos é definido no código que os grava.

### O ponto de entrada de toda página

Cada HTML declara `data-pagina`. O único script de aplicação é `js/main.js`, que importa a classe correspondente sob demanda.

{{codigo|js/main.js|static async iniciar()}}

Toda página herda de `Pagina`: `iniciar()` chama `preparar()` (acesso) e depois `montar()` (tela). As protegidas redirecionam quem não pode estar ali.

{{codigo|js/servicos/ControleAcesso.js|async exigirAutenticacao}}

> ! Esse redirecionamento é **só experiência de uso**. Quem editar o JavaScript consegue abrir a página, mas a API continua recusando os dados. A proteção real é o middleware do servidor.

## cadastro | Cadastro e verificação de e-mail | Do formulário ao documento em `users`.

| Pergunta | Resposta |
| Quem inicia | `PaginaCadastro` no `submit` do formulário |
| Dados recebidos | `{ name, email, password, acceptTerms: true }` |
| Função no servidor | `cadastrar()` em `services/autenticacao.js` |
| Armazenamento | `users`, `authTokens`, `auditLogs` |
| Resposta | `201 { etapa, token, usuario, emailEnviado }` |
| Tela final | `verificar-email.html` |

1. O front valida nome, e-mail, senha e a **confirmação da senha** (comparação exata, diferencia maiúsculas) e exige a caixa de aceite.

{{codigo|js/paginas/PaginaCadastro.js|#validar(nome, email, senha, senha2) {}}

2. `ServicoAutenticacao.criarConta` envia o JSON. A confirmação (`senha2`) não é enviada: é uma conferência de digitação.
3. O servidor **valida tudo de novo**, gera o hash e grava. O e-mail duplicado é barrado pelo índice único, inclusive em cadastros simultâneos.

{{codigo|backend/src/services/autenticacao.js|export async function cadastrar}}

4. O link de verificação leva um token aleatório. No banco fica **só o SHA-256** dele, com validade.

{{codigo|backend/src/services/tokensUsoUnico.js|export async function criarToken}}

5. Ao abrir o link, `confirmarEmail` consome o token com `findOneAndDelete` (uso único e atômico) e marca `emailVerified: true`.

> O cadastro devolve um JWT antes da verificação, mas as rotas de jogo respondem `403 EMAIL_NAO_VERIFICADO` até o e-mail ser confirmado.

## login | Login, sessão e 2FA | Primeiro fator, segundo fator e o JWT.

{{codigo|backend/src/services/autenticacao.js|export async function entrar(ctx, corpo)}}

- Conta inexistente e senha errada devolvem a **mesma** mensagem `CREDENCIAIS_INVALIDAS`.
- Quando o e-mail não existe, o servidor ainda roda `bcrypt.compare` contra um hash fictício, para o tempo de resposta não denunciar quem tem cadastro (com a migração do Firebase ligada, esse caso consulta o Firebase em vez disso).
- Com 2FA ativo, o primeiro fator **não** entrega sessão: entrega um "desafio" de 5 minutos.

{{codigo|backend/src/services/autenticacao.js|export async function concluirPrimeiroFator}}

{{codigo|backend/src/services/sessao.js|export function emitirSessao}}

No navegador, `#resultado` guarda o token somente quando a etapa é `concluido`.

{{codigo|js/servicos/ServicoAutenticacao.js|#resultado(resposta) {}}

### O segundo fator (TOTP)

O app autenticador e o servidor compartilham um segredo. O código de 6 dígitos deriva do segredo e do relógio, em períodos de 30 s. O segredo fica cifrado com AES-256-GCM e o "passo" usado é gravado para o mesmo código não valer duas vezes.

{{codigo|backend/src/services/doisFatores.js|export async function conferirSegundoFator}}

### Login com Google

Fluxo Authorization Code com **PKCE**, `state` (guardado no banco e em cookie `httpOnly`) e `nonce`. O JWT nunca aparece na URL: o retorno leva um código de uso único de 2 minutos, trocado por `POST /api/auth/google/exchange`.

{{codigo|backend/src/services/google.js|async validarIdToken}}

## requisicao | Como o JavaScript fala com a API | Um único `fetch` para todas as chamadas REST.

{{codigo|js/nucleo/Api.js|static async requisitar}}

Leitura linha a linha:

- `async` faz a função devolver uma **Promise**; `await fetch(...)` suspende só esta função até a resposta chegar, sem travar a tela.
- `JSON.stringify` transforma o objeto em texto para viajar; `resposta.json()` faz o caminho inverso.
- `fetch` **só rejeita em falha de rede** (cai no `catch` e vira `SEM_CONEXAO`). Um 404 ou 500 resolve normalmente, por isso o teste de `resposta.ok`.
- `204` significa sucesso sem corpo.
- Em `401 TOKEN_INVALIDO` o token local é apagado.

O endereço da API muda sozinho conforme o domínio:

{{codigo|js/config.js|3-7}}

## grupos | Grupos e convites | Criar, entrar, convidar, sair e excluir.

### Criar

{{codigo|backend/src/services/grupos.js|export async function criarGrupo}}

- Nome de 3 a 30 caracteres; "demo" é reservado.
- O intervalo de 30 s é reservado com um `updateOne` condicional no próprio usuário: dois cliques simultâneos não passam.
- O criador vira `ownerId` e primeiro item de `members`.

### Entrar por link ou QR Code

{{codigo|backend/src/services/grupos.js|export async function adicionarMembro}}

O filtro é a regra: só adiciona se o usuário **ainda não** está no vetor, se a posição `members.3` não existe (máximo 4) e se o código confere. Como é uma operação atômica em um documento, duas pessoas não ocupam a última vaga.

### Quem pode o quê

{{codigo|backend/src/services/grupos.js|export async function grupoComoMembro}}

{{codigo|backend/src/services/grupos.js|export async function grupoComoDono}}

> Essas duas funções são a **autorização por grupo**. Não são middlewares do Express: são chamadas dentro dos services. Grupo, chat e partida passam por elas.

### Convite por username

O `_id` do convite é `idDoGrupo_idDoConvidado`, então não existem dois convites pendentes iguais. Aceitar primeiro "reserva" o convite (`status: "pending"` → `accepted`) e depois tenta ocupar a vaga; se o grupo encheu, o status volta para pendente.

{{codigo|backend/src/services/convites.js|export async function responderConvite}}

### Grupo DEMO

Administradores compartilham um grupo especial chamado DEMO, criado na primeira listagem. Nele, qualquer admin age como dono e a partida usa a configuração fixa de `js/modelos/ConfigDemo.js`. É o melhor recurso para a **demonstração ao vivo**.

## ciclo | Ciclo completo da partida | Lobby, início, exploração, enigmas e fim.

| Estado | Como se chega | Quem pode |
| (sem documento) | grupo sem partida | — |
| `WAITING` | `POST /api/games/:gid` | dono |
| `PLAYING` | `POST .../start` | dono |
| `COMPLETED` | resolver o enigma final | jogador da partida |
| `FAILED` | `POST .../end` com `FAILED` | dono |
| `EXPIRED` | `POST .../end` com `EXPIRED` após o prazo | qualquer membro |

### 1. Gerar a sala (no navegador do dono)

{{codigo|js/servicos/Partida.js|async criar(dificuldade)}}

A semente é aleatória, mas a partir dela tudo é **determinístico**: o gerador escolhe objetos, modelos de enigma e dependências, e simula um jogador para garantir que a sala é solucionável.

{{codigo|js/nucleo/GeradorProcedural.js|static gerar(}}

{{codigo|js/nucleo/GeradorProcedural.js|static #simular}}

### 2. O servidor confere o formato e grava

{{codigo|backend/src/services/partidas.js|export async function criarPartida}}

`validarConfig` confere quantidade de enigmas, chaves, referências cruzadas e um único enigma final.

> ! Limite: o servidor valida a **estrutura**, mas não confere se o `modeloId` existe nem se a sala é solucionável. A geração é confiada ao cliente do dono.

### 3. Entrar e iniciar

{{codigo|backend/src/services/partidas.js|export async function entrarNaPartida}}

{{codigo|backend/src/services/partidas.js|export async function iniciarPartida}}

O grupo aceita 4 integrantes; a partida, **3 jogadores**. O quarto assiste.

### 4. Cronômetro

O servidor grava `startedAt` e `expiresAt`. O cliente mede a diferença entre os relógios (descontando metade do tempo da requisição) e só **exibe** a contagem.

{{codigo|js/servicos/ServicoPartida.js|async deslocamentoMs()}}

{{codigo|js/nucleo/Cronometro.js|restanteMs() {}}

Quando zera no navegador, `#expirar` pede `EXPIRED`; o servidor aceita só se o prazo realmente venceu (tolerância de 2 s).

> ! Não há tarefa agendada no servidor. Se ninguém estiver com a sala aberta quando o prazo vence, o documento continua `PLAYING` até alguém abrir a sala. As estatísticas e o histórico tratam esse caso como expirado.

### 5. Pistas

Clicar em um objeto chama `Partida.interagir`. Se o objeto guarda pista, ela é registrada no servidor.

{{codigo|js/servicos/Partida.js|async interagir(hotspot)}}

{{codigo|backend/src/services/partidas.js|export async function registrarPista}}

### 6. Enigmas e conclusão

{{codigo|js/servicos/Partida.js|async validar(chave, codigo, codigoDigitado)}}

{{codigo|backend/src/services/partidas.js|export async function registrarEnigma}}

> ! **A limitação mais importante do projeto:** o servidor confere participação, prazo, pistas e dependências, mas **não confere se o Python foi executado nem se a resposta está certa**. Quem chamar a API diretamente conclui a partida sem programar. Veja a prova em [Segurança](seguranca.html#provas).

### 7. Pontuação

{{codigo|backend/src/services/pontuacao.js|export function calcularPontuacao}}

Fórmula: `200 × enigmas + piso(segundos restantes × bônus) − 40 × dicas − 10 × tentativas`, limitada entre 0 e 5000. Bônus por segundo: fácil 0,15; médio 0,10; difícil 0,08. O front calcula a mesma fórmula, mas o campo `score` enviado é **ignorado**. Os números são decisão de projeto: não há no repositório estudo que os fundamente, então apresentem como escolha da equipe.

## simultaneo | Sincronização e ações simultâneas | O que acontece quando dois jogadores agem juntos.

| Informação | Quem controla | Observação |
| Conta, papel, sessão | servidor | lidos do banco a cada requisição |
| Membros, dono, vagas | servidor | filtros atômicos |
| Status, início e fim da partida | servidor | relógio do servidor |
| Pistas achadas e enigmas resolvidos | servidor grava, **cliente afirma** | confere pré-condições, não o conteúdo |
| Correção do Python | **cliente** | Pyodide no navegador |
| Dicas e tentativas | **cliente** | contador em memória; recarregar a página zera |
| Pontuação | servidor calcula | com dicas e tentativas informadas pelo cliente |
| Geração da sala | **cliente do dono** | servidor valida o formato |
| Rascunho de código, posição na sala | cliente | não é compartilhado |

O controle de concorrência é **o filtro do `updateOne`**. O MongoDB aplica a condição e a escrita de forma atômica em um documento.

| Corrida | Condição no filtro | Quem perde recebe |
| duas pessoas na 3ª vaga | `players.2` não existe | `409 PARTIDA_FECHADA` |
| dois cliques em iniciar | `status: "WAITING"` | `409 PARTIDA_JA_INICIADA` |
| mesma pista | `found.objeto` não existe | sucesso silencioso (idempotente) |
| mesmo enigma | `solved.chave` não existe | `409 ENIGMA_JA_RESOLVIDO`, ignorado pelo front |
| progresso após o prazo | `expiresAt > agora` | `409` |

Depois de gravar, o servidor avisa o grupo e cada cliente **busca o estado de novo**. Não há mesclagem no navegador: a verdade é o documento no banco.

{{codigo|js/nucleo/TempoReal.js|observar(canais, carregar}}

Essa função é um bom exemplo de **closure**: `ativo` e `versao` ficam presos a cada assinatura. Se duas respostas chegarem fora de ordem, só a mais nova é aplicada.

## chat | Chat do grupo | Envio por HTTP, aviso por SSE, leitura por HTTP.

**Tecnologia real: Server-Sent Events + REST.** Não há WebSocket nem Socket.IO.

### 1. Capturar o evento

{{codigo|js/componentes/PainelChat.js|async #enviar(ev)}}

`preventDefault()` impede o recarregamento da página. O chat existe em duas telas: `PaginaGrupo` e a sala (`PainelChat`), ambas usando `ServicoChat`.

### 2. Servidor: autorizar, limitar, gravar, avisar

{{codigo|backend/src/services/chat.js|export async function enviarMensagem}}

- O autor vem de `req.usuario` (token), nunca do corpo: não dá para falar em nome de outro.
- Limites: 300 caracteres, 2 s entre mensagens, 15 por minuto.
- Persistência: coleção `messages`, com `expiresAt` de 24 h (índice TTL).

> ! Os dois limites fazem "consultar e depois inserir". Em teste, **8 mensagens disparadas ao mesmo tempo foram todas aceitas** (`201`). O limite vale para uso normal, não contra um script.

### 3. Aviso em tempo real

{{codigo|backend/src/services/tempoReal.js|abrir(uid, resposta)}}

{{codigo|backend/src/services/tempoReal.js|notificar(uids, canal)}}

O Map liga **id do usuário → conjunto de conexões abertas** (várias abas). Não existe "sala" de rede: o destino é calculado na hora a partir de `grupo.members`. A mensagem enviada é só `{"canal":"chat:<id>"}`, sem o texto.

### 4. Cliente: ler o fluxo e recarregar

{{codigo|js/nucleo/TempoReal.js|async #abrir()}}

{{codigo|js/nucleo/TempoReal.js|#processar(bloco)}}

{{codigo|js/componentes/Chat.js|renderizar(mensagens, uid, agora)}}

`textContent` insere o texto como texto: `<img onerror=...>` aparece escrito, não executa.

### Presença, saída e reconexão

- Online = ter ao menos uma conexão SSE aberta. Ao abrir a primeira ou fechar a última, os colegas recebem `presenca:<uid>`.
- Queda: nova tentativa em 1 s, 2 s, 4 s… até 30 s. Ao reconectar, **todas** as assinaturas recarregam, porque avisos podem ter se perdido.
- Ping a cada 25 s para proxies não derrubarem a conexão.
- Quem é removido do grupo deixa de ser avisado e recebe `403` ao tentar ler ou enviar.

## python | Execução do Python com Pyodide e Web Worker | Como o código digitado vira resultado.

**Pyodide** é o interpretador CPython compilado para WebAssembly; aqui é a versão 0.26.4, baixada do CDN jsDelivr. Rodar no navegador evita instalar Python e evita executar código de estranhos no servidor.

### 1. Do editor ao Worker

`PainelEnigma` chama `Partida.validar`, que chama `GerenciadorEnigmas`. Nos enigmas fáceis (`semDef`) o jogador escreve só o corpo, e o JavaScript monta a função:

{{codigo|js/servicos/GerenciadorEnigmas.js|static #embrulhar}}

{{codigo|js/servicos/GerenciadorEnigmas.js|async validar(enigma}}

### 2. Mensagens entre threads, com limite de tempo

{{codigo|js/nucleo/ExecutorPython.js|async executar(}}

`postMessage` envia uma **cópia** dos dados. O `id` casa resposta com pedido. Em 6 s sem resposta, o Worker é destruído com `terminate()`: é a única forma de parar um `while True`. A carga inicial tem limite próprio de 90 s.

### 3. Dentro do Worker

{{codigo|js/nucleo/PyodideWorker.js|self.onmessage}}

O programa Python `HARNESS` faz, nesta ordem: `ast.parse` e `compile` (pega erro de sintaxe), `exec` em um dicionário novo (pega erro de execução), procura a função, roda cada teste comparando **tipo e valor**, e por fim calcula o "código do mecanismo" com a entrada da pista.

{{codigo|js/nucleo/PyodideWorker.js|44-58}}

{{codigo|js/nucleo/PyodideWorker.js|67-99}}

### 4. De onde vêm os testes

{{codigo|js/modelos/Enigma.js|constructor({ chave, modelo}}

Cada modelo em `js/modelos/ModelosEnigma.js` tem uma função de referência `f` em JavaScript. A semente sorteia parâmetros e entradas; o resultado esperado é calculado **no próprio navegador**. São 6 casos por enigma e os 3 primeiros são visíveis no feedback.

### 5. Retorno real do avaliador

Saídas obtidas executando o `HARNESS` em CPython, com dois testes de exemplo:

```resultado em JSON
código correto  -> {"fase":"ok","codigo":"137","aprovados":2,"total":2}
valor errado    -> {"fase":"teste","falhas":[{"args":"10","esperado":"67","obtido":"70","tipo":"valor"}, ...]}
faltou ":"      -> {"fase":"sintaxe","mensagem":"expected ':'","linha":1}
divisão por 0   -> {"fase":"teste","falhas":[{"tipo":"erro","obtido":"ZeroDivisionError: division by zero","linha":2}, ...]}
```

{{codigo|js/modelos/TentativaEnigma.js|static conferirCodigo}}

### Navegador × servidor

| | No navegador (o que fazemos) | No servidor |
| Quem sofre com código malicioso ou pesado | a aba do próprio jogador | todos os usuários |
| Custo de infraestrutura | nenhum | processos e isolamento por execução |
| Resultado é confiável? | **não**: o dono do navegador pode forjar | sim, se bem isolado |

> ! O Worker **não é uma sandbox de segurança completa**. Pelo funcionamento do Pyodide, o Python alcança APIs do Worker pelo módulo `js` (inclusive rede). Ele não alcança o DOM nem o `localStorage`, onde está o token. Como cada pessoa executa só o próprio código, o risco principal é contra o próprio resultado.

## progresso | Resultado, histórico e estatísticas | O que sobra depois que a partida acaba.

{{codigo|backend/src/services/historico.js|export async function arquivarPartida(ctx, partida)}}

{{codigo|backend/src/services/estatisticas.js|export async function estatisticasDoJogador}}

O dashboard pede `GET /api/users/me/stats` e desenha os gráficos com Chart.js. Não existe uma tela que liste partida por partida: o histórico alimenta as **estatísticas**. Detalhes das coleções em [API e banco](api-banco.html#colecoes).

## admin | Editor de salas e auditoria | Recursos restritos a administradores.

O papel `role: "admin"` é definido manualmente no Atlas. `editor-sala.html` edita hotspots (áreas clicáveis em coordenadas de 0 a 1) e salva por `PUT /api/rooms/:id`; a pré-visualização usa `ServicoPartidaLocal`, uma partida em memória. Sem sala publicada no banco, o jogo usa `assets/salas/sala-gotica.json`.

{{codigo|backend/src/services/salas.js|export async function obterSala}}

`auditoria.html` lista os logs por `GET /api/audit`. O front esconde a tela de quem não é admin, e o servidor recusa com `403 SOMENTE_ADMIN`.
