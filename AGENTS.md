# AGENTS.md — Guia de implementação do ExameSUS

Este arquivo contém as regras permanentes para agentes de desenvolvimento que atuem neste repositório, especialmente o Codex.

As instruções deste documento devem ser consideradas antes de qualquer alteração no projeto. Uma solicitação explícita do responsável pelo projeto tem prioridade sobre este arquivo. Em caso de dúvida, conflito ou necessidade de desvio, pare e solicite aprovação.

---

## 1. Visão do projeto

O **ExameSUS** é uma plataforma digital acadêmica para gestão de exames no Sistema Único de Saúde. Seu objetivo é centralizar o agendamento, o acompanhamento, o histórico e o controle de exames, reduzindo processos demorados, burocráticos e pouco transparentes.

A aplicação deve oferecer uma experiência clara para cidadãos e profissionais de saúde, reunir informações em um único ambiente e apoiar a gestão pública com dados organizados.

### Objetivos principais

- permitir acesso às informações de exames por meio de autenticação;
- cadastrar e consultar cidadãos vinculados ao SUS;
- exibir exames agendados, realizados e seus resultados;
- manter histórico de exames, sem comparação automática de resultados;
- apresentar lembretes de acompanhamento por notificações internas;
- permitir a administração de unidades e profissionais de saúde;
- controlar acesso conforme o perfil do usuário;
- disponibilizar uma API REST;
- possuir testes automatizados e suporte a internacionalização.

---

## 2. Regras inegociáveis

1. **Implemente apenas uma funcionalidade por vez.**
2. **Implemente apenas uma tela por vez.**
3. **Implemente apenas um item de infraestrutura ou critério acadêmico por vez.**
4. Ao concluir uma unidade de trabalho, execute as verificações aplicáveis, apresente o resultado e **pare para validação**.
5. Não antecipe requisitos posteriores, mesmo quando pareçam relacionados.
6. Não altere requisitos, modelos, relacionamentos ou tecnologias sem autorização explícita.
7. Não crie funcionalidades extras antes de todos os requisitos obrigatórios estarem implementados, testados e validados.
8. Não faça refatorações amplas ou mudanças em arquivos não relacionados à tarefa atual.
9. Preserve o trabalho já existente no repositório. Antes de editar, inspecione a estrutura e as alterações locais.
10. Quando houver mais de uma solução tecnicamente válida, apresente a alternativa recomendada, a justificativa e os impactos antes de implementá-la.

### Regra de parada

Pare e consulte o responsável pelo projeto quando for necessário:

- adicionar ou remover modelo, tabela ou campo;
- alterar relacionamento, cardinalidade, nulabilidade ou restrição de banco;
- usar biblioteca, framework, serviço ou tecnologia não autorizada;
- mudar o significado de um requisito;
- escolher uma regra de negócio não documentada;
- definir sozinho como tratar uma inconsistência entre os requisitos e o modelo de dados;
- implementar integração externa, envio de e-mail, SMS, WhatsApp ou serviço de notificações;
- realizar uma alteração destrutiva ou irreversível.

Não contorne uma decisão pendente com uma implementação provisória silenciosa.

---

## 2.1 Decisões já confirmadas

As seguintes decisões estão aprovadas e não devem voltar a ser tratadas como dúvidas:

- autenticação por CPF e senha;
- cidadãos criam a própria conta e definem a própria senha;
- os perfis autenticáveis de domínio são Cidadão, Servidor e Profissional;
- `Profissional` é uma especialização autenticável de `Usuario`, implementada por herança multi-tabela, e utiliza CPF e senha;
- profissionais são criados exclusivamente pelo superusuário no Django Admin e não possuem autocadastro;
- o administrador do projeto é um superusuário do Django, criado com `python manage.py createsuperuser`, e utiliza exclusivamente o Django Admin;
- `cargo` e `especialidade` são campos distintos no cadastro de profissional;
- `especialidade` é opcional;
- comparação de resultados foi removida do escopo;
- notificações serão apresentadas por sino e badge numérica ao lado do nome do usuário;
- o Codex pode definir o evento de domínio mais adequado para gerar as notificações, desde que documente a decisão e permaneça na pilha autorizada;
- uma notificação é criada explicitamente para o profissional na atribuição inicial do exame;
- uma notificação é criada explicitamente para o cidadão quando o exame transiciona para `RESULTADO_DISPONIVEL`, orientando-o a consultar o resultado e realizar o acompanhamento necessário;
- apenas `UnidadeSaude.contato` e `Profissional.especialidade` podem ser nulos entre os campos de domínio já definidos;
- uma unidade pode existir temporariamente sem profissionais;
- cardinalidades descritas na seção 5 devem ser respeitadas;
- o conjunto de status de exame é fechado;
- `Agendamento.data` armazena data e horário;
- `Exame.data` armazena data e horário;
- cidadãos autenticados são direcionados para `/exames/`; profissionais são direcionados para sua lista de exames; todos os servidores são direcionados para `/usuarios/`; e superusuários são direcionados para o Django Admin;
- qualquer usuário com perfil `SERVIDOR` pode criar e editar cidadãos e servidores pela área `/usuarios/`, sem permissões Django adicionais; também pode editar e inativar profissionais por essa área, mas não alterar superusuários;
- unidades e profissionais devem ser desativados, e não excluídos fisicamente; profissionais utilizam `Usuario.is_active` como fonte única de ativação;
- usuários são desativados por meio do campo `is_active`; cidadãos e profissionais também podem ser inativados por servidores na área `/usuarios/`;
- a API REST deve usar Django REST Framework, com detalhamento incremental posterior.

---

## 3. Tecnologias autorizadas

### Backend

- Python;
- Django;
- Django REST Framework, pois a API REST é requisito obrigatório.

### Frontend

- Django Templates;
- HTML;
- CSS;
- JavaScript puro;
- recursos nativos ou já fornecidos pelo Django.

### Não utilizar sem aprovação

- React, Vue, Angular, Svelte ou frameworks equivalentes;
- Bootstrap, Tailwind CSS ou outros frameworks de interface;
- HTMX, Alpine.js, jQuery ou bibliotecas JavaScript adicionais;
- Celery, Redis, filas, schedulers externos ou serviços de background;
- bancos, serviços em nuvem ou APIs externas não definidos pelo responsável;
- geradores de PDF ou bibliotecas de gráficos antes da aprovação das funcionalidades opcionais;
- qualquer dependência nova que não seja indispensável aos requisitos autorizados.

Caso a pilha autorizada seja insuficiente, explique:

1. qual requisito não pode ser atendido adequadamente;
2. por que a solução atual é insuficiente;
3. qual dependência é proposta;
4. quais impactos ela traz;
5. qual alternativa existe sem essa dependência.

Aguarde aprovação antes de instalar ou usar a tecnologia proposta.

---

## 4. Arquitetura obrigatória

O projeto deve seguir a arquitetura **MVT do Django**.

### Responsabilidades

- **Models:** representar exclusivamente o domínio e as regras de persistência aprovadas.
- **Views:** coordenar requisições, permissões, formulários, consultas e respostas.
- **Templates:** apresentar dados, sem concentrar regras de negócio.
- **Forms:** validar entradas das páginas HTML.
- **Services ou selectors:** só criar quando a complexidade real justificar; não adicionar camadas abstratas sem necessidade.
- **URLs:** usar nomes de rota consistentes e namespaces por aplicação.
- **Static:** centralizar CSS, JavaScript e demais recursos visuais de forma organizada.
- **Tests:** acompanhar cada funcionalidade implementada.

