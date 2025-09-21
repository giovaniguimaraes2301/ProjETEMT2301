@echo off
echo ==========================================
echo     VITALTECH - INSTALACAO AUTOMATIZADA
echo ==========================================
echo.

echo [1/5] Verificando Python...
python --version
if errorlevel 1 (
    echo ERRO: Python nao encontrado! Instale Python 3.10+ primeiro.
    pause
    exit /b 1
)

echo.
echo [2/5] Instalando dependencias do backend...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias Python!
    pause
    exit /b 1
)

echo.
echo [3/5] Configurando backend para execucao local...
echo REACT_APP_BACKEND_URL=http://localhost:8001 > ..\frontend\.env
echo MONGO_URL=mongodb://localhost:27017 > .env
echo DB_NAME=vitaltech_local >> .env
echo CORS_ORIGINS=* >> .env
echo GEMINI_API_KEY=AIzaSyBFFX8AZlYiWnw0OLP9ekdaWKGP0dASbn4 >> .env

echo.
echo [4/5] Verificando Node.js e instalando dependencias frontend...
cd ..\frontend
node --version
if errorlevel 1 (
    echo AVISO: Node.js nao encontrado! Instale Node.js 18+ primeiro.
    echo Download: https://nodejs.org/
    pause
)

npm --version
if not errorlevel 1 (
    echo Usando npm...
    npm install
) else (
    echo ERRO: npm nao encontrado!
    pause
    exit /b 1
)

echo.
echo [5/5] Criando scripts de execucao...
cd ..

echo @echo off > start_backend.bat
echo echo Iniciando VitalTech Backend... >> start_backend.bat
echo cd backend >> start_backend.bat
echo python server.py >> start_backend.bat
echo pause >> start_backend.bat

echo @echo off > start_frontend.bat
echo echo Iniciando VitalTech Frontend... >> start_frontend.bat
echo cd frontend >> start_frontend.bat
echo npm start >> start_frontend.bat
echo pause >> start_frontend.bat

echo @echo off > start_esp32_bridge.bat
echo echo Iniciando ESP32 Bridge (Simulacao)... >> start_esp32_bridge.bat
echo python ble_bridge.py --simulate --api-url "http://localhost:8001/api" >> start_esp32_bridge.bat
echo pause >> start_esp32_bridge.bat

echo.
echo ==========================================
echo        INSTALACAO CONCLUIDA!
echo ==========================================
echo.
echo PROXIMOS PASSOS:
echo 1. Execute: start_backend.bat (para iniciar o servidor)
echo 2. Execute: start_frontend.bat (para iniciar o site)
echo 3. Acesse: http://localhost:3000
echo.
echo OPCIONAL:
echo 4. Execute: start_esp32_bridge.bat (para simular dados ESP32)
echo.
echo IMPORTANTE: MongoDB deve estar rodando em localhost:27017
echo Se nao tiver MongoDB, use MongoDB Atlas (cloud).
echo.
pause