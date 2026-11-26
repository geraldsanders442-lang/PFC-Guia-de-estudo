# O que a banca cobrou no simpósio | Análise da transcrição automática "Apresentação de PFCs (matutino)" e o que ela significa para o Escape.py.

> ! A transcrição é automática, mistura as vozes (todas aparecem como `@1`) e tem muitos trechos truncados. As frases abaixo são **paráfrases interpretadas**. Os três projetos apresentados são de outras pessoas: nada deles é atribuído ao Escape.py. Antes de citar um momento, ouçam o vídeo.

## momentos | Momentos que merecem atenção | O que ocorreu, o que foi exigido e onde estamos.

| Tempo | O que aconteceu | Nível exigido | Escape.py hoje | Treinar |
| 22:06–23:11 | origem dos preços não aparecia; texto confuso na exclusão | coerência com o objetivo e o público | explicar o público (estudantes) e de onde vêm os enigmas | [decisão](simulado.html#q-dec-escape) |
| 23:37–24:00 | "ao criar a conta, como ficam política de privacidade e termos?" | mostrar na tela | caixa de aceite e links no cadastro | [LGPD](simulado.html#q-lgpd-aceite) |
| 24:15–26:11 | cadastro com confirmação de senha diferente; sem opção de ver a senha | testar erro ao vivo | o front compara exatamente; **não há "mostrar senha"** | [senha](simulado.html#q-auth-confirmacao) |
| 26:11–26:44 | "existe no banco um campo que diga se aceitou?" Não existia | prova no banco | `termsVersion`, `termsAcceptedAt` e log; falha em contas migradas | [prova](simulado.html#q-lgpd-aceite) |
| 27:29–27:45 | "no banco, a senha está criptografada?" resposta: hash | abrir o documento | bcrypt custo 12 | [hash](simulado.html#q-auth-hash) |
| 28:28–29:17 | exigência de **data e hora** do aceite; validação que deixou passar senha errada | persistência e validação | data e hora do servidor; validação repetida na API | [validação](simulado.html#q-seg-validacao) |
| 29:27–29:45 | "com quais APIs integrou?"; integração incompleta mostrada no código | saber listar e justificar | Brevo, Google, Firebase (migração), DiceBear | [APIs](simulado.html#q-api-externas) |
| 30:09–30:40 | código de funcionalidade inexistente criticado | código limpo | **há código Firebase sem uso** | [legado](simulado.html#q-dec-legado) |
| 30:52–31:46 | rotas protegidas, CORS, **credenciais expostas** e falta de variável de ambiente; justificativa "é acadêmico" rejeitada | padrão profissional | segredos em ambiente; mostrar `.env.example` e `.gitignore` | [segredos](simulado.html#q-seg-segredos) |
| 32:34–33:25 | falhas consideradas graves e aceite sem registro | comprovar | ter a consulta pronta | [prova](simulado.html#q-lgpd-aceite) |
| 58:42–59:44 | tempo abaixo do mínimo; ensaiar e antecipar perguntas | preparo | cronometrar o roteiro | [testes](testes.html#manual) |
| 1:00:47–1:01:49 | ferramenta de teste; "unitário é obrigatório"; mostrar o teste de autenticação | executar ao vivo | integração no GitHub; unitários só locais | [unitários](simulado.html#q-tes-unitario) |
| 1:03:37–1:04:07 | comentários que parecem de gerador de código | autoria e domínio | saber explicar cada arquivo que mostrar | [código](simulado.html#q-dec-autoria) |
| 1:04:40, 1:10:04–1:11:05 | dado sensível exposto; layout quebrado ao reduzir a janela | testar responsividade | há media queries; **testem a sala no dia** | [responsivo](simulado.html#q-dec-responsivo) |
| 1:05:11–1:08:55 | valor negativo e regra de parcelas errada | regras de negócio pelo uso | testar entradas absurdas | [regras](simulado.html#q-reg-entradas) |
| 1:12:20–1:13:20 | exclusão definitiva; o administrador vê dados de quem? | papéis | admin vê logs, não conversas | [admin](simulado.html#q-seg-admin) |
| 1:15:27–1:16:29 | categorias iguais misturaram receita e despesa | integridade dos dados | índices únicos e filtros | [índices](simulado.html#q-mdb-indices) |
| 1:17:00–1:18:36 | cálculo de percentual sem fonte: "é da minha cabeça" criticado | embasamento | pontuação não tem referência documentada | [pontos](simulado.html#q-reg-pontuacao) |
| 1:38:09–1:40:36 | **apresentação** de arquitetura, tabelas, isolamento por usuário, hash, middlewares e testes | — (trecho expositivo; não há perguntas gravadas depois) | é o roteiro que podemos seguir | [arquitetura](simulado.html#q-arq-visao) |
| 1:46:25–1:46:55 | pergunta sobre o que o admin não pode fazer | regras por papel | listar permissões | [admin](simulado.html#q-seg-admin) |

## padroes | Padrões do questionamento | O que se repete.

### Assuntos
- LGPD e aceite com data e hora.
- Senhas e dados sensíveis.
- Credenciais, variáveis de ambiente e proteção de rotas.
- Validação de entradas e regras de negócio.
- Testes, principalmente unitários e de autenticação.
- Integrações, código sobrando, responsividade e embasamento.

### Profundidade
A banca não parou na definição: pediu para **abrir o banco**, **repetir a ação com dado errado** e **mostrar o arquivo**.

### Erros encontrados nos projetos
- Aceite não persistido.
- Cadastro concluído com confirmação de senha incorreta.
- Credenciais no código.
- Integração inacabada deixada no projeto.
- Valores negativos e cálculo financeiro incorreto.
- Dados misturados e layout quebrado.

### Respostas que não convenceram
- "É um ambiente acadêmico" como justificativa.
- "Vai ficar para melhoria futura" com o código já presente.
- "Eu criei a fórmula" sem fundamento.
- Procurar na hora o que deveria estar ensaiado.

## defesa | Como responder | Um método de quatro passos.

1. **Responda direto** em uma frase.
2. **Mostre**: tela, aba Rede, documento no banco ou teste.
3. **Abra o arquivo** e aponte a função.
4. **Admita o limite** e diga a correção.

> Exemplo: "O servidor calcula a pontuação e ignora a enviada. Aqui está `calcularPontuacao`. Mas hoje ele aceita que o cliente diga que resolveu; a correção é avaliar a resposta no servidor."

## divisao | Roteiro de demonstração sugerido | Cerca de 12 minutos, dentro da faixa de 10 a 15 citada no evento (confirmem a regra de vocês).

| Min | Ação | Quem prova |
| 0–2 | problema, público, objetivo | slides |
| 2–3 | arquitetura | [diagrama 1](diagramas.html#arquitetura) |
| 3–5 | cadastro, aceite e hash no banco | Atlas |
| 5–9 | partida com duas janelas, chat e Python | sistema |
| 9–10 | segurança: 401 e 403 | console |
| 10–11 | `npm test` (iniciar antes, pois leva ~1,5 min) | terminal |
| 11–12 | limitações e melhorias | [lista](seguranca.html#melhorias) |