### Organização

- Prefira aplicações Django separadas por domínio ou responsabilidade clara.
- Evite tanto uma única aplicação que concentre todo o sistema quanto fragmentação excessiva.
- Use herança de templates para cabeçalho, navegação, mensagens, conteúdo e rodapé.
- Evite lógica de consulta repetida e consultas N+1; use `select_related` e `prefetch_related` quando aplicável.
- Não coloque regras de negócio importantes apenas no JavaScript ou no template.
- A validação do servidor é obrigatória, mesmo quando existir validação no navegador.


### 4.1 Estrutura modular obrigatória

O ExameSUS deve ser desenvolvido como um **monólito modular em Django**: um único projeto, um único banco de dados e aplicações separadas por domínio. Não adotar microsserviços, frontend desacoplado ou arquitetura distribuída sem solicitação explícita.

A estrutura abaixo representa o **estado final pretendido**. Ela não autoriza a criação antecipada de todos os diretórios e arquivos. Cada aplicação, template, endpoint, serviço e conjunto de testes deve ser criado apenas quando a etapa correspondente entrar no escopo aprovado.

```text
ExameSUS/
├── AGENTS.md
├── README.md
├── manage.py
├── requirements.txt
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── usuarios/
│   ├── migrations/
│   ├── templates/
│   │   ├── usuarios/
│   │   │   ├── cadastro.html
│   │   │   └── lista.html
│   │   └── registration/
│   │       └── login.html
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_forms.py
│   │   ├── test_views.py
│   │   └── test_permissions.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── managers.py
│   ├── models.py
│   ├── permissions.py
│   ├── urls.py
│   └── views.py
│
├── rede_saude/
│   ├── migrations/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_admin.py
│   │   └── test_forms.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   └── models.py
│
├── exames/
│   ├── migrations/
│   ├── templates/
│   │   └── exames/
│   │       ├── lista.html
│   │       ├── historico.html
│   │       └── detalhe.html
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   ├── test_permissions.py
│   │   ├── test_status.py
│   │   └── test_api.py
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── services.py
│   ├── urls.py
│   └── views.py
│
├── notificacoes/                  # Criar apenas ao iniciar o RF006
│   ├── migrations/
│   ├── templates/
│   │   └── notificacoes/
│   │       └── lista.html
│   ├── tests/
│   ├── __init__.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── models.py
│   ├── services.py
│   ├── urls.py
│   └── views.py
│
├── templates/
│   ├── base.html
│   ├── includes/
│   │   ├── header.html
│   │   ├── footer.html
│   │   ├── messages.html
│   │   └── notification_bell.html
│   └── components/
│       ├── breadcrumb.html
│       ├── pagination.html
│       ├── status_badge.html
│       └── empty_state.html
│
├── static/
│   ├── css/
│   │   ├── tokens.css
│   │   ├── base.css
│   │   ├── layout.css
│   │   ├── components.css
│   │   └── pages/
│   ├── js/
│   │   └── main.js
│   └── img/
│       └── icons/
│
├── locale/
│   └── pt_BR/
│       └── LC_MESSAGES/
│
└── docs/
    ├── requisitos.md
    ├── modelo-de-dados.md
    └── api.md
```

Arquivos ilustrados na árvore podem ser omitidos enquanto não forem necessários. Não criar arquivos vazios apenas para reproduzir a estrutura.

### 4.2 Responsabilidades das aplicações

#### `config`

Deve conter apenas configurações globais do projeto:

- configurações do Django;
- URLs principais;
- ASGI e WSGI;
- configuração de templates, arquivos estáticos, i18n e Django REST Framework;
- definição de `AUTH_USER_MODEL = "usuarios.Usuario"` antes das migrations iniciais;
- configurações globais de login e redirecionamento.

Prefixos de URL recomendados:

```text
/admin/             Painel administrativo padrão do Django
/conta/             Autocadastro, login e logout
/usuarios/          Funcionalidades autorizadas para usuários
/exames/            Lista, histórico e detalhes de exames
/notificacoes/      Notificações do cidadão
/api/v1/            API REST versionada
```

O prefixo `/api/v1/` deve ser adotado quando a primeira rota da API for aprovada.

#### `usuarios`

Responsável por:

- modelo customizado `Usuario`;
- `UsuarioManager`, incluindo `create_user()` e `create_superuser()`;
- autenticação por CPF e senha;
- autocadastro do cidadão;
- logout;
- listagem paginada de usuários;
- perfis `CIDADAO`, `SERVIDOR` e `PROFISSIONAL`;
- ativação e desativação por `is_active`;
- forms, views e permissões relacionadas a usuários.

`tipo` identifica o perfil de domínio, mas não substitui as permissões nativas do Django. Operações sensíveis podem exigir simultaneamente o perfil adequado e a permissão Django correspondente. `is_staff` deve permanecer reservado ao acesso ao Django Admin; um servidor comum não precisa ser `is_staff`.

#### `rede_saude`

Responsável por:

- `UnidadeSaude`;
- `Profissional`;
- especialização autenticável de `Usuario` para o profissional;
- validações desses modelos;
- configuração de ambos no Django Admin;
- desativação e reativação do profissional por `Usuario.is_active`;
- filtragem de unidades ativas para novos vínculos.

O cadastro inicial de unidades e profissionais permanece no Django Admin. A edição e a inativação de profissionais também são disponibilizadas aos servidores autenticados pela área `/usuarios/`.

O `admin.py` deve, quando os respectivos requisitos forem implementados, oferecer listagem, busca, filtros, edição, desativação e reativação, sem exclusão física.

#### `exames`

Responsável por:

- `Agendamento`;
- `Exame`;
- enum e fluxo de status;
- validação das transições;
- lista de exames do cidadão;
- histórico;
- detalhes e resultados;
- criação transacional de agendamento e exame pelo servidor autorizado;
- lista e detalhe dos exames atribuídos ao profissional autenticado;
- transições de status e registro de resultado pelo profissional responsável;
- consultas restritas ao usuário autenticado;
- API relacionada a exames, quando aprovada.

`Agendamento` e `Exame` devem permanecer na mesma aplicação por integrarem o mesmo fluxo de domínio. Não separá-los em aplicações distintas sem necessidade real e aprovação.

A lógica reutilizável de transição de status deve ficar centralizada, preferencialmente em função ou serviço como `transicionar_status(exame, novo_status, usuario_responsavel)`, quando houver mais de uma interface alterando o status. Essa operação deve validar o fluxo, persistir de forma transacional e disparar a criação de notificação quando a regra aprovada exigir.

Como `Exame` e `Agendamento` armazenam usuário e unidade, validar no backend que:

```text
exame.usuario_id == exame.agendamento.usuario_id
exame.unidade_id == exame.agendamento.unidade_id
```

Essa validação evita registros contraditórios e não modifica o modelo aprovado.

Não impor que `exame.profissional.unidade_id == exame.unidade_id`. Está aprovado associar ao exame um profissional cuja unidade principal seja diferente da unidade do exame.

#### `notificacoes`

Criar somente quando o RF006 for iniciado.

Responsável por:

- modelo mínimo de notificação, caso necessário;
- persistência e estado de leitura;
- consulta das notificações do cidadão;
- página de notificações;
- serviço explícito de criação;
- badge de notificações não lidas no cabeçalho.

A notificação deve identificar o evento que a originou e admitir múltiplos destinatários e eventos para o mesmo exame. A unicidade deve ser garantida pela combinação de exame, destinatário e tipo de evento.

