"""
Custom password hashers for Gestao_a_Vista
Otimizado para melhor performance mantendo segurança adequada
"""
from django.contrib.auth.hashers import PBKDF2PasswordHasher


class FastPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """
    PBKDF2 hasher otimizado com menos iterações para melhor performance
    
    Reduzido de 600.000 para 150.000 iterações
    Ainda fornece segurança adequada (OWASP recomenda mínimo de 100.000)
    """
    iterations = 150000
