"""
Middleware para lidar com tentativas de conexão HTTPS no servidor de desenvolvimento
"""
import logging

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class HTTPSRedirectMiddleware(MiddlewareMixin):
    """
    Middleware para lidar com tentativas de conexão HTTPS no desenvolvimento.
    Retorna uma resposta amigável em vez de erro 400.
    """

    def process_request(self, request):
        # Verificar se é uma tentativa de conexão HTTPS mal formada
        if hasattr(request, "META"):
            # Verificar headers que indicam tentativa HTTPS
            if request.META.get("REQUEST_METHOD") == "GET" and request.META.get(
                "PATH_INFO", ""
            ).startswith("\x16\x03"):
                logger.info(
                    "Tentativa de conexão HTTPS detectada - retornando resposta HTTP"
                )

                # Retornar resposta HTTP simples
                response_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Servidor HTTP</title>
                    <meta charset="utf-8">
                </head>
                <body>
                    <h1>Servidor de Desenvolvimento Django</h1>
                    <p>Este servidor aceita apenas conexões HTTP.</p>
                    <p>Acesse via: <a href="http://localhost:8000">http://localhost:8000</a></p>
                </body>
                </html>
                """

                return HttpResponse(
                    response_content, content_type="text/html", status=200
                )

        return None
