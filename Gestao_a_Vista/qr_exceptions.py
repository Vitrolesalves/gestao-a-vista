"""
Exceções específicas para o módulo de geração de QR Codes
"""


class QRCodeError(Exception):
    """Exceção base para erros relacionados a QR Codes"""

    pass


class QRCodeValidationError(QRCodeError):
    """Erro de validação de dados de entrada"""

    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"Erro de validação no campo '{field}': {message}")


class QRCodeGenerationError(QRCodeError):
    """Erro durante a geração do QR Code"""

    def __init__(self, message, original_error=None):
        self.original_error = original_error
        super().__init__(f"Erro na geração do QR Code: {message}")


class QRCodeImageError(QRCodeError):
    """Erro no processamento de imagens (logos, etc.)"""

    def __init__(self, message, file_path=None):
        self.file_path = file_path
        super().__init__(f"Erro no processamento de imagem: {message}")


class QRCodeConfigurationError(QRCodeError):
    """Erro de configuração do módulo QR Code"""

    def __init__(self, setting, message):
        self.setting = setting
        super().__init__(f"Erro de configuração '{setting}': {message}")


class QRCodeDatabaseError(QRCodeError):
    """Erro relacionado a operações de banco de dados"""

    def __init__(self, message, query=None):
        self.query = query
        super().__init__(f"Erro de banco de dados: {message}")


class QRCodePermissionError(QRCodeError):
    """Erro de permissão de acesso"""

    def __init__(self, user, action):
        self.user = user
        self.action = action
        super().__init__(f"Usuário '{user}' não tem permissão para '{action}'")
