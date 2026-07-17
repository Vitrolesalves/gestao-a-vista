#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para gerar ícones PWA em diferentes tamanhos
a partir do logo existente
"""
import sys
import io

# Configura encoding para UTF-8 no Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from PIL import Image
import os

# Caminho para o logo original
LOGO_PATH = "Gestao_a_Vista/static/img/logo.png"
OUTPUT_DIR = "Gestao_a_Vista/static/img"

# Tamanhos necessários para PWA
SIZES = [72, 96, 128, 144, 152, 192, 384, 512]

def generate_icons():
    """Gera ícones PWA em diferentes tamanhos"""

    if not os.path.exists(LOGO_PATH):
        print(f"❌ Logo não encontrado: {LOGO_PATH}")
        print("📝 Por favor, coloque um logo.png na pasta Gestao_a_Vista/static/img/")
        return False

    try:
        # Abre a imagem original
        original = Image.open(LOGO_PATH)
        print(f"✅ Logo carregado: {LOGO_PATH}")
        print(f"   Tamanho original: {original.size}")

        # Converte para RGBA se necessário (para transparência)
        if original.mode != 'RGBA':
            original = original.convert('RGBA')

        # Cria os ícones em diferentes tamanhos
        for size in SIZES:
            # Redimensiona mantendo a proporção
            icon = original.copy()
            icon.thumbnail((size, size), Image.Resampling.LANCZOS)

            # Cria uma imagem quadrada com fundo transparente
            square_icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))

            # Centraliza o ícone
            offset = ((size - icon.size[0]) // 2, (size - icon.size[1]) // 2)
            square_icon.paste(icon, offset, icon if icon.mode == 'RGBA' else None)

            # Salva o ícone
            output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")
            square_icon.save(output_path, 'PNG', optimize=True)
            print(f"✅ Ícone criado: icon-{size}x{size}.png")

        print("\n🎉 Todos os ícones PWA foram gerados com sucesso!")
        print(f"📁 Localização: {OUTPUT_DIR}")
        return True

    except Exception as e:
        print(f"❌ Erro ao gerar ícones: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_fallback_icon():
    """Cria um ícone de fallback caso o logo não exista"""
    print("📝 Criando ícones de fallback...")

    try:
        # Cria uma imagem simples com gradiente
        from PIL import ImageDraw, ImageFont

        for size in SIZES:
            # Cria imagem com gradiente azul
            img = Image.new('RGBA', (size, size), (30, 41, 59, 255))  # #1e293b
            draw = ImageDraw.Draw(img)

            # Adiciona um círculo branco no centro
            circle_size = int(size * 0.6)
            circle_pos = (size - circle_size) // 2
            draw.ellipse(
                [circle_pos, circle_pos, circle_pos + circle_size, circle_pos + circle_size],
                fill=(56, 189, 248, 255),  # Azul claro
                outline=None
            )

            # Salva
            output_path = os.path.join(OUTPUT_DIR, f"icon-{size}x{size}.png")
            img.save(output_path, 'PNG', optimize=True)
            print(f"✅ Ícone fallback criado: icon-{size}x{size}.png")

        print("\n✅ Ícones de fallback criados!")
        print("⚠️  Recomendação: Substitua por seu logo personalizado posteriormente")
        return True

    except Exception as e:
        print(f"❌ Erro ao criar ícones de fallback: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Gerador de Ícones PWA")
    print("=" * 50)

    # Verifica se o diretório de saída existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Tenta gerar ícones a partir do logo
    if not generate_icons():
        print("\n⚠️  Gerando ícones de fallback...")
        create_fallback_icon()

    print("\n" + "=" * 50)
    print("✅ Processo concluído!")
    print("\n📋 Próximos passos:")
    print("   1. Inicie o servidor: python manage.py runserver")
    print("   2. Acesse: http://localhost:8000/gestao-qualidade/")
    print("   3. No Chrome/Edge mobile: Menu > Instalar app")
    print("   4. No Safari iOS: Compartilhar > Adicionar à Tela Inicial")
