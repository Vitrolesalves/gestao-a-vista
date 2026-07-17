#!/usr/bin/env python3
"""
Script de teste para verificar se as fontes estão funcionando corretamente
no gerador de etiquetas do Sistema de Gestão à Vista.
"""

import os
import sys
import platform
from PIL import Image, ImageDraw, ImageFont

def test_font_loading():
    """Testa o carregamento das fontes do sistema"""
    print("🔤 Testando carregamento de fontes...")
    print(f"Sistema operacional: {platform.system()}")
    print(f"Arquitetura: {platform.machine()}")
    print()
    
    # Caminhos de fontes por sistema
    font_paths = {
        'Linux': [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
            '/usr/share/fonts/TTF/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf',
            '/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf',
            '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
        ],
        'Windows': [
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/arialbd.ttf',
            'C:/Windows/Fonts/calibri.ttf',
            'C:/Windows/Fonts/calibrib.ttf',
        ],
        'Darwin': [
            '/System/Library/Fonts/Arial.ttf',
            '/System/Library/Fonts/Arial Bold.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
        ]
    }
    
    system = platform.system()
    paths = font_paths.get(system, font_paths['Linux'])
    
    found_fonts = []
    
    print("📁 Verificando arquivos de fonte...")
    for path in paths:
        if os.path.exists(path):
            print(f"  ✅ {path}")
            found_fonts.append(path)
        else:
            print(f"  ❌ {path}")
    
    print()
    
    if not found_fonts:
        print("⚠️  Nenhuma fonte TrueType encontrada!")
        print("Execute o script de instalação: ./scripts/install-fonts-linux.sh")
        return False
    
    print("🔧 Testando carregamento com PIL/Pillow...")
    
    successful_fonts = []
    
    for font_path in found_fonts:
        try:
            # Testar diferentes tamanhos
            for size in [20, 24, 26]:
                font = ImageFont.truetype(font_path, size)
                print(f"  ✅ {os.path.basename(font_path)} - Tamanho {size}px")
            successful_fonts.append(font_path)
            break  # Se uma fonte funcionar, não precisamos testar todas
        except Exception as e:
            print(f"  ❌ {os.path.basename(font_path)} - Erro: {e}")
    
    print()
    
    if successful_fonts:
        print(f"✅ Fontes funcionais encontradas: {len(successful_fonts)}")
        return True
    else:
        print("❌ Nenhuma fonte pôde ser carregada!")
        return False

