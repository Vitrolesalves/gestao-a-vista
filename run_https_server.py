#!/usr/bin/env python
"""
Script para executar o servidor Django com suporte HTTPS no desenvolvimento.
Gera certificados auto-assinados temporários se necessário.
"""

import os
import subprocess
import sys
from pathlib import Path


def generate_self_signed_cert():
    """Gera certificados auto-assinados para desenvolvimento"""
    cert_dir = Path("certs")
    cert_dir.mkdir(exist_ok=True)

    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"

    if cert_file.exists() and key_file.exists():
        print("✓ Certificados já existem")
        return str(cert_file), str(key_file)

    print("Gerando certificados auto-assinados...")

    try:
        # Comando OpenSSL para gerar certificado auto-assinado
        cmd = [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:4096",
            "-keyout",
            str(key_file),
            "-out",
            str(cert_file),
            "-days",
            "365",
            "-nodes",
            "-subj",
            "/C=BR/ST=SP/L=SaoPaulo/O=Development/CN=localhost",
        ]

        subprocess.run(cmd, check=True, capture_output=True)
        print("✓ Certificados gerados com sucesso")
        return str(cert_file), str(key_file)

    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao gerar certificados: {e}")
        print("Instale o OpenSSL ou use o servidor HTTP normal")
        return None, None
    except FileNotFoundError:
        print("✗ OpenSSL não encontrado")
        print("Instale o OpenSSL ou use: python manage.py runserver")
        return None, None


def run_https_server():
    """Executa o servidor Django com HTTPS"""
    cert_file, key_file = generate_self_signed_cert()

    if not cert_file or not key_file:
        print("Executando servidor HTTP normal...")
        os.system("python manage.py runserver 0.0.0.0:8000")
        return

    print("Iniciando servidor HTTPS...")
    print("Acesse: https://localhost:8000")
    print(
        "Nota: Você verá um aviso de segurança (normal para certificados auto-assinados)"
    )

    # Executar servidor com SSL
    cmd = [
        sys.executable,
        "manage.py",
        "runserver_plus",
        "--cert-file",
        cert_file,
        "--key-file",
        key_file,
        "0.0.0.0:8000",
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("✗ Erro ao executar servidor HTTPS")
        print("Tentando instalar django-extensions...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "django-extensions"],
                check=True,
            )
            print("✓ django-extensions instalado")
            print("Adicione 'django_extensions' ao INSTALLED_APPS em settings.py")
            print("Depois execute novamente: python run_https_server.py")
        except subprocess.CalledProcessError:
            print("✗ Não foi possível instalar django-extensions")
            print("Execute manualmente: pip install django-extensions")


if __name__ == "__main__":
    print("=== Servidor Django HTTPS ===")
    print()

    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        print("Executando servidor HTTP normal...")
        os.system("python manage.py runserver 0.0.0.0:8000")
    else:
        run_https_server()
