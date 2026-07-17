"""
Serviço refatorado para geração de QR Codes com tratamento robusto de exceções
"""
import base64
import json
import os
import time
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import qrcode
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from PIL import Image, ImageDraw, ImageFont

from .models import Estrutura
from .qr_exceptions import (QRCodeConfigurationError, QRCodeDatabaseError,
                            QRCodeGenerationError, QRCodeImageError,
                            QRCodePermissionError, QRCodeValidationError)
from .qr_logger import qr_logger
from .qr_validators import QRCodeValidator


class QRCodeService:
    """Serviço para geração de QR Codes com tratamento robusto de erros"""

    def __init__(self):
        self.validator = QRCodeValidator()
        self.logger = qr_logger

        # Configurações padrão
        self.default_qr_config = {
            "version": 1,
            "error_correction": qrcode.constants.ERROR_CORRECT_L,
            "box_size": 10,
            "border": 4,
        }

        self.image_config = {
            "final_size": (300, 400),
            "background_color": "white",
            "border_width": 2,
            "border_color": "black",
        }

    def generate_qr_codes(
        self, request_data: Dict[str, Any], user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Gera QR Codes com tratamento completo de exceções

        Args:
            request_data: Dados da requisição validados
            user_id: ID do usuário (opcional)

        Returns:
            Dict com resultado da geração

        Raises:
            QRCodeValidationError: Erro de validação
            QRCodeGenerationError: Erro na geração
            QRCodeDatabaseError: Erro de banco de dados
        """
        start_time = time.time()

        try:
            # Log início da operação
            self.logger.log_request_start(user_id, request_data)

            # Validar dados de entrada
            validated_data = self._validate_request_data(request_data)

            # Buscar estruturas no banco de dados
            estruturas_map = self._fetch_estruturas(validated_data["locations"])

            # Gerar QR Codes para cada local
            qr_codes = []
            for location in validated_data["locations"]:
                qr_code_data = self._generate_single_qr_code(
                    location, validated_data, estruturas_map.get(location["id"])
                )
                qr_codes.append(qr_code_data)

            # Log sucesso
            generation_time = time.time() - start_time
            self.logger.log_generation_success(
                user_id, validated_data["cr_number"], len(qr_codes), generation_time
            )

            return {
                "success": True,
                "qr_codes": qr_codes,
                "generation_time": round(generation_time, 3),
                "total_codes": len(qr_codes),
            }

        except QRCodeValidationError as e:
            self.logger.log_validation_error(e.field, e.message, user_id)
            raise

        except QRCodeDatabaseError as e:
            self.logger.log_generation_error("database", str(e), user_id)
            raise

        except QRCodeGenerationError as e:
            self.logger.log_generation_error("generation", str(e), user_id)
            raise

        except Exception as e:
            # Log erro inesperado
            self.logger.log_generation_error("unexpected", str(e), user_id)
            raise QRCodeGenerationError(f"Erro inesperado na geração: {str(e)}", e)

    def _validate_request_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida dados da requisição"""
        try:
            return self.validator.validate_request_data(data)
        except QRCodeValidationError:
            raise
        except Exception as e:
            raise QRCodeValidationError(
                "request", f"Erro na validação dos dados: {str(e)}"
            )

    def _fetch_estruturas(
        self, locations: List[Dict[str, Any]]
    ) -> Dict[int, Optional["Estrutura"]]:
        """
        Busca estruturas no banco de dados de forma otimizada

        Args:
            locations: Lista de locais validados

        Returns:
            Mapa de ID -> Estrutura (ou None se não encontrada)
        """
        query_start = time.time()

        try:
            # Extrair IDs únicos
            location_ids = [loc["id"] for loc in locations]

            # Query otimizada - buscar todos de uma vez
            with transaction.atomic():
                estruturas = Estrutura.objects.filter(
                    id__in=location_ids
                ).select_related()
                estruturas_dict = {est.id: est for est in estruturas}

            # Log da query
            query_time = time.time() - query_start
            self.logger.log_database_query(
                "SELECT", "Estrutura", query_time, len(estruturas_dict)
            )

            # Mapear todos os IDs (incluindo os não encontrados como None)
            result = {}
            for location_id in location_ids:
                result[location_id] = estruturas_dict.get(location_id)

            return result

        except Exception as e:
            raise QRCodeDatabaseError(f"Erro ao buscar estruturas: {str(e)}")

    def _generate_single_qr_code(
        self,
        location: Dict[str, Any],
        validated_data: Dict[str, Any],
        estrutura: Optional["Estrutura"],
    ) -> Dict[str, Any]:
        """
        Gera um único QR Code para um local

        Args:
            location: Dados do local validados
            validated_data: Todos os dados validados da requisição
            estrutura: Estrutura encontrada no banco (ou None)

        Returns:
            Dict com dados do QR Code gerado
        """
        try:
            # Determinar conteúdo do QR Code
            qr_content = self._build_qr_content(location, validated_data, estrutura)

            # Sanitizar conteúdo
            qr_content = self.validator.sanitize_qr_data(qr_content)

            # Gerar imagem do QR Code
            qr_image = self._create_qr_image(qr_content)

            # Criar layout final com logos
            final_image = self._create_final_layout(qr_image, location, validated_data)

            # Converter para base64
            image_base64 = self._image_to_base64(final_image)

            return {
                "location_id": location["id"],
                "location_name": location["displayName"],
                "qr_data": qr_content,
                "image": image_base64,
                "has_estrutura": estrutura is not None,
                "estrutura_id": estrutura.id if estrutura else None,
            }

        except Exception as e:
            raise QRCodeGenerationError(
                f"Erro ao gerar QR Code para local '{location['displayName']}': {str(e)}",
                e,
            )

    def _build_qr_content(
        self,
        location: Dict[str, Any],
        validated_data: Dict[str, Any],
        estrutura: Optional["Estrutura"],
    ) -> str:
        """Constrói o conteúdo do QR Code"""

        # Se estrutura tem QR Code próprio, usar ele
        if estrutura and estrutura.qrcode and estrutura.qrcode.strip():
            qr_content = estrutura.qrcode.strip()
            self.logger.debug(
                "Using existing QR code from estrutura",
                location_id=location["id"],
                estrutura_id=estrutura.id,
            )
        else:
            # Gerar conteúdo padrão
            qr_content = f"CR: {validated_data['cr_number']} | Serviço: {validated_data['service']} | Local: {location['displayName']}"

            # Adicionar ambiente se disponível
            if location.get("ambiente"):
                qr_content += f" | Ambiente: {location['ambiente']}"

            self.logger.debug(
                "Generated default QR content",
                location_id=location["id"],
                content_length=len(qr_content),
            )

        return qr_content

    def _create_qr_image(self, qr_content: str) -> Image.Image:
        """Cria a imagem base do QR Code"""
        try:
            qr = qrcode.QRCode(**self.default_qr_config)
            qr.add_data(qr_content)
            qr.make(fit=True)

            qr_image = qr.make_image(fill_color="black", back_color="white")

            self.logger.debug(
                "QR code image created",
                image_size=qr_image.size,
                content_length=len(qr_content),
            )

            return qr_image

        except Exception as e:
            raise QRCodeGenerationError(f"Erro ao criar imagem do QR Code: {str(e)}", e)

    def _create_final_layout(
        self,
        qr_image: Image.Image,
        location: Dict[str, Any],
        validated_data: Dict[str, Any],
    ) -> Image.Image:
        """Cria o layout final com logos e bordas"""
        try:
            processing_start = time.time()

            # Criar imagem final
            final_image = Image.new(
                "RGB",
                self.image_config["final_size"],
                self.image_config["background_color"],
            )
            draw = ImageDraw.Draw(final_image)

            # Adicionar borda
            border_coords = [
                (5, 5),
                (
                    self.image_config["final_size"][0] - 5,
                    self.image_config["final_size"][1] - 5,
                ),
            ]
            draw.rectangle(
                border_coords,
                outline=self.image_config["border_color"],
                width=self.image_config["border_width"],
            )

            # Redimensionar e posicionar QR Code
            qr_size = (200, 200)
            qr_image_resized = qr_image.resize(qr_size, Image.Resampling.LANCZOS)
            qr_position = (50, 100)  # Centralizado
            final_image.paste(qr_image_resized, qr_position)

            # Tentar carregar e adicionar logos
            self._add_logos_to_image(final_image, draw, validated_data)

            # Adicionar texto
            self._add_text_to_image(final_image, draw, location, validated_data)

            processing_time = time.time() - processing_start
            self.logger.log_image_processing(
                "final_layout_creation",
                processing_time=processing_time,
                image_size=final_image.size,
            )

            return final_image

        except Exception as e:
            raise QRCodeImageError(f"Erro ao criar layout final: {str(e)}")

    def _add_logos_to_image(
        self,
        final_image: Image.Image,
        draw: ImageDraw.Draw,
        validated_data: Dict[str, Any],
    ):
        """Adiciona logos à imagem (com tratamento de erros)"""
        try:
            # Tentar carregar logo OpsVista
            app_logo = self._load_ops_vista_logo()
            if app_logo:
                # Redimensionar e posicionar
                logo_size = (60, 60)
                app_logo_resized = app_logo.resize(logo_size, Image.Resampling.LANCZOS)
                final_image.paste(app_logo_resized, (20, 20))

                self.logger.debug("OpsVista logo added successfully")

            # TODO: Adicionar logo do serviço se disponível

        except Exception as e:
            # Log erro mas não falha a geração
            self.logger.log_image_processing(
                "logo_loading_failed", processing_time=0, image_path=None
            )
            self.logger.warning(f"Erro ao carregar logos: {str(e)}")

    def _load_ops_vista_logo(self) -> Optional[Image.Image]:
        """Carrega logo OpsVista com tratamento de erros"""
        possible_paths = [
            os.path.join(
                settings.BASE_DIR, "Gestao_a_Vista", "static", "images", "visa.png"
            ),
            os.path.join(
                settings.BASE_DIR, "Gestao_a_Vista", "static", "images", "logo.png"
            ),
            os.path.join(
                settings.BASE_DIR, "Gestao_a_Vista", "templates", "image", "visa.png"
            ),
            os.path.join(
                settings.BASE_DIR, "Gestao_a_Vista", "templates", "image", "logo.png"
            ),
        ]

        for logo_path in possible_paths:
            try:
                if os.path.exists(logo_path):
                    logo = Image.open(logo_path)
                    self.logger.debug(
                        "OpsVista logo loaded",
                        image_path=logo_path,
                        image_size=logo.size,
                    )
                    return logo
            except Exception as e:
                self.logger.debug(f"Failed to load logo from {logo_path}: {str(e)}")
                continue

        self.logger.warning("OpsVista logo not found in any expected location")
        return None

    def _add_text_to_image(
        self,
        final_image: Image.Image,
        draw: ImageDraw.Draw,
        location: Dict[str, Any],
        validated_data: Dict[str, Any],
    ):
        """Adiciona texto à imagem"""
        try:
            # Texto do CR
            cr_text = f"CR: {validated_data['cr_number']}"
            draw.text((20, 320), cr_text, fill="black")

            # Texto do serviço
            service_text = f"Serviço: {validated_data['service']}"
            draw.text((20, 340), service_text, fill="black")

            # Texto do local
            location_text = f"Local: {location['displayName']}"
            draw.text((20, 360), location_text, fill="black")

        except Exception as e:
            self.logger.warning(f"Erro ao adicionar texto: {str(e)}")

    def _image_to_base64(self, image: Image.Image) -> str:
        """Converte imagem para base64"""
        try:
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            self.logger.debug(
                "Image converted to base64",
                image_size=image.size,
                base64_length=len(img_str),
            )

            return img_str

        except Exception as e:
            raise QRCodeImageError(f"Erro ao converter imagem para base64: {str(e)}")


# Instância global do serviço
qr_service = QRCodeService()


@login_required
@require_POST
def generate_qr_code_improved(request):
    """
    Endpoint melhorado para geração de QR Codes com tratamento robusto de exceções
    """
    try:
        # Verificar método
        if request.method != "POST":
            return JsonResponse(
                {
                    "success": False,
                    "error": "Método não permitido",
                    "error_type": "method_not_allowed",
                },
                status=405,
            )

        # Obter ID do usuário
        user_id = request.user.id if request.user.is_authenticated else None

        # Parse dos dados JSON
        try:
            if request.content_type == "application/json":
                data = json.loads(request.body.decode("utf-8"))
            else:
                data = json.loads(request.POST.get("data", "{}"))
        except json.JSONDecodeError as e:
            qr_logger.log_validation_error("json", f"JSON inválido: {str(e)}", user_id)
            return JsonResponse(
                {
                    "success": False,
                    "error": "Dados JSON inválidos",
                    "error_type": "invalid_json",
                    "details": str(e),
                },
                status=400,
            )

        # Gerar QR Codes usando o serviço
        result = qr_service.generate_qr_codes(data, user_id)

        return JsonResponse(result)

    except QRCodeValidationError as e:
        return JsonResponse(
            {
                "success": False,
                "error": e.message,
                "error_type": "validation_error",
                "field": e.field,
            },
            status=400,
        )

    except QRCodeDatabaseError as e:
        return JsonResponse(
            {
                "success": False,
                "error": "Erro no banco de dados",
                "error_type": "database_error",
                "details": str(e) if settings.DEBUG else None,
            },
            status=500,
        )

    except QRCodeGenerationError as e:
        return JsonResponse(
            {
                "success": False,
                "error": "Erro na geração do QR Code",
                "error_type": "generation_error",
                "details": str(e) if settings.DEBUG else None,
            },
            status=500,
        )

    except QRCodePermissionError as e:
        return JsonResponse(
            {
                "success": False,
                "error": "Permissão negada",
                "error_type": "permission_error",
                "details": str(e),
            },
            status=403,
        )

    except Exception as e:
        # Log erro inesperado
        qr_logger.log_generation_error("unexpected", str(e), user_id)

        return JsonResponse(
            {
                "success": False,
                "error": "Erro interno do servidor",
                "error_type": "internal_error",
                "details": str(e) if settings.DEBUG else None,
            },
            status=500,
        )