Um context processor pode fornecer a quantidade de notificações não lidas aos templates globais. A consulta deve ser executada apenas para usuário autenticado e não pode expor notificações de terceiros.

Preferir chamadas explícitas em `notificacoes/services.py` a sinais do Django. Não usar signals para ocultar efeitos colaterais, salvo justificativa concreta e aprovação.

### 4.3 Templates e componentes compartilhados

Todas as páginas da aplicação comum devem herdar de `templates/base.html`.

O template base deve concentrar:

- cabeçalho;
- identificação do usuário;
- sino de notificações;
- área de breadcrumb;
- mensagens do Django;
- conteúdo principal;
- rodapé.

Elementos repetidos devem ser extraídos para includes ou componentes, especialmente:

- paginação;
- badge de status;
- breadcrumb;
- alertas e mensagens;
- estado vazio;
- sino de notificações.

O mesmo componente de status deve ser usado em lista, histórico e detalhes para preservar texto, cor e acessibilidade.

### 4.4 Organização de CSS e JavaScript

A organização visual recomendada é:

- `tokens.css`: cores, espaçamentos, tipografia e variáveis;
- `base.css`: normalização, elementos HTML, tipografia e acessibilidade;
- `layout.css`: container, cabeçalho, navegação, grids e rodapé;
- `components.css`: botões, alertas, badges, formulários, tabelas, paginação e breadcrumbs;
- `pages/`: apenas estilos específicos que não possam ser compartilhados.

Não concentrar todo o CSS em um arquivo excessivamente grande e não criar fragmentação desnecessária em dezenas de arquivos mínimos.

O JavaScript deve permanecer pequeno e progressivo. Regras de negócio, autorização e validações essenciais devem funcionar no servidor e não podem depender exclusivamente de JavaScript.

### 4.5 Organização da API REST

Não criar uma aplicação central genérica chamada `api` para concentrar todos os recursos.

Quando um domínio receber endpoints aprovados, criar um subpacote dentro da própria aplicação, por exemplo:

```text
exames/
└── api/
    ├── __init__.py
    ├── serializers.py
    ├── permissions.py
    ├── urls.py
    └── views.py
```

Aplicar a mesma abordagem em `usuarios` ou `notificacoes` somente quando existirem endpoints aprovados para esses domínios.

As URLs devem ser agregadas em `config/urls.py` sob `/api/v1/`. A API deve reutilizar as regras de domínio existentes, e não manter uma segunda implementação das mesmas regras.

### 4.6 Organização dos testes

Os testes devem ficar dentro da aplicação responsável pelo comportamento testado, em pacote `tests/`.

Separar por responsabilidade quando houver volume suficiente, por exemplo:

```text
exames/tests/
├── test_models.py
├── test_status.py
├── test_views.py
├── test_permissions.py
└── test_api.py
```

Começar com `django.test.TestCase` e `setUpTestData()` quando adequados. Não adicionar `pytest`, `factory_boy` ou bibliotecas equivalentes sem aprovação.

Os testes devem acompanhar cada funcionalidade. A etapa final de testes é de consolidação, não de criação tardia de toda a suíte.

### 4.7 Direção das dependências

A direção recomendada é:

```text
usuarios ───────────────┐
                        ├──► exames
rede_saude ─────────────┘

usuarios ───────────────┐
                        ├──► notificacoes
exames ─────────────────┘
```

Regras:

- `usuarios` não deve depender de `exames`;
- `rede_saude` não deve depender de `exames`;
- `exames` pode referenciar usuários, unidades e profissionais;
- `notificacoes` pode referenciar usuário e, se necessário, exame;
- uma aplicação não deve importar views ou forms de outra aplicação;
- usar referências por string nos relacionamentos entre models quando isso evitar importações circulares;
- evitar ciclos de dependência entre módulos.

---

## 5. Modelo de dados autorizado

Respeite os modelos, campos, restrições e relacionamentos definidos nesta seção. As decisões abaixo substituem as pendências anteriores sobre autenticação, perfis, nulabilidade, cardinalidade, status e exclusão física.

### 5.1 Usuário e autenticação

O usuário autenticável deve ser um **modelo de usuário customizado do Django**, definido antes das migrations iniciais do projeto.

Campos de domínio:

- `id`;
- `nome`;
- `cpf`, único e obrigatório;
- `tipo`, obrigatório.

Regras de autenticação:

- o login deve utilizar exclusivamente **CPF e senha**;
- `cpf` deve ser o identificador de autenticação (`USERNAME_FIELD`);
- não utilizar nome de usuário ou e-mail como credencial de login;
- a senha nunca deve ser armazenada em texto puro;
- utilizar os mecanismos nativos de hashing, sessão e autenticação do Django;
- normalizar o CPF antes de autenticar e persistir;
- o modelo customizado deve ser criado antes da primeira migration relevante, evitando troca tardia do modelo de usuário.

Campos técnicos exigidos pelo sistema de autenticação e permissões do Django, como `password`, `last_login`, `is_active`, `is_staff`, `is_superuser`, grupos e permissões, são permitidos. Eles não devem ser tratados como novos campos de negócio nem removidos apenas para reproduzir literalmente a tabela conceitual inicial.

Valores permitidos para `tipo`:

- `CIDADAO`;
- `SERVIDOR`.
- `PROFISSIONAL`.

`PROFISSIONAL` identifica a identidade autenticável especializada pelo modelo de domínio `Profissional`.

Utilize `TextChoices` ou mecanismo equivalente do próprio Django para manter os valores centralizados. Não adicionar outro valor de perfil sem aprovação.

O superusuário criado por `createsuperuser` deve utilizar `tipo=SERVIDOR` como convenção técnica, mas sua autorização administrativa depende de `is_staff` e `is_superuser`, e não do campo `tipo`.

### 5.2 Exame

Campos:

- `id`;
- `tipo`, obrigatório;
- `data`, obrigatória;
- `status`, obrigatório;
- `resultado`, não nulo;
- `documento_resultado`, opcional, com ausência representada por string vazia e sem `NULL`;
- `usuario_id`, obrigatório;
- `unidade_id`, obrigatório;
- `profissional_id`, obrigatório;
- `agendamento_id`, obrigatório.

Valores permitidos para `status`:

- `CONFIRMADO` — “Confirmado”;
- `EM_ANALISE` — “Em análise”;
- `RESULTADO_DISPONIVEL` — “Resultado disponível”;
- `CANCELADO` — “Cancelado”.

O conjunto de status é fechado. Não criar status adicional sem aprovação.

Transições aprovadas:

```text
CONFIRMADO
├── EM_ANALISE
│   └── RESULTADO_DISPONIVEL
└── CANCELADO
```

Regras:

- `CONFIRMADO` pode mudar para `EM_ANALISE` ou `CANCELADO`;
- `EM_ANALISE` pode mudar apenas para `RESULTADO_DISPONIVEL`;
- `CANCELADO` e `RESULTADO_DISPONIVEL` são estados finais no fluxo aprovado;
- não permitir regressão de status ou transição diferente das listadas;
- validar as transições no backend e cobri-las com testes automatizados.

Como `resultado` não pode ser nulo e pode ainda não existir em exames não concluídos, represente a ausência de resultado com string vazia no banco (`null=False`, podendo usar `blank=True` e valor padrão vazio). A interface deve apresentar uma mensagem como “Resultado ainda não disponível”, e nunca exibir apenas um campo vazio.

