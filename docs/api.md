# API REST do ExameSUS

## Versão e autenticação

A primeira versão da API utiliza o prefixo `/api/v1/` e autenticação pela sessão do Django. O cliente deve autenticar o usuário pela aplicação web e manter o cookie de sessão. Requisições anônimas são recusadas.

## Exames

### Listar exames

`GET /api/v1/exames/`

- cidadão: somente seus exames;
- profissional: somente exames atribuídos a ele;
- servidor: todos os exames;
- ordenação: data e identificador, ambos decrescentes;
- paginação: cinco registros por página.

Parâmetros opcionais:

- `page`: página;
- `status`: `CONFIRMADO`, `EM_ANALISE`, `RESULTADO_DISPONIVEL` ou `CANCELADO`;
- `data_inicio`: data e horário em ISO 8601;
- `data_fim`: data e horário em ISO 8601;
- `unidade`: identificador numérico da unidade de saúde.

### Detalhar exame

`GET /api/v1/exames/<id>/`

Aplica as mesmas regras de isolamento da listagem. Um exame fora do escopo do usuário não é revelado e retorna `404`.

### Documento do resultado

Quando houver anexo, `documento_resultado_url` aponta para a rota protegida de download. O caminho físico do arquivo não é exposto.

## Escopo atual

Os endpoints são somente leitura. Criação, atualização e exclusão via API serão avaliadas incrementalmente.
