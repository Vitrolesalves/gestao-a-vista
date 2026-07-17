"""
Teste básico para verificar se a configuração Selenium está funcionando

Este arquivo contém testes simples para validar que o ambiente Selenium
está configurado corretamente e funcionando.
"""

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


@pytest.mark.selenium
def test_selenium_basic_setup():
    """Testa configuração básica do Selenium"""

    # Configurar Chrome options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Criar driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Testar navegação básica
        driver.get("https://www.google.com")

        # Verificar título
        assert "Google" in driver.title

        # Verificar se página carregou
        assert driver.current_url.startswith("https://www.google")

        print("✅ Selenium configurado corretamente!")

    finally:
        driver.quit()


@pytest.mark.selenium
def test_webdriver_manager():
    """Testa se WebDriverManager está funcionando"""

    try:
        # Baixar driver automaticamente
        driver_path = ChromeDriverManager().install()

        # Verificar se driver foi baixado
        assert driver_path is not None
        assert "chromedriver" in driver_path.lower()

        print(f"✅ WebDriverManager funcionando! Driver em: {driver_path}")

    except Exception as e:
        pytest.fail(f"Erro no WebDriverManager: {e}")


@pytest.mark.selenium
def test_chrome_headless():
    """Testa modo headless do Chrome"""

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Testar JavaScript
        driver.get(
            'data:text/html,<html><body><h1 id="test">Selenium Test</h1></body></html>'
        )

        # Verificar elemento
        element = driver.find_element(By.ID, "test")
        assert element.text == "Selenium Test"

        # Testar JavaScript
        result = driver.execute_script("return document.title")
        assert result == ""  # Página simples sem título

        # Testar tamanho da janela
        size = driver.get_window_size()
        assert size["width"] == 1920
        assert size["height"] == 1080

        print("✅ Chrome headless funcionando corretamente!")

    finally:
        driver.quit()


if __name__ == "__main__":
    # Executar testes diretamente
    print("Testando configuração Selenium...")

    try:
        test_selenium_basic_setup()
        test_webdriver_manager()
        test_chrome_headless()
        print("\n🎉 Todos os testes passaram! Selenium está pronto para uso.")

    except Exception as e:
        print(f"\n❌ Erro nos testes: {e}")
        print("Verifique se o Chrome está instalado e as dependências estão corretas.")