`documento_resultado` é um único arquivo PDF opcional, limitado a 10 MB e armazenado localmente em área privada. Somente o cidadão proprietário e o profissional responsável podem baixá-lo por rota protegida. O profissional pode enviá-lo ou substituí-lo apenas na transição para `RESULTADO_DISPONIVEL`; ao substituir, o arquivo anterior deve ser removido sem excluir o exame.

### 5.3 Agendamento

Campos:

- `id`;
- `usuario_id`, obrigatório;
- `unidade_id`, obrigatório;
- `data`, obrigatória.

### 5.4 Unidade de Saúde

Campos:

- `id`;
- `nome`, obrigatório;
- `endereco`, obrigatório;
- `contato`, opcional e anulável;
- `ativo`, booleano, obrigatório, com padrão `True`.

`ativo` é autorizado para permitir desativação sem exclusão física.

### 5.5 Profissional

Campos:

- identidade herdada de `Usuario`, incluindo `id`, `nome`, `cpf`, senha e `is_active`;
- `cargo`, obrigatório;
- `especialidade`, opcional e anulável;
- `unidade_id`, obrigatório;

Regras:

- `cargo` identifica a função principal, por exemplo “Médico”, “Psicólogo” ou “Fisioterapeuta”;
- `especialidade` é utilizada quando aplicável e pode ficar nula, inclusive para profissional sem especialidade cadastrada ou clínico geral;
- não exigir especialidade de todos os profissionais;
- não substituir `cargo` por `especialidade` nem combinar ambos em um único campo.
- todo `Profissional` deve corresponder a exatamente um `Usuario` com `tipo=PROFISSIONAL`;
- o superusuário cria a identidade profissional e define sua senha no Django Admin;
- profissionais migrados de cadastros anteriores recebem senha inutilizável até que o superusuário defina uma senha;
- conflitos de CPF entre cadastros legados de usuário e profissional devem interromper a migração com erro claro, sem associação automática;
- não oferecer autocadastro profissional.

`Usuario.is_active` é a fonte única de ativação e desativação do profissional.

### 5.6 Nulabilidade

Entre os campos de domínio definidos neste documento, apenas os seguintes podem receber `NULL` no banco:

- `UnidadeSaude.contato`;
- `Profissional.especialidade`.

Todos os demais campos de domínio devem usar `null=False`.

Campos técnicos gerenciados pelo Django podem seguir as exigências do framework. Valores temporariamente indisponíveis em campos textuais não anuláveis, como `Exame.resultado`, devem seguir a convenção explicitamente definida neste documento, e não usar `NULL`.

### 5.7 Cardinalidades obrigatórias

- um usuário possui zero ou vários agendamentos;
- cada agendamento pertence a exatamente um usuário;
- uma unidade de saúde recebe zero ou vários agendamentos;
- cada agendamento ocorre em exatamente uma unidade;
- um agendamento gera zero ou vários exames;
- cada exame está associado a exatamente um agendamento;
- um usuário realiza zero ou vários exames;
- cada exame pertence a exatamente um usuário;
- uma unidade realiza zero ou vários exames;
- cada exame é realizado em exatamente uma unidade;
- um profissional solicita ou realiza zero ou vários exames;
- cada exame é associado a exatamente um profissional;
- cada profissional pertence a exatamente uma unidade;
- cada profissional especializa exatamente um usuário com `tipo=PROFISSIONAL`;
- uma unidade pode alocar zero ou vários profissionais, inclusive permanecer temporariamente sem nenhum;

Use `ForeignKey` no lado “vários”. Não transforme essas relações em `ManyToManyField` ou `OneToOneField` sem aprovação.

### 5.8 Integridade referencial e desativação

- não oferecer exclusão física de usuários, unidades ou profissionais pela interface ou API;
- unidades devem ser desativadas por flag booleana própria;
- usuários autenticáveis, incluindo profissionais, devem utilizar o mecanismo `is_active` do Django;
- ativação e desativação de usuários devem ocorrer pelo Django Admin, sem necessidade de tela própria na aplicação comum;
- registros desativados devem continuar visíveis em históricos já existentes;
- registros desativados não devem aparecer como opção para novos vínculos, salvo necessidade administrativa explicitamente aprovada;
- utilizar proteção referencial, preferencialmente `PROTECT`, nas relações que preservam histórico;
- não usar `CASCADE` em relações que possam apagar exames, agendamentos ou outros dados históricos;
- exames e agendamentos não possuem operação de exclusão física aprovada.

Toda mudança de schema deve ser acompanhada de migration e testes apropriados.

### 5.9 Restrições adicionais

- não adicione campos de auditoria, timestamps automáticos, enums, tabelas auxiliares ou modelos de notificação além dos expressamente autorizados;
- não substitua os modelos definidos por estruturas genéricas;
- não altere nomes ou relações apenas por preferência técnica;
- não duplique CPF em estruturas novas sem necessidade e sem regra clara de sincronização;
- não duplique nome, CPF, senha ou estado de ativação em `Profissional`; esses dados pertencem à identidade `Usuario` herdada.

---

## 6. Perfis, atores e autorização

### Cidadão

Usuário autenticável que procura atendimento de saúde. Pode criar a própria conta, acessar seus próprios agendamentos, exames, resultados, histórico e notificações.

### Servidor

Usuário autenticável que medeia o atendimento entre cidadão e profissional. Com as permissões Django necessárias, cria conjuntamente o agendamento e o exame, associa cidadão, unidade e profissional e não executa o exame em nome do profissional.

### Profissional de Saúde

Usuário autenticável e entidade de domínio representada pelo modelo `Profissional`, que especializa `Usuario`. Pode ser médico, psicólogo, psiquiatra, fisioterapeuta ou outro profissional cadastrado.

Neste projeto, `Profissional`:

- autentica com CPF e senha e possui `Usuario.tipo=PROFISSIONAL`;
- é criado exclusivamente pelo superusuário no Django Admin;
- acessa apenas os exames nos quais está indicado como profissional responsável;
- pode executar as transições aprovadas, incluindo cancelamento somente nos estados permitidos;
- registra obrigatoriamente um resultado não vazio ao transicionar de `EM_ANALISE` para `RESULTADO_DISPONIVEL`;
- não pode alterar cidadão, unidade, profissional responsável, tipo ou datas do exame.

### Administrador do Django

O administrador é um superusuário técnico criado com:

```bash
python manage.py createsuperuser
```

Esse administrador:

- acessa o painel padrão do Django Admin;
- deve possuir `is_staff=True` e `is_superuser=True`;
- é responsável por administrar unidades, profissionais e ativação ou desativação de usuários;
- não constitui um novo valor no campo `Usuario.tipo`;
- utiliza `tipo=SERVIDOR` como convenção do modelo customizado;
- não exige a criação de dashboard administrativo próprio para cumprir RF007 ou RF008.

### Princípios obrigatórios

- um cidadão só pode acessar seus próprios dados, exames, agendamentos, histórico e notificações;
- um servidor só pode executar ações expressamente permitidas;
- um cidadão não pode criar agendamentos ou exames;
- um servidor autorizado cria o agendamento e o exame de forma transacional, sempre com status inicial `CONFIRMADO`;
- um profissional só pode consultar e operar exames atribuídos a ele;
- funções administrativas de RF007 e RF008 devem ser implementadas no Django Admin;
- autenticação não substitui autorização;
- toda restrição deve existir no backend, não apenas na interface;
- endpoints da API devem aplicar as mesmas regras de acesso das páginas;
- permissões por objeto devem impedir acesso por alteração manual de URL ou requisição;
- tentativas sem permissão devem retornar comportamento HTTP adequado e mensagem compreensível.

