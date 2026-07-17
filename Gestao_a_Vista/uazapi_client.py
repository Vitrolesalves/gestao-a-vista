"""
Cliente simples para a API da uazapi (WhatsApp), usada para notificar
responsáveis quando um turno não preenche o Livro Ata.

Docs de referência: header 'token' (instância) ou 'admintoken' (admin),
base URL 'https://{subdominio}.uazapi.com'.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def formatar_numero(numero):
    """Remove tudo que não for dígito. Garante DDI 55 (Brasil) se ausente."""
    digitos = ''.join(c for c in str(numero) if c.isdigit())
    if not digitos.startswith('55'):
        digitos = '55' + digitos
    return digitos


def enviar_whatsapp(numero, mensagem):
    """
    Envia uma mensagem de texto via uazapi.
    Retorna (sucesso: bool, detalhe: str).
    """
    base_url = getattr(settings, 'UAZAPI_BASE_URL', None)
    token = getattr(settings, 'UAZAPI_INSTANCE_TOKEN', None)

    if not base_url or not token:
        return False, 'Credenciais da uazapi não configuradas.'

    try:
        response = requests.post(
            f'{base_url}/send/text',
            headers={'token': token, 'Content-Type': 'application/json'},
            json={'number': formatar_numero(numero), 'text': mensagem},
            timeout=15,
        )
        if response.status_code >= 400:
            logger.error(f'Erro ao enviar WhatsApp via uazapi ({response.status_code}): {response.text}')
            return False, f'Erro {response.status_code}: {response.text[:200]}'
        return True, 'Mensagem enviada com sucesso.'
    except requests.RequestException as e:
        logger.error(f'Falha de conexão com a uazapi: {e}')
        return False, f'Falha de conexão: {e}'


def obter_status_instancia():
    """
    Consulta GET /instance/status: status atual da instância
    ('connected', 'connecting' ou 'disconnected') e, se em processo de
    conexão, o QR Code/código de pareamento mais recente.
    Retorna (sucesso: bool, dados: dict | detalhe: str).
    """
    base_url = getattr(settings, 'UAZAPI_BASE_URL', None)
    token = getattr(settings, 'UAZAPI_INSTANCE_TOKEN', None)

    if not base_url or not token:
        return False, 'Credenciais da uazapi não configuradas.'

    try:
        response = requests.get(
            f'{base_url}/instance/status',
            headers={'token': token},
            timeout=15,
        )
        if response.status_code >= 400:
            logger.error(f'Erro ao consultar status da uazapi ({response.status_code}): {response.text}')
            return False, f'Erro {response.status_code}: {response.text[:200]}'
        return True, response.json()
    except requests.RequestException as e:
        logger.error(f'Falha de conexão com a uazapi: {e}')
        return False, f'Falha de conexão: {e}'


def conectar_instancia():
    """
    Aciona POST /instance/connect para (re)iniciar a conexão da instância e
    obter um QR Code (base64) novo para escanear. A uazapi expira o QR Code
    em ~2 minutos, por isso deve ser chamado periodicamente enquanto
    desconectado.
    Retorna (sucesso: bool, dados: dict | detalhe: str).
    """
    base_url = getattr(settings, 'UAZAPI_BASE_URL', None)
    token = getattr(settings, 'UAZAPI_INSTANCE_TOKEN', None)

    if not base_url or not token:
        return False, 'Credenciais da uazapi não configuradas.'

    try:
        response = requests.post(
            f'{base_url}/instance/connect',
            headers={'token': token, 'Content-Type': 'application/json'},
            json={},
            timeout=20,
        )
        if response.status_code >= 400:
            logger.error(f'Erro ao conectar instância uazapi ({response.status_code}): {response.text}')
            return False, f'Erro {response.status_code}: {response.text[:200]}'
        return True, response.json()
    except requests.RequestException as e:
        logger.error(f'Falha de conexão com a uazapi: {e}')
        return False, f'Falha de conexão: {e}'
