# Guia de Instalação Local - VitalTech

## 📋 Pré-requisitos

1. **Python 3.10+** instalado
2. **Node.js 18+** e **npm** instalados  
3. **MongoDB** instalado e rodando localmente na porta 27017
4. **Git** instalado

## 🔧 Passo 1: Preparar o Ambiente

### 1.1 Instalar Node.js e Yarn
```bash
# Baixar e instalar Node.js em: https://nodejs.org/
# Depois instalar o Yarn globalmente:
npm install -g yarn
```

### 1.2 Instalar MongoDB
```bash
# Windows: Baixar em https://www.mongodb.com/try/download/community
# Ou usar MongoDB Atlas (cloud) se preferir
```

### 1.3 Verificar instalações
```bash
python --version     # Deve mostrar 3.10+
node --version       # Deve mostrar 18+
yarn --version       # Deve mostrar 1.22+
```

## 🚀 Passo 2: Configurar Backend

### 2.1 Navegar para pasta backend
```bash
cd backend
```

### 2.2 Instalar dependências Python
```bash
pip install -r requirements.txt
```

### 2.3 Configurar variáveis de ambiente
O arquivo `.env` já está configurado, mas certifique-se que MongoDB está rodando em `mongodb://localhost:27017`

### 2.4 **IMPORTANTE**: Corrigir problemas no servidor
O servidor tem um pequeno problema que impede de iniciar. Execute:

```bash
# Para Windows:
python -c "
import os
server_path = 'server.py'
with open(server_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar se há problema com lifespan
if '__name__ == \"__main__\"' not in content:
    # Adicionar código para executar o servidor
    content += '''

# === EXECUÇÃO DO SERVIDOR ===
if __name__ == \"__main__\":
    import uvicorn
    uvicorn.run(app, host=\"0.0.0.0\", port=8001)
'''
    with open(server_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Servidor corrigido!')
else:
    print('Servidor já está correto.')
"
```

### 2.5 Iniciar o servidor backend
```bash
python server.py
```

Se der erro, tente:
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

O servidor deve mostrar:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8001
```

## 🎨 Passo 3: Configurar Frontend

### 3.1 Abrir NOVO terminal e navegar para frontend
```bash
cd frontend
```

### 3.2 Instalar dependências
```bash
yarn install
```

### 3.3 **IMPORTANTE**: Atualizar URL do backend
Edite o arquivo `frontend/.env`:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 3.4 Iniciar o frontend
```bash
yarn start
```

O frontend deve abrir em: http://localhost:3000

## 🤖 Passo 4: Testar ESP32 Bridge (Opcional)

### 4.1 Em um NOVO terminal, na pasta raiz:
```bash
python ble_bridge.py --simulate --api-url "http://localhost:8001/api"
```

## ✅ Passo 5: Verificar Funcionamento

1. **Backend**: Acesse http://localhost:8001/api/ - deve mostrar mensagem da API
2. **Frontend**: Acesse http://localhost:3000 - deve mostrar dashboard
3. **Dados**: O dashboard deve mostrar gráficos em tempo real

## 🔧 Solução de Problemas

### ❌ Backend não inicia
```bash
# Verificar dependências
pip install fastapi uvicorn pymongo python-dotenv google-generativeai firebase-admin

# Tentar iniciar manualmente
uvicorn server:app --host 0.0.0.0 --port 8001
```

### ❌ Frontend não encontra backend
1. Verificar se backend está rodando na porta 8001
2. Conferir arquivo `frontend/.env`:
   ```
   REACT_APP_BACKEND_URL=http://localhost:8001
   ```

### ❌ MongoDB não conecta
1. Instalar MongoDB Community Edition
2. Iniciar serviço MongoDB
3. Ou usar MongoDB Atlas (cloud) e atualizar MONGO_URL no .env

### ❌ Erro "yarn não é reconhecido"
```bash
npm install -g yarn
# Ou usar npm diretamente:
npm install
npm start
```

## 📱 URLs Importantes

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api
- **Health Check**: http://localhost:8001/api/health
- **Documentação API**: http://localhost:8001/docs

## 🎯 Status Esperado

Quando tudo estiver funcionando:
- ✅ Backend rodando na porta 8001
- ✅ Frontend rodando na porta 3000  
- ✅ Dashboard mostrando gráficos em tempo real
- ✅ ESP32 bridge enviando dados simulados (opcional)

## 📞 Suporte

Se ainda houver problemas:
1. Verificar logs de erro nos terminais
2. Confirmar que todas as dependências foram instaladas
3. Verificar se as portas 3000 e 8001 estão livres