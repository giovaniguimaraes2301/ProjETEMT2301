# 🔧 Solucionando Problemas - VitalTech

## ❌ Problema: Backend não inicia (Windows)

**Sintoma:** Executar `python server.py` não mostra nada e volta ao prompt

**Solução:**
```bash
cd backend
# Método 1: Usar uvicorn diretamente
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Método 2: Verificar dependências
pip install fastapi uvicorn pymongo python-dotenv google-generativeai

# Método 3: Executar com debug
python -c "
import server
import uvicorn
uvicorn.run(server.app, host='0.0.0.0', port=8001)
"
```

## ❌ Problema: "yarn não é reconhecido" (Windows)

**Solução:**
```bash
# Instalar yarn globalmente
npm install -g yarn

# OU usar npm diretamente
cd frontend
npm install
npm start
```

## ❌ Problema: ESP32 Bridge não conecta

**Sintoma:** Erro "No connection could be made"

**Soluções:**
1. **Verificar se backend está rodando:**
   ```bash
   # Testar manualmente
   curl http://localhost:8001/api/health
   ```

2. **Usar URL correta:**
   ```bash
   python ble_bridge.py --simulate --api-url "http://localhost:8001/api"
   ```

3. **Verificar firewall do Windows**

## ❌ Problema: MongoDB não conecta

**Soluções:**

### Opção 1: Instalar MongoDB local
1. Baixar: https://www.mongodb.com/try/download/community
2. Instalar e iniciar serviço
3. Verificar se está rodando na porta 27017

### Opção 2: Usar MongoDB Atlas (Nuvem)
1. Criar conta em: https://cloud.mongodb.com/
2. Criar cluster gratuito
3. Obter string de conexão
4. Atualizar `backend/.env`:
   ```
   MONGO_URL=mongodb+srv://usuario:senha@cluster.mongodb.net/vitaltech
   ```

## ❌ Problema: Porta ocupada

**Para porta 8001 (backend):**
```bash
# Windows
netstat -ano | findstr :8001
taskkill /PID [número_do_processo] /F
```

**Para porta 3000 (frontend):**
```bash
# Windows  
netstat -ano | findstr :3000
taskkill /PID [número_do_processo] /F
```

## ❌ Problema: Frontend não conecta com Backend

**Verificar arquivo frontend/.env:**
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Testar conexão:**
1. Abrir http://localhost:8001/api no navegador
2. Deve mostrar: `{"message": "VitalTech API - Sistema de Monitoramento..."}`

## ❌ Problema: Gráficos não aparecem

**Possíveis causas:**
1. Backend não está enviando dados
2. Simulação não está ativa
3. Erro no frontend

**Soluções:**
1. Verificar logs do backend
2. Acessar http://localhost:8001/api/vital-signs
3. Deve retornar dados JSON

## ❌ Problema: Erro de CORS

**Sintoma:** Erro "blocked by CORS policy"

**Solução:** Verificar `backend/.env`:
```
CORS_ORIGINS=*
```

## 🆘 Último Recurso: Reset Completo

```bash
# 1. Parar todos os processos
# Fechar todos os terminais

# 2. Limpar dependências
cd frontend
rm -rf node_modules
npm install

cd ../backend  
pip uninstall -r requirements.txt -y
pip install -r requirements.txt

# 3. Usar configuração local
copy local.env .env
cd ../frontend
copy local.env .env

# 4. Reiniciar
cd ../backend
python server.py

# Novo terminal
cd frontend
npm start
```

## 📞 Suporte Adicional

Se nenhuma solução funcionar:

1. **Verificar versões:**
   ```bash
   python --version  # Deve ser 3.10+
   node --version    # Deve ser 18+
   ```

2. **Enviar logs de erro completos**

3. **Informar sistema operacional e versão**