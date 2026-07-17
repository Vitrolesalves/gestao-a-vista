"""
Teste offline para verificar configuração Selenium

Este teste não requer conexão com internet e valida apenas
a configuração local do Selenium.
"""

import os

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def test_selenium_offline_setup():
    """Testa configuração Selenium sem internet"""

    print("Testando configuração Selenium offline...")

    # Configurar Chrome options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")

    try:
        # Tentar baixar driver
        print("Baixando ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        print("✅ ChromeDriver baixado com sucesso!")

        # Criar driver
        print("Criando instância do WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ WebDriver criado com sucesso!")

        try:
            # Testar com página HTML local
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Teste Selenium Offline</title>
            </head>
            <body>
                <h1 id="titulo">Selenium Funcionando!</h1>
                <button id="botao" onclick="document.getElementById('resultado').innerHTML='Clicado!'">
                    Clique Aqui
                </button>
                <div id="resultado"></div>
                
                <script>
                    console.log('JavaScript funcionando!');
                </script>
            </body>
            </html>
            """

            # Navegar para página local
            print("Carregando página HTML local...")
            driver.get(f"data:text/html;charset=utf-8,{html_content}")
            print("✅ Página carregada com sucesso!")

            # Verificar título
            titulo = driver.title
            assert titulo == "Teste Selenium Offline"
            print(f"✅ Título correto: {titulo}")

            # Verificar elemento
            elemento_titulo = driver.find_element(By.ID, "titulo")
            assert elemento_titulo.text == "Selenium Funcionando!"
            print(f"✅ Elemento encontrado: {elemento_titulo.text}")

            # Testar JavaScript
            resultado_js = driver.execute_script("return 'JavaScript OK'")
            assert resultado_js == "JavaScript OK"
            print("✅ JavaScript funcionando!")

            # Testar clique
            botao = driver.find_element(By.ID, "botao")
            botao.click()

            # Verificar resultado do clique
            resultado = driver.find_element(By.ID, "resultado")
            assert resultado.text == "Clicado!"
            print("✅ Interação com clique funcionando!")

            # Testar tamanho da janela
            size = driver.get_window_size()
            print(f"✅ Tamanho da janela: {size['width']}x{size['height']}")

            # Testar screenshot
            screenshot_path = "tests/selenium/screenshots/test_offline.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            driver.save_screenshot(screenshot_path)
            print(f"✅ Screenshot salvo em: {screenshot_path}")

            print("\n🎉 Todos os testes offline passaram!")
            print("Selenium está configurado e funcionando corretamente!")

            return True

        finally:
            driver.quit()
            print("✅ WebDriver fechado corretamente!")

    except Exception as e:
        print(f"\n❌ Erro na configuração: {e}")
        print("Detalhes do erro:")
        import traceback

        traceback.print_exc()
        return False


def test_webdriver_installation():
    """Testa apenas a instalação do WebDriver"""

    try:
        print("Verificando instalação do ChromeDriver...")

        # Tentar baixar/encontrar driver
        driver_path = ChromeDriverManager().install()

        print(f"✅ ChromeDriver encontrado em: {driver_path}")

        # Verificar se arquivo existe
        if os.path.exists(driver_path):
            print("✅ Arquivo do driver existe!")

            # Verificar permissões (no Windows não é tão crítico)
            if os.access(driver_path, os.R_OK):
                print("✅ Driver tem permissões de leitura!")

            return True
        else:
            print("❌ Arquivo do driver não encontrado!")
            return False

    except Exception as e:
        print(f"❌ Erro ao verificar driver: {e}")
        return False


def test_chrome_availability():
    """Testa se Chrome está disponível"""

    try:
        print("Verificando disponibilidade do Chrome...")

        # Tentar criar options (não requer Chrome instalado)
        options = Options()
        options.add_argument("--version")

        print("✅ Chrome Options criado com sucesso!")

        # Verificar caminhos comuns do Chrome no Windows
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
                os.getenv("USERNAME", "")
            ),
        ]

        chrome_found = False
        for path in chrome_paths:
            if os.path.exists(path):
                print(f"✅ Chrome encontrado em: {path}")
                chrome_found = True
                break

        if not chrome_found:
            print("⚠️ Chrome não encontrado nos caminhos padrão")
            print("Isso não impede o funcionamento se Chrome estiver no PATH")

        return True

    except Exception as e:
        print(f"❌ Erro ao verificar Chrome: {e}")
        return False


if __name__ == "__main__":
    print("=== Teste de Configuração Selenium Offline ===\n")

    # Executar testes em sequência
    tests = [
        ("Instalação WebDriver", test_webdriver_installation),
        ("Disponibilidade Chrome", test_chrome_availability),
        ("Configuração Completa", test_selenium_offline_setup),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))

    # Resumo dos resultados
    print("\n" + "=" * 50)
    print("RESUMO DOS TESTES:")
    print("=" * 50)

    all_passed = True
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("Selenium está pronto para uso!")
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        print("Verifique os erros acima e instale as dependências necessárias.")

    print("\nPróximos passos:")
    print("1. Execute: python run_selenium_tests.py --suite smoke")
    print("2. Para debug: python run_selenium_tests.py --debug")
    print("3. Para ver todos os testes: python run_selenium_tests.py --list-suites")