---

## 7. Requisitos funcionais obrigatórios

Todos os requisitos RF001 a RF011 são obrigatórios. A implementação deve respeitar a ordem aprovada pelo responsável e ocorrer uma funcionalidade por vez.

### RF001 — Login com CPF e senha

O usuário deve entrar no sistema usando CPF e senha.

Critérios mínimos:

- campo de CPF claramente identificado;
- campo de senha com tipo apropriado;
- CPF normalizado antes da autenticação;
- autenticação pelo modelo customizado do Django, com `cpf` como identificador;
- senha armazenada apenas por meio do hashing nativo do Django;
- mensagem de erro genérica, sem confirmar se determinado CPF existe;
- sessão autenticada pelo Django;
- redirecionamento conforme o perfil e as permissões após o sucesso;
- proteção contra acesso anônimo às páginas privadas;
- testes de login válido, senha inválida, CPF inexistente, CPF formatado e acesso anônimo.

Não implementar login por nome de usuário ou e-mail.

### RF002 — Autocadastro do cidadão

O próprio cidadão deve criar sua conta e definir sua senha para acessar o sistema.

Esta decisão não autoriza cidadão, servidor ou profissional a criar contas de profissional. O cadastro profissional é exclusivo do superusuário no Django Admin.

Critérios mínimos:

- formulário público de cadastro com os campos autorizados do usuário;
- criação obrigatória com `tipo=CIDADAO`;
- CPF único, normalizado e validado;
- senha informada e confirmada pelo próprio cidadão;
- aplicação dos validadores de senha configurados no Django;
- senha armazenada apenas pelo mecanismo nativo de hashing do Django;
- mensagens claras de sucesso e erro;
- proteção contra CPF duplicado;
- login posterior com CPF e senha;
- testes de formulário, CPF, confirmação de senha, força mínima configurada e persistência.

Não usar CPF como senha, não criar senha padrão e não enviar credenciais por canal externo. A recuperação de senha não integra o escopo atual, salvo solicitação posterior.

### RF003 — Lista paginada de usuários

Qualquer usuário com perfil `SERVIDOR` deve visualizar cidadãos e servidores de forma paginada, sem exigir uma permissão Django adicional para esta consulta.

Critérios mínimos:

- paginação feita no servidor;
- ordenação estável;
- navegação acessível entre páginas;
- preservação de filtros, caso filtros sejam posteriormente aprovados;
- estado vazio compreensível;
- acesso restrito ao perfil autorizado;
- testes de paginação e permissão.

Não adicione pesquisa, filtros avançados ou exportação como parte deste requisito sem autorização.

### RF004 — Lista de exames do cidadão

O cidadão deve visualizar exames agendados e realizados.

A listagem deve apresentar, no mínimo:

- data;
- tipo do exame;
- local ou unidade de saúde;
- status.

Critérios mínimos:

- mostrar apenas exames do cidadão autenticado;
- diferenciar status com texto e estilo visual consistente;
- ordenar de maneira definida e documentada;
- tratar estado vazio;
- impedir vazamento de exames de outro usuário;
- possuir testes de consulta, permissão e apresentação dos dados essenciais.

### RF005 — Histórico de exames

O cidadão deve visualizar seu histórico completo de exames e resultados anteriores.

A funcionalidade de comparação de dados foi descartada e **não deve ser implementada**.

Critérios mínimos:

- histórico restrito ao cidadão autenticado;
- exames organizados cronologicamente;
- indicação de tipo, data, unidade, profissional, status e resultado quando disponível;
- mensagem clara quando o resultado ainda não estiver disponível;
- estado vazio compreensível;
- nenhuma interpretação, comparação ou recomendação clínica automática;
- testes de isolamento dos dados, ordenação e apresentação.

### RF006 — Lembretes e notificações no sistema

O cidadão deve ser informado quando houver lembrete de acompanhamento relacionado a exame de controle.

Apresentação visual aprovada:

- utilizar um ícone de sino no cabeçalho;
- posicionar o sino ao lado do nome do usuário autenticado;
- exibir uma badge com a quantidade de notificações pendentes;
- ocultar a badge quando a quantidade for zero;
- fornecer nome acessível ao botão ou link do sino;
- não depender apenas da cor para comunicar a quantidade;
- manter o padrão em telas desktop e móveis.

Não implementar e-mail, SMS, WhatsApp, push notification, Celery, Redis ou serviço externo.

O Codex está autorizado a definir a regra de geração da notificação que melhor se encaixe no ciclo de exames e lembretes de acompanhamento.

Ao tomar essa decisão, deve:

- explicar qual evento gera a notificação e por que ele atende ao RF006;
- preferir uma solução simples baseada no banco de dados local e nos recursos do Django;
- implementar persistência, estado de leitura e atualização da badge de forma coerente;
- não usar Celery, Redis, tarefas externas, e-mail, SMS, WhatsApp ou push;
- evitar temporizadores ou processamento em background enquanto isso não for aprovado;
- criar, caso necessário, apenas o modelo mínimo de notificação, com campos não nulos e migration correspondente;
- garantir que cada cidadão visualize somente suas próprias notificações;
- documentar a regra escolhida e cobri-la com testes.

A autonomia concedida nesta seção limita-se à regra interna das notificações e não autoriza dependências externas ou funcionalidades adicionais.

### RF007 — Administração de unidades de saúde

O superusuário deve configurar unidades de saúde pelo painel padrão do Django Admin com:

- nome;
- endereço;
- contato opcional.

Critérios mínimos:

- listagem;
- cadastro;
- edição;
- desativação e reativação;
- validação dos campos;
- restrição a usuários com acesso ao Django Admin e permissões administrativas adequadas;
- preservação da integridade dos exames e profissionais vinculados;
- confirmação antes da desativação;
- testes de permissão, validação, persistência e filtragem de unidades inativas.

Não oferecer exclusão física.

### RF008 — Administração de profissionais de saúde

O superusuário deve gerenciar profissionais de saúde pelo painel padrão do Django Admin. Servidores autenticados também podem editar e inativar profissionais pela área `/usuarios/`, sem acesso à criação de profissionais.

- nome;
- CPF;
- cargo;
- especialidade opcional;
- unidade de trabalho;
- situação ativa ou inativa.

Critérios mínimos:

- CPF único, normalizado e validado;
- cargo obrigatório;
- especialidade opcional;
- vínculo obrigatório com unidade de saúde;
- listagem, cadastro, edição, desativação e reativação;
- unidades desativadas não devem ser oferecidas para novos vínculos;
- criação restrita ao superusuário no Django Admin; edição e inativação também permitidas a usuários com perfil `SERVIDOR`;
- mensagens e validações claras;
- testes de permissão, unicidade, relacionamento e desativação.

Não oferecer exclusão física.

### RF009 — Autenticação e controle de acesso por perfil

O sistema deve proteger dados e operações com autenticação e autorização por perfil.

Critérios mínimos:

- proteção das views e endpoints;
- restrição por objeto quando necessário;
- redirecionamento ou resposta HTTP adequada;
- navegação sem links para ações proibidas, sem depender disso como proteção;
- testes para usuário anônimo, perfil autorizado, perfil não autorizado, usuário inativo e acesso a objeto de terceiro;
- uso das proteções padrão do Django, incluindo CSRF nas operações HTML.

### RF010 — Gestão operacional de agendamentos e exames