def test_label_generation():
    """Testa a geração de uma etiqueta de exemplo"""
    print("🏷️  Testando geração de etiqueta...")
    
    try:
        # Criar imagem de teste (tamanho de etiqueta A4348)
        width, height = 365, 201  # 31x17mm em 300 DPI
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Desenhar borda
        draw.rectangle([0, 0, width-1, height-1], outline='black', width=1)
        
        # Tentar carregar fonte
        font_loaded = False
        font_normal = None
        font_bold = None
        
        # Lista de fontes para testar
        test_fonts = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            'C:/Windows/Fonts/arial.ttf',
            '/System/Library/Fonts/Arial.ttf'
        ]
        
        for font_path in test_fonts:
            if os.path.exists(font_path):
                try:
                    font_normal = ImageFont.truetype(font_path, 24)
                    font_bold = ImageFont.truetype(font_path.replace('.ttf', '-Bold.ttf'), 26)
                    if not os.path.exists(font_path.replace('.ttf', '-Bold.ttf')):
                        font_bold = font_normal  # Usar normal se bold não existir
                    font_loaded = True
                    print(f"  ✅ Fonte carregada: {os.path.basename(font_path)}")
                    break
                except Exception as e:
                    print(f"  ⚠️  Erro ao carregar {os.path.basename(font_path)}: {e}")
                    continue
        
        if not font_loaded:
            print("  ⚠️  Usando fonte padrão do sistema")
            font_normal = ImageFont.load_default()
            font_bold = font_normal
        
        # Dados de teste
        test_data = {
            'data': '2025-11-05',
            'cr': '16711',
            'patrimonio': '123456',
            'gerente': 'João Silva',
            'responsavel': 'Maria Santos',
            'imei': '123456789012345',
            'anotacoes': 'Teste OK'
        }
        
        # Desenhar texto de teste
        y_pos = 8
        line_height = 22
        
        # Data (bold)
        draw.text((8, y_pos), f"Data: {test_data['data']}", fill='black', font=font_bold)
        y_pos += line_height
        
        # Outros campos
        fields = [
            ('CR', test_data['cr']),
            ('Pat', test_data['patrimonio'][:12]),
            ('Ger', test_data['gerente'][:15]),
            ('Resp', test_data['responsavel'][:13]),
            ('IMEI', test_data['imei'][:15]),
            ('Obs', test_data['anotacoes'][:13])
        ]
        
        for label, value in fields:
            if y_pos + line_height <= height - 8:  # Verificar se cabe
                draw.text((8, y_pos), f"{label}: {value}", fill='black', font=font_normal)
                y_pos += line_height
        
        # Salvar imagem de teste
        test_file = 'test_etiqueta.png'
        image.save(test_file)
        
        print(f"  ✅ Etiqueta de teste gerada: {test_file}")
        print(f"  📏 Dimensões: {width}x{height}px (31x17mm)")
        
        # Verificar tamanho do arquivo
        file_size = os.path.getsize(test_file)
        print(f"  📦 Tamanho do arquivo: {file_size} bytes")
        
        if file_size > 1000:  # Arquivo muito pequeno pode indicar problema
            print("  ✅ Arquivo gerado com sucesso!")
            return True
        else:
            print("  ⚠️  Arquivo muito pequeno, pode haver problemas")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro na geração: {e}")
        return False

def test_freetype_support():
    """Testa se o FreeType está habilitado no Pillow"""
    print("🔧 Verificando suporte FreeType no Pillow...")
    
    try:
        from PIL import features
        
        # Verificar recursos disponíveis
        freetype_enabled = features.check('freetype2')
        print(f"  FreeType2: {'✅ Habilitado' if freetype_enabled else '❌ Desabilitado'}")
        
        # Verificar outros recursos úteis
        jpeg_enabled = features.check('jpg')
        png_enabled = features.check('png')
        
        print(f"  JPEG: {'✅ Habilitado' if jpeg_enabled else '❌ Desabilitado'}")
        print(f"  PNG: {'✅ Habilitado' if png_enabled else '❌ Desabilitado'}")
        
        print()
        
        if freetype_enabled:
            print("✅ FreeType está habilitado - Fontes TrueType devem funcionar")
            return True
        else:
            print("❌ FreeType não está habilitado - Apenas fontes bitmap funcionarão")
            print("Instale libfreetype6-dev (Ubuntu) ou freetype-devel (CentOS)")
            print("Depois reinstale Pillow: pip install --upgrade --force-reinstall Pillow")
            return False
            
    except ImportError:
        print("  ❌ Módulo PIL.features não encontrado")
        return False
    except Exception as e:
        print(f"  ❌ Erro ao verificar FreeType: {e}")
        return False

def main():
    """Função principal do teste"""
    print("🚀 Sistema de Teste de Fontes - Gestão à Vista")
    print("=" * 50)
    print()
    
    # Executar testes
    tests = [
        ("Suporte FreeType", test_freetype_support),
        ("Carregamento de Fontes", test_font_loading),
        ("Geração de Etiqueta", test_label_generation)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"🧪 Executando: {test_name}")
        print("-" * 30)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
        
        print()
    
    # Resumo dos resultados
    print("📊 Resumo dos Testes")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print()
    print(f"Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! O gerador de etiquetas deve funcionar corretamente.")
        return 0
    elif passed > 0:
        print("⚠️  Alguns testes falharam. Verifique as mensagens acima.")
        return 1
    else:
        print("❌ Todos os testes falharam. Execute o script de instalação de fontes.")
        return 2

if __name__ == "__main__":
    sys.exit(main())
