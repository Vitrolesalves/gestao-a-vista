#!/bin/bash

# Script para instalar fontes necessárias no Linux para o gerador de etiquetas
# Gestão à Vista - Sistema de Etiquetas

set -e

echo "🔤 Instalando fontes para o Sistema de Gestão à Vista..."

# Detectar distribuição Linux
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
fi

# Função para Ubuntu/Debian
install_ubuntu_debian() {
    echo "📦 Detectado Ubuntu/Debian - Instalando fontes..."
    
    # Atualizar repositórios
    sudo apt-get update
    
    # Instalar fontes essenciais
    sudo apt-get install -y \
        fonts-dejavu \
        fonts-liberation \
        fonts-ubuntu \
        fonts-noto \
        fontconfig \
        libfreetype6-dev \
        libjpeg-dev \
        libpng-dev
    
    echo "✅ Fontes Ubuntu/Debian instaladas com sucesso!"
}

# Função para CentOS/RHEL/Fedora
install_centos_rhel() {
    echo "📦 Detectado CentOS/RHEL/Fedora - Instalando fontes..."
    
    # Detectar gerenciador de pacotes
    if command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
    else
        echo "❌ Gerenciador de pacotes não encontrado!"
        exit 1
    fi
    
    # Instalar fontes essenciais
    sudo $PKG_MANAGER install -y \
        dejavu-sans-fonts \
        liberation-fonts \
        google-noto-fonts \
        fontconfig \
        freetype-devel \
        libjpeg-devel \
        libpng-devel
    
    echo "✅ Fontes CentOS/RHEL/Fedora instaladas com sucesso!"
}

# Função para Alpine Linux
install_alpine() {
    echo "📦 Detectado Alpine Linux - Instalando fontes..."
    
    # Instalar fontes essenciais
    sudo apk add --no-cache \
        font-dejavu \
        font-liberation \
        font-noto \
        fontconfig \
        freetype-dev \
        jpeg-dev \
        libpng-dev
    
    echo "✅ Fontes Alpine Linux instaladas com sucesso!"
}

# Detectar e instalar baseado na distribuição
case "$OS" in
    *"Ubuntu"*|*"Debian"*)
        install_ubuntu_debian
        ;;
    *"CentOS"*|*"Red Hat"*|*"Fedora"*)
        install_centos_rhel
        ;;
    *"Alpine"*)
        install_alpine
        ;;
    *)
        echo "⚠️  Distribuição não reconhecida: $OS"
        echo "Tentando instalação genérica..."
        
        # Tentar instalação genérica
        if command -v apt-get &> /dev/null; then
            install_ubuntu_debian
        elif command -v dnf &> /dev/null || command -v yum &> /dev/null; then
            install_centos_rhel
        elif command -v apk &> /dev/null; then
            install_alpine
        else
            echo "❌ Não foi possível detectar o gerenciador de pacotes!"
            echo "Por favor, instale manualmente as seguintes fontes:"
            echo "  - DejaVu Sans"
            echo "  - Liberation Sans"
            echo "  - Ubuntu Fonts"
            echo "  - Noto Sans"
            echo "  - FreeType development libraries"
            exit 1
        fi
        ;;
esac

# Atualizar cache de fontes
echo "🔄 Atualizando cache de fontes..."
sudo fc-cache -fv

# Verificar instalação
echo "🔍 Verificando fontes instaladas..."

# Lista de fontes para verificar
FONTES_VERIFICAR=(
    "DejaVu Sans"
    "Liberation Sans"
    "Ubuntu"
    "Noto Sans"
)

FONTES_ENCONTRADAS=0

for fonte in "${FONTES_VERIFICAR[@]}"; do
    if fc-list | grep -i "$fonte" > /dev/null; then
        echo "  ✅ $fonte - Encontrada"
        ((FONTES_ENCONTRADAS++))
    else
        echo "  ❌ $fonte - Não encontrada"
    fi
done

echo ""
echo "📊 Resumo da instalação:"
echo "  Fontes encontradas: $FONTES_ENCONTRADAS/${#FONTES_VERIFICAR[@]}"

if [ $FONTES_ENCONTRADAS -gt 0 ]; then
    echo "  ✅ Instalação bem-sucedida! O gerador de etiquetas deve funcionar corretamente."
else
    echo "  ⚠️  Nenhuma fonte foi encontrada. Pode haver problemas com o gerador de etiquetas."
    echo "  Verifique se as fontes foram instaladas corretamente."
fi

echo ""
echo "🎯 Próximos passos:"
echo "  1. Reinicie o servidor Django se estiver rodando"
echo "  2. Teste o gerador de etiquetas"
echo "  3. Se ainda houver problemas, verifique os logs do Django"

echo ""
echo "📝 Para testar as fontes disponíveis, execute:"
echo "  fc-list | grep -E '(DejaVu|Liberation|Ubuntu|Noto)'"

echo ""
echo "🚀 Instalação de fontes concluída!"