O servidor autorizado deve mediar o atendimento criando o agendamento e o exame para um cidadão e indicando o profissional responsável. O cidadão não pode criar exames. O profissional indicado deve acompanhar e executar o fluxo do exame em área autenticada própria.

#### Criação pelo servidor

- utilizar um único formulário para criar `Agendamento` e `Exame` de forma transacional;
- permitir apenas cidadão, unidade e profissional ativos;
- exigir perfil `SERVIDOR` e permissões Django para adicionar agendamento e exame;
- solicitar datas independentes e exigir que a data do exame seja posterior à data do agendamento;
- permitir profissional cuja unidade principal seja diferente da unidade do exame;
- criar o exame obrigatoriamente em `CONFIRMADO`;
- impedir criação por cidadão ou profissional;
- criar uma notificação única de atribuição para o profissional indicado.

#### Operação pelo profissional

- apresentar lista paginada contendo somente exames atribuídos ao profissional autenticado;
- apresentar uma tela de detalhes com dados do exame, cidadão, unidade e agendamento;
- permitir apenas as próximas transições definidas no fluxo aprovado;
- permitir cancelamento somente nos estados que já admitem `CANCELADO`;
- exigir e salvar resultado não vazio na mesma transação que altera `EM_ANALISE` para `RESULTADO_DISPONIVEL`;
- permitir, nessa mesma transição, anexar ou substituir um único PDF opcional de até 10 MB referente ao resultado;
- disponibilizar o anexo somente por download protegido ao cidadão proprietário e ao profissional responsável;
- impedir alteração de cidadão, unidade, profissional, tipo e datas;
- exigir perfil `PROFISSIONAL`, permissão Django aplicável e vínculo do exame ao profissional autenticado.

#### Notificações e navegação

- reutilizar sino, badge, página e estado de leitura para cidadão e profissional;
- garantir isolamento por destinatário;
- permitir notificações distintas de atribuição e resultado disponível no mesmo exame;
- garantir unicidade por exame, destinatário e tipo de evento;
- redirecionar profissional autenticado para sua lista de exames;
- manter cidadãos em `/exames/`, servidores nos destinos autorizados e superusuários no Django Admin.

### RF011 — Testes automatizados

As funcionalidades principais devem possuir testes automatizados.

Cobrir, conforme aplicável:

- models e restrições;
- forms e validações;
- views e códigos de resposta;
- autenticação e autorização;
- isolamento de dados por usuário;
- paginação;
- endpoints da API;
- desativação e filtragem de registros inativos;
- transições válidas e inválidas de status;
- fluxos de sucesso e falha;
- regressões identificadas durante o desenvolvimento.

Os testes devem ser executáveis de maneira reproduzível com o comando padrão do projeto.

---

## 8. Critérios acadêmicos obrigatórios

Além dos requisitos funcionais, o projeto deve demonstrar:

- funcionalidades implementadas conforme os requisitos;
- arquitetura MVT;
- paginação;
- autenticação;
- autorização;
- API REST com Django REST Framework;
- testes automatizados;
- internacionalização (`i18n`).

Esses itens não devem ser apenas declarados. Devem estar presentes no código, ser demonstráveis e possuir documentação mínima de uso.

---

## 9. API REST

A API deve usar Django REST Framework e refletir apenas recursos e operações previamente aprovados.

Por enquanto, está autorizado:

- configurar Django REST Framework;
- utilizar serializers, autenticação, permissões e paginação padrão quando adequados;
- expor recursos do domínio de forma incremental;
- implementar um recurso ou endpoint por vez;
- manter as mesmas regras de autorização e desativação das páginas HTML.

### Regras

- não gerar CRUD completo automaticamente para todos os modelos;
- não tornar endpoints públicos por padrão;
- não expor senha, hashes, permissões internas ou dados além do necessário;
- filtrar querysets para impedir acesso a dados de terceiros;
- não permitir exclusão física por `DELETE`;
- quando uma operação de remoção administrativa for aprovada, ela deve representar desativação;
- use serializers para validação e representação;
- utilize códigos HTTP adequados;
- retorne erros estruturados e compreensíveis;
- pagine coleções quando aplicável;
- adicione testes de API para sucesso, validação, autenticação e autorização;
- não crie operações de escrita apenas porque o DRF as facilita.

A escolha entre APIViews, generic views ou ViewSets deve considerar simplicidade, clareza e o escopo real. Evite abstração excessiva.

**Pendências para a fase da API:** recursos expostos, métodos permitidos por perfil, forma de autenticação da API, versionamento e política detalhada de desativação. Antes de cada endpoint, apresente a proposta e aguarde validação.

---

## 10. Internacionalização

O projeto deve possuir suporte a `i18n`.

### Regras

- idioma principal da interface: português do Brasil;
- envolver textos visíveis do Python com `gettext` ou `gettext_lazy`;
- usar `{% trans %}` ou `{% blocktrans %}` nos templates;
- não concatenar frases traduzíveis de forma que quebre a gramática;
- manter formatos de data e hora coerentes com a localização;
- não deixar textos visíveis espalhados no JavaScript sem estratégia de tradução;
- validar o carregamento das traduções com ao menos um cenário demonstrável.

Não é necessário traduzir toda a aplicação para vários idiomas em uma única tarefa. A infraestrutura e a adoção progressiva devem ser implementadas e validadas conforme o escopo aprovado.

---

## 11. Identidade visual

A interface deve ser inspirada na linguagem visual dos serviços digitais do Governo Federal e do GOV.BR, sem copiar literalmente sua marca.

### Características desejadas

- institucional, sem ser burocrática;
- simples, sem parecer vazia;
- acolhedora, sem ser infantil;
- moderna, sem ser futurista;
- objetiva, sem ser fria;
- consistente entre todas as páginas;
- acessível para usuários com diferentes níveis de familiaridade digital.

### Evitar

- gradientes chamativos;
- efeitos 3D;
- sombras intensas;
- cores neon;
- animações exageradas;
- excesso de decoração;
- aparência comercial ou informal;
- componentes visualmente inconsistentes;
- excesso de informação competindo pela atenção.

### Cores

Use variáveis CSS para os tokens principais.

```css
:root {
  --color-primary: #1351B4;
  --color-primary-dark: #0C326F;
  --color-heading: #071D41;
  --color-info-soft: #E6F0FF;
  --color-info-soft-strong: #D4E5FF;

  --color-background: #FFFFFF;
  --color-background-secondary: #F8F8F8;
  --color-surface-grouped: #F1F1F1;
  --color-border: #D9D9D9;
  --color-border-strong: #B8B8B8;

  --color-text: #333333;
  --color-text-strong: #1B1B1B;
  --color-text-secondary: #555555;
  --color-text-muted: #666666;
  --color-text-disabled: #888888;
  --color-text-on-dark: #FFFFFF;

  --color-success: #168821;
  --color-success-soft: #E8F5E9;
  --color-danger: #E52207;
  --color-danger-soft: #FDECEA;
  --color-warning: #FFCD07;
  --color-warning-soft: #FFF7D6;
}
```

### Tipografia

```css
font-family: "Rawline", "Raleway", Arial, Helvetica, sans-serif;
```

Não inclua arquivos de fonte ou dependências externas sem aprovação. Use o fallback disponível quando Rawline ou Raleway não estiverem instaladas.

Hierarquia recomendada:

- título principal: `32px`, peso 600 ou 700, linha aproximada de 1.2;
- título de seção: `24px`, peso 600;
- subtítulo: `20px`, peso 600;
- título de cartão: `18px`, peso 600;
- texto padrão: `16px`, linha entre 1.5 e 1.6;
- texto auxiliar: `14px`;
- legenda: entre `12px` e `14px`.

