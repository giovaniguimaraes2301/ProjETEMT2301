@echo off
echo ==========================================
echo     VITALTECH ESP32 - SETUP WINDOWS
echo ==========================================
echo.

echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python nao encontrado!
    echo.
    echo 📥 Por favor, instale Python primeiro:
    echo 🌐 Acesse: https://python.org
    echo ✅ Marque a opcao "Add Python to PATH" durante a instalacao
    echo.
    pause
    start https://python.org
    exit /b 1
)
echo ✅ Python encontrado!

echo.
echo [2/4] Verificando Bluetooth...
powershell -Command "Get-Service -Name 'bthserv' | Where-Status -eq 'Running'" >nul 2>&1
if errorlevel 1 (
    echo ❌ AVISO: Servico Bluetooth pode nao estar ativo
    echo 📱 Ative o Bluetooth nas configuracoes do Windows
) else (
    echo ✅ Bluetooth ativo!
)

echo.
echo [3/4] Instalando bibliotecas Python...
pip install bleak requests
if errorlevel 1 (
    echo ❌ ERRO: Falha ao instalar bibliotecas!
    echo.
    echo 🔧 Tente executar como Administrador
    echo    Clique com botao direito no arquivo e "Executar como administrador"
    pause
    exit /b 1
)
echo ✅ Bibliotecas instaladas!

echo.
echo [4/4] Baixando bridge ESP32...
curl -o ble_bridge_esp32.py https://vitaltech-monitor.preview.emergentagent.com/ble_bridge_esp32.py >nul 2>&1
if errorlevel 1 (
    echo ❌ AVISO: Nao foi possivel baixar automaticamente
    echo 📋 Copie o codigo manualmente do site
) else (
    echo ✅ Bridge baixado!
)

echo.
echo ==========================================
echo        INSTALACAO CONCLUIDA!
echo ==========================================
echo.
echo 🎯 PROXIMOS PASSOS:
echo.
echo 1. 🔌 Ligue seu ESP32 (USB ou fonte 5V)
echo 2. 🚀 Execute: python ble_bridge_esp32.py
echo 3. 🌐 Acesse: https://vitaltech-monitor.preview.emergentagent.com
echo 4. 📊 Veja os dados em tempo real!
echo.
echo 📋 COMANDOS UTEIS:
echo    python ble_bridge_esp32.py    - Conectar ao ESP32
echo    pip install bleak requests    - Reinstalar bibliotecas
echo.
echo ❓ PROBLEMAS? Veja a secao "Problemas comuns" no site
echo.
pause