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

### Criar agendamento e exame

`POST /api/v1/exames/`

Disponível somente para servidor com as permissões `exames.add_agendamento` e `exames.add_exame`. A operação cria agendamento e exame na mesma transação, sempre com status inicial `CONFIRMADO`.

Corpo JSON:

```json
{
  "usuario": 1,
  "unidade": 1,
  "profissional": 2,
  "tipo": "Hemograma",
  "data_agendamento": "2026-10-09T14:00:00-03:00",
  "data_exame": "2026-10-10T14:00:00-03:00"
}
```

Somente cidadãos, unidades e profissionais ativos são aceitos. A data do exame deve ser posterior à data do agendamento.

### Atualizar estado e resultado

`PATCH /api/v1/exames/<id>/`

Disponível somente para o profissional responsável com a permissão `exames.change_exame`. A operação aceita apenas a próxima transição prevista no fluxo de status.

Exemplo de transição para análise:

```json
{
  "novo_status": "EM_ANALISE"
}
```

Para disponibilizar um resultado:

```json
{
  "novo_status": "RESULTADO_DISPONIVEL",
  "resultado": "Resultado descritivo do exame"
}
```

O resultado é obrigatório nessa transição. Um PDF opcional de até 10 MB pode ser enviado usando `multipart/form-data` no campo `documento_resultado`.

## Escopo atual

Listagem, detalhe, criação e atualização do fluxo profissional estão disponíveis. Exclusão via API será avaliada incrementalmente.