Evite texto menor que `12px`, frases inteiras em maiúsculas e excesso de pesos tipográficos.

### Espaçamento

Adote escala baseada em múltiplos de 8px:

- 4px para ajuste mínimo;
- 8px para espaço pequeno;
- 16px para espaço padrão;
- 24px entre grupos;
- 32px entre seções;
- 40px ou 48px para grandes separações;
- 64px em blocos principais quando necessário.

### Botões

- primário: fundo `#1351B4`, texto branco, altura mínima aproximada de 40px;
- primário em hover: `#0C326F`;
- secundário: fundo branco, texto e borda azuis;
- terciário: aparência de link e fundo transparente;
- destrutivo: vermelho e confirmação para ação irreversível.

Como exclusão física não é permitida, ações administrativas devem usar rótulos como “Desativar” e “Reativar”, e não “Excluir”.

Não remova o foco visível. Ações importantes devem possuir rótulo textual; ícones isolados exigem nome acessível e, quando adequado, tooltip.

### Status de exames

Cada status deve manter o mesmo texto, cor e componente em todo o sistema.

Mapeamento visual obrigatório:

- Confirmado: fundo verde-claro, texto verde;
- Resultado disponível: fundo azul institucional suave, texto azul institucional;
- Cancelado: fundo vermelho-claro, texto vermelho;
- Em análise: fundo cinza-claro, texto cinza-escuro.

Nunca comunique status apenas por cor. Inclua sempre o texto do status e, quando útil, um ícone.

### Cabeçalho e notificações

Quando o usuário estiver autenticado, o cabeçalho deve apresentar:

- o nome do usuário;
- um ícone de sino ao lado do nome;
- badge numérica no sino quando houver notificações pendentes;
- nome acessível que informe a quantidade, por exemplo “3 notificações pendentes”;
- comportamento responsivo sem ocultar a informação essencial.

A existência do componente visual não autoriza a criação automática de um modelo de notificação.

### Breadcrumbs, alertas e ícones

- páginas internas devem usar breadcrumb acima do título;
- etapas anteriores do breadcrumb são links; a página atual não é link;
- alertas devem indicar sucesso, erro, aviso ou informação com mensagem objetiva;
- cor não pode ser o único indicador de feedback;
- mensagens críticas não devem desaparecer antes de poderem ser lidas;
- use um único padrão de ícones, simples e consistente;
- prefira recursos locais ou ícones simples em SVG aprovados no projeto;
- não adicione biblioteca de ícones sem aprovação.

---

## 12. Acessibilidade e usabilidade

Toda tela deve:

- usar HTML semântico;
- possuir `label` associado a cada campo;
- permitir navegação por teclado;
- manter foco visível;
- oferecer contraste adequado;
- apresentar erros próximos aos campos e em resumo quando necessário;
- não depender apenas de cor, posição ou ícone para transmitir significado;
- usar textos claros e orientados à ação;
- possuir títulos em ordem hierárquica;
- fornecer nomes acessíveis para controles;
- adaptar-se a telas menores sem perda de funcionalidade;
- evitar tabelas como solução única quando o conteúdo se torna ilegível em dispositivos estreitos.

A interface deve priorizar a conclusão da tarefa e não a decoração.

---

## 13. Fluxo obrigatório de trabalho do Codex

Para cada solicitação:

### Antes de editar

1. Leia este `AGENTS.md`.
2. Inspecione a estrutura do repositório e os arquivos relacionados.
3. Verifique alterações locais para não sobrescrever trabalho existente.
4. Identifique exatamente uma funcionalidade, uma tela ou um critério como escopo.
5. Liste dúvidas ou bloqueios que exigem decisão.
6. Não comece se o escopo depender de uma decisão bloqueante.

### Durante a implementação

1. Faça a menor alteração completa que atenda ao escopo aprovado.
2. Mantenha o código simples e coerente com o padrão existente.
3. Não modifique partes não relacionadas.
4. Adicione ou atualize testes no mesmo passo.
5. Atualize documentação apenas quando a mudança exigir.
6. Não adicione dependências, modelos ou campos silenciosamente.

### Antes de concluir

1. Execute os testes relevantes.
2. Execute verificações do Django, incluindo `check`, quando aplicável.
3. Verifique migrations pendentes ou inconsistentes quando houver alteração de models.
4. Revise permissões e risco de acesso a dados de terceiros.
5. Revise textos visíveis para `i18n`.
6. Revise responsividade, foco, labels, mensagens e contraste da tela alterada.
7. Analise o diff para remover alterações acidentais.

### Relatório obrigatório

Ao terminar, informe:

- escopo implementado;
- arquivos alterados;
- decisões tomadas dentro do escopo autorizado;
- testes e comandos executados;
- resultado das verificações;
- limitações ou pendências;
- próximo passo sugerido, sem iniciá-lo.

Depois do relatório, pare e aguarde validação.

---

## 14. Qualidade de código

- Siga PEP 8 e os padrões do projeto.
- Use nomes claros em português ou inglês conforme o padrão já adotado; não misture idiomas arbitrariamente.
- Evite duplicação, mas não crie abstrações prematuras.
- Mantenha funções e classes com responsabilidades claras.
- Não use `except Exception` sem tratamento e justificativa adequados.
- Não silencie erros.
- Não deixe `print`, código morto, credenciais, segredos ou dados pessoais reais no repositório.
- Use dados fictícios em testes e fixtures.
- Não dependa da ordem acidental do banco; defina ordenação quando necessária.
- Considere integridade transacional em operações que alterem mais de um registro.
- Mensagens para o usuário devem ser compreensíveis; detalhes internos pertencem aos logs, quando existirem.

---

## 15. Estratégia de testes

Cada unidade implementada deve trazer os testes diretamente relacionados.

### Prioridades

1. autorização e isolamento dos dados;
2. regras de negócio e validações;
3. fluxos principais das views;
4. API REST;
5. paginação;
6. respostas a entradas inválidas;
7. regressões.

### Regras

- não escreva teste que apenas reproduza a implementação sem validar comportamento;
- use factories ou fixtures apenas se já aprovadas ou se não introduzirem dependência externa;
- mantenha os testes independentes;
- não use CPF real;
- teste o usuário autorizado e o não autorizado;
- para cada correção de bug, adicione um teste que falharia antes da correção;
- não marque teste como ignorado para obter uma suíte verde sem justificativa e aprovação.

---

## 16. Funcionalidades opcionais

Somente considerar após RF001 a RF011, arquitetura MVT, paginação, autenticação, autorização, API REST, testes e i18n estarem implementados, funcionando e validados.

### Opcionais já previstos

- dashboard de exames para o administrador;
- exportação de exame para PDF.

A comparação de resultados de exames **não é uma funcionalidade opcional**: ela foi removida do escopo e não deve ser implementada sem uma nova solicitação explícita.

Mesmo após a conclusão dos obrigatórios, implemente um opcional por vez e aguarde aprovação. Bibliotecas adicionais para gráficos ou PDF exigem consulta prévia.

Não implemente outras sugestões antes da conclusão integral do escopo obrigatório.

---

## 17. Decisões ainda pendentes

As definições anteriores foram resolvidas. Permanece somente o ponto abaixo.

### 17.1 Detalhamento progressivo da API

Antes da implementação de cada endpoint, validar ou propor de forma incremental:

- recurso exposto;
- métodos permitidos;
- permissões por perfil;
- autenticação da API;
- versionamento;
- formato de paginação e filtros;
- comportamento de desativação via API.

