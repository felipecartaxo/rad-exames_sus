#!/usr/bin/env python
import os
import sys


def main():
    """Execute administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. Verifique se as dependências "
            "estão instaladas e se o ambiente virtual está ativo."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()

