MongoDB Atlas | Banco orientado a documentos, acessado somente pelo servidor.
MongoDB guarda documentos BSON em coleções. O projeto usa o driver oficial `mongodb` e tem nove coleções: `users`, `authTokens`, `groups`, `invites`, `messages`, `games`, `gameHistory`, `auditLogs` e `rooms`.

{{codigo|backend/src/config/banco.js|export async function conectar}}

Índices aceleram consultas, impõem unicidade e, no caso de TTL, apagam documentos vencidos. Um índice não substitui validação nem autorização. O navegador nunca recebe a credencial do banco.

Documentos reais, relacionamentos e a diferença entre `games` e `gameHistory` estão em [API e banco](api-banco.html#colecoes).
