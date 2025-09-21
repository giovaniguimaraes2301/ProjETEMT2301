#!/usr/bin/env python3
"""
Script de configuração automática do ambiente VitalTech
Funciona no Windows, Linux e macOS
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Executar comando e retornar resultado"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, 
                              capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_requirement(command, name):
    """Verificar se um pré-requisito está instalado"""
    success, output = run_command(command)
    if success:
        print(f"✅ {name}: {output.strip().split()[0] if output.strip() else 'Instalado'}")
        return True
    else:
        print(f"❌ {name}: Não encontrado")
        return False

def setup_backend():
    """Configurar backend"""
    print("\n🔧 Configurando Backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Pasta backend não encontrada")
        return False
    
    # Instalar dependências Python
    print("Instalando dependências Python...")
    success, output = run_command("pip install -r requirements.txt", cwd=backend_dir)
    if success:
        print("✅ Dependências Python instaladas")
    else:
        print(f"❌ Erro ao instalar dependências: {output}")
        return False
    
    # Configurar arquivo .env para ambiente local
    env_file = backend_dir / ".env"
    local_env = """MONGO_URL=mongodb://localhost:27017
DB_NAME=vitaltech_local
CORS_ORIGINS=*
GEMINI_API_KEY=AIzaSyBFFX8AZlYiWnw0OLP9ekdaWKGP0dASbn4
"""
    
    with open(env_file, "w") as f:
        f.write(local_env)
    print("✅ Arquivo .env configurado para ambiente local")
    
    return True

def setup_frontend():
    """Configurar frontend"""
    print("\n🎨 Configurando Frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Pasta frontend não encontrada")
        return False
    
    # Verificar se npm ou yarn está disponível
    has_yarn = check_requirement("yarn --version", "Yarn")
    has_npm = check_requirement("npm --version", "NPM")
    
    if not has_yarn and not has_npm:
        print("❌ Nem Yarn nem NPM encontrados. Instale Node.js primeiro.")
        return False
    
    # Instalar dependências
    package_manager = "yarn" if has_yarn else "npm"
    install_cmd = "yarn install" if has_yarn else "npm install"
    
    print(f"Instalando dependências com {package_manager}...")
    success, output = run_command(install_cmd, cwd=frontend_dir)
    if success:
        print("✅ Dependências frontend instaladas")
    else:
        print(f"❌ Erro ao instalar dependências: {output}")
        return False
    
    # Configurar arquivo .env para ambiente local
    env_file = frontend_dir / ".env"
    local_env = """REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
"""
    
    with open(env_file, "w") as f:
        f.write(local_env)
    print("✅ Arquivo .env configurado para ambiente local")
    
    return True

def create_startup_scripts():
    """Criar scripts de inicialização"""
    print("\n📜 Criando scripts de inicialização...")
    
    # Scripts para Windows
    backend_bat = """@echo off
echo Iniciando VitalTech Backend...
cd backend
python server.py
pause
"""
    
    frontend_bat = """@echo off
echo Iniciando VitalTech Frontend...
cd frontend
npm start
pause
"""
    
    bridge_bat = """@echo off
echo Iniciando ESP32 Bridge (Simulacao)...
python ble_bridge.py --simulate --api-url "http://localhost:8001/api"
pause
"""
    
    # Scripts para Unix (Linux/macOS)
    backend_sh = """#!/bin/bash
echo "Iniciando VitalTech Backend..."
cd backend
python3 server.py
"""
    
    frontend_sh = """#!/bin/bash
echo "Iniciando VitalTech Frontend..."
cd frontend
npm start
"""
    
    bridge_sh = """#!/bin/bash
echo "Iniciando ESP32 Bridge (Simulacao)..."
python3 ble_bridge.py --simulate --api-url "http://localhost:8001/api"
"""
    
    # Determinar plataforma e criar scripts apropriados
    if os.name == 'nt':  # Windows
        with open("start_backend.bat", "w") as f:
            f.write(backend_bat)
        with open("start_frontend.bat", "w") as f:
            f.write(frontend_bat)
        with open("start_bridge.bat", "w") as f:
            f.write(bridge_bat)
        print("✅ Scripts .bat criados para Windows")
    else:  # Unix-like
        with open("start_backend.sh", "w") as f:
            f.write(backend_sh)
        with open("start_frontend.sh", "w") as f:
            f.write(frontend_sh)
        with open("start_bridge.sh", "w") as f:
            f.write(bridge_sh)
        
        # Tornar executáveis
        os.chmod("start_backend.sh", 0o755)
        os.chmod("start_frontend.sh", 0o755)
        os.chmod("start_bridge.sh", 0o755)
        print("✅ Scripts .sh criados para Unix/Linux/macOS")

def main():
    """Função principal"""
    print("🚀 VitalTech - Configuração Automática do Ambiente")
    print("=" * 50)
    
    # Verificar pré-requisitos
    print("🔍 Verificando pré-requisitos...")
    
    python_ok = check_requirement("python --version", "Python")
    if not python_ok:
        python_ok = check_requirement("python3 --version", "Python3")
    
    node_ok = check_requirement("node --version", "Node.js")
    
    if not python_ok:
        print("\n❌ Python não encontrado. Instale Python 3.10+ primeiro.")
        print("Download: https://www.python.org/downloads/")
        return False
    
    if not node_ok:
        print("\n❌ Node.js não encontrado. Instale Node.js 18+ primeiro.")
        print("Download: https://nodejs.org/")
        return False
    
    # Configurar componentes
    backend_ok = setup_backend()
    frontend_ok = setup_frontend()
    
    if backend_ok and frontend_ok:
        create_startup_scripts()
        
        print("\n🎉 Configuração concluída com sucesso!")
        print("\nPróximos passos:")
        print("1. Inicie MongoDB (localhost:27017) ou configure MongoDB Atlas")
        
        if os.name == 'nt':
            print("2. Execute: start_backend.bat")
            print("3. Execute: start_frontend.bat")
        else:
            print("2. Execute: ./start_backend.sh")
            print("3. Execute: ./start_frontend.sh")
        
        print("4. Acesse: http://localhost:3000")
        print("\nOpcional:")
        if os.name == 'nt':
            print("5. Execute: start_bridge.bat (para simulação ESP32)")
        else:
            print("5. Execute: ./start_bridge.sh (para simulação ESP32)")
        
        return True
    else:
        print("\n❌ Configuração falhou. Verifique os erros acima.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)