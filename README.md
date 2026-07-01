# ExameSUS

Plataforma acadêmica para gestão de exames no Sistema Único de Saúde, construída
como um monólito modular com Django.

## Requisitos

- Python 3.13.14
- Django 6.0.6
- Django REST Framework 3.17.1

## Preparação do ambiente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

O projeto lê configurações sensíveis diretamente do ambiente. Para desenvolvimento,
há valores locais explícitos. Antes de publicar a aplicação, defina ao menos:

```powershell
$env:DJANGO_SECRET_KEY = "uma-chave-secreta-forte"
$env:DJANGO_DEBUG = "false"
$env:DJANGO_ALLOWED_HOSTS = "seu-dominio.example"
```

## Banco de dados e execução

```powershell
python manage.py migrate
python manage.py runserver
```

O painel administrativo fica disponível em `http://127.0.0.1:8000/admin/`.

## Verificações

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

Consulte o `AGENTS.md` antes de implementar qualquer nova entrega.