Esses pontos não impedem a configuração inicial do Django REST Framework, mas impedem a exposição indiscriminada de CRUDs.

---

## 18. Ordem obrigatória de construção

A estrutura deve surgir gradualmente. Cada item abaixo é uma entrega separada e deve ser implementado, testado, apresentado e validado antes do próximo. O responsável pode alterar a ordem por solicitação explícita.

1. **Preparar o repositório e a base do projeto**
   - criar ou revisar `config`, `manage.py`, dependências mínimas e configurações básicas;
   - configurar templates, static, locale e banco de dados sem antecipar funcionalidades;
   - comprovar o funcionamento inicial do projeto com `check` e teste básico.

2. **Criar a aplicação `usuarios` e o modelo customizado de usuário**
   - definir `Usuario`, `UsuarioManager` e `AUTH_USER_MODEL` antes das migrations iniciais;
   - implementar CPF como `USERNAME_FIELD`;
   - garantir suporte a `createsuperuser` com `tipo=SERVIDOR`;
   - criar e testar as migrations iniciais.

3. **Criar a aplicação `rede_saude` e implementar `UnidadeSaude`**
   - criar somente o modelo, migration, validações e testes referentes à unidade;
   - não implementar `Profissional` no mesmo passo.

4. **Implementar `Profissional` em `rede_saude`**
   - adicionar o modelo, relacionamento com unidade, validações, migration e testes;
   - respeitar cargo obrigatório, especialidade opcional e desativação lógica.

5. **Criar a aplicação `exames` e implementar `Agendamento`**
   - criar somente o modelo, relações, migration, validações e testes do agendamento;
   - não implementar `Exame` antecipadamente.

6. **Implementar `Exame` e o fluxo de status**
   - criar o modelo e a migration;
   - implementar as transições permitidas em ponto centralizado;
   - validar a consistência entre exame e agendamento;
   - testar transições válidas, inválidas e estados finais.

7. **Configurar o Django Admin**
   - registrar e configurar usuários, unidades e profissionais;
   - atender RF007 e RF008 com listagem, busca, filtros, edição, desativação e reativação;
   - impedir exclusão física;
   - preservar o uso do painel padrão do Django.

8. **Implementar RF002 — autocadastro do cidadão**
   - criar uma única tela de cadastro;
   - validar CPF, senha e confirmação;
   - criar sempre `tipo=CIDADAO`;
   - adicionar testes de formulário, view e persistência.

9. **Implementar RF001 — login por CPF e senha**
   - criar uma única tela de login;
   - configurar autenticação, sessão, redirecionamentos e logout;
   - testar credenciais válidas, inválidas e usuário inativo.

10. **Criar o layout compartilhado**
    - implementar `base.html`, cabeçalho, rodapé, mensagens e estrutura responsiva;
    - preparar o local do nome do usuário e do sino, sem criar a lógica de notificações antes do RF006;
    - criar componentes compartilhados apenas conforme forem usados.

11. **Implementar RF003 — lista paginada de usuários**
    - restringir a usuários com perfil `SERVIDOR`;
    - implementar paginação no backend, ordenação e estado vazio;
    - criar apenas a tela necessária e seus testes.

12. **Implementar RF004 — lista de exames do cidadão**
    - exibir somente os exames do cidadão autenticado;
    - usar o componente compartilhado de status;
    - implementar paginação se o volume ou requisito aprovado exigir;
    - testar isolamento de dados e autorização.

13. **Implementar RF005 — histórico de exames**
    - criar a tela de histórico sem comparação de dados;
    - exibir resultado ou mensagem de indisponibilidade;
    - testar ordenação e isolamento por cidadão.

14. **Criar a aplicação `notificacoes` e implementar RF006**
    - definir e documentar o evento de geração autorizado;
    - criar apenas o modelo mínimo necessário;
    - implementar persistência, leitura, página de notificações, context processor, sino e badge;
    - evitar signals, tarefas em background e integrações externas, salvo aprovação.

15. **Consolidar RF009 — autenticação e autorização**
    - revisar todas as páginas e operações já implementadas;
    - confirmar restrições por perfil, objeto e usuário inativo;
    - corrigir lacunas e ampliar testes de segurança funcional.

16. **Implementar a API REST progressivamente**
    - definir o primeiro recurso com o responsável;
    - criar o subpacote `api/` apenas na aplicação correspondente;
    - adotar `/api/v1/`;
    - implementar um endpoint ou conjunto mínimo coerente por vez;
    - aplicar as mesmas regras de autorização das páginas HTML;
    - não gerar CRUDs completos automaticamente.

17. **Consolidar i18n**
    - revisar textos Python, templates e JavaScript existentes;
    - gerar e validar catálogos conforme a estratégia aprovada;
    - demonstrar ao menos um cenário de tradução funcional.

18. **Implementar RF010 — gestão operacional de agendamentos e exames**
    - atualizar `Profissional` para especializar `Usuario`, migrar os dados e configurar seu cadastro autenticável no Django Admin;
    - implementar separadamente e validar, nesta ordem: criação transacional pelo servidor, lista do profissional e detalhe com transições e resultado;
    - generalizar notificações e implementar os eventos de atribuição e espera de confirmação;
    - consolidar permissões, isolamento por objeto, navegação e testes integrados do fluxo.

19. **Consolidar RF011 e a suíte de testes**
    - revisar cobertura dos requisitos principais;
    - completar testes ausentes identificados na revisão;
    - executar a suíte completa e documentar os comandos.

20. **Revisar critérios acadêmicos e documentação**
    - confirmar MVT, paginação, autenticação, autorização, API REST, testes e i18n;
    - atualizar `README.md` e documentos em `docs/` conforme o que realmente foi implementado;
    - verificar migrations, acessibilidade, identidade visual e consistência do projeto.

21. **Avaliar funcionalidades opcionais**
    - considerar dashboard administrativo e exportação para PDF somente após todos os itens obrigatórios estarem funcionando e validados;
    - implementar apenas um opcional por vez e consultar antes de adicionar dependências.

### Regras de progressão

- não criar todas as aplicações, pastas ou telas no início;
- não agrupar dois modelos ou requisitos em uma mesma entrega apenas por conveniência;
- testes, autorização, acessibilidade, i18n aplicável e identidade visual acompanham cada etapa;
- a consolidação final não substitui as verificações realizadas durante o desenvolvimento;
- depois de cada item, emitir o relatório previsto na seção 13 e aguardar validação.

---

## 19. Definição de pronto

Uma unidade de trabalho só está pronta quando:

- atende exatamente ao escopo aprovado;
- não introduz mudanças não autorizadas;
- possui autorização adequada;
- não expõe dados de outros usuários;
- possui validação no backend;
- segue a identidade visual e os requisitos de acessibilidade aplicáveis;
- inclui testes relevantes;
- passa nas verificações executadas;
- não deixa migrations inconsistentes;
- inclui textos preparados para i18n quando aplicável;
- foi documentada no relatório final;
- está pronta para validação do responsável.

“Funciona na interface” não é suficiente se a regra puder ser burlada por URL, requisição direta ou API.

---

## 20. Conduta diante de ambiguidades

Use esta sequência:

1. identifique a ambiguidade;
2. explique por que ela afeta a implementação;
3. apresente no máximo algumas alternativas objetivas;
4. recomende uma alternativa com justificativa;
5. aguarde decisão;
6. registre a decisão no código ou documentação adequada após aprovação.

Não use suposições silenciosas para avançar.
