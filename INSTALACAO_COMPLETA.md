# 🏥 VitalTech - Sistema de Monitoramento de Sinais Vitais

## 📋 DESCRIÇÃO DO PROJETO

Sistema completo de monitoramento de sinais vitais para feira de inovação, desenvolvido com:
- **Frontend**: React + Chart.js + TailwindCSS
- **Backend**: FastAPI + MongoDB + Google Gemini IA
- **Hardware**: ESP32 S3 + Sensores (MAX30105, MPU6050, LM35, FSR402, GSR)
- **Comunicação**: Bluetooth LE + HTTP Bridge

## 🚀 INSTALAÇÃO E EXECUÇÃO

### **Pré-requisitos:**
- Python 3.11+
- Node.js 16+
- MongoDB
- Yarn (não usar npm)

### **1. Backend (FastAPI):**
```bash
cd backend
pip install -r requirements.txt
python server.py
```

### **2. Frontend (React):**
```bash
cd frontend
yarn install
yarn start
```

### **3. Bridge Bluetooth (Opcional):**
```bash
# Para conectar ESP32 real
pip install ble-serial
python ble_bridge.py --simulate  # Modo simulação
python ble_bridge.py             # Modo real com ESP32
```

## 🔧 CONFIGURAÇÃO

### **Variáveis de Ambiente:**

**Backend (.env):**
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="vitaltech"
CORS_ORIGINS="*"

# Google Gemini IA
GEMINI_API_KEY="sua_api_key_aqui"

# Firebase (opcional)
FIREBASE_PROJECT_ID="seu_projeto"
FIREBASE_PRIVATE_KEY="sua_chave"
FIREBASE_CLIENT_EMAIL="seu_email"
```

**Frontend (.env):**
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 📊 FUNCIONALIDADES

### **Dashboard em Tempo Real:**
- ✅ Gráficos interativos com Chart.js
- ✅ 5 sensores: FC, PA, SpO2, Temp, GSR
- ✅ Atualização automática a cada 3-5 segundos
- ✅ Histórico de até 2000 registros

### **Sistema de Alertas IA:**
- ✅ Análise com Google Gemini
- ✅ Detecção de anomalias automática
- ✅ Alertas baseados em regras médicas
- ✅ Recomendações contextuais

### **Relatórios Profissionais:**
- ✅ Geração PDF automática
- ✅ Exportação CSV
- ✅ Períodos: diário, semanal, mensal
- ✅ Estatísticas completas

### **Interface Otimizada:**
- ✅ Design responsivo
- ✅ Modo escuro/claro
- ✅ Tela cheia para apresentações
- ✅ Interface em português
- ✅ Status de conexão ESP32

## 🔗 INTEGRAÇÃO ESP32

### **Sensores Suportados:**
1. **MAX30105**: Frequência cardíaca + SpO2
2. **MPU6050**: Acelerômetro + Giroscópio  
3. **LM35**: Temperatura corporal
4. **FSR402**: Pressão localizada
5. **TCC + Amp-op**: Resistência galvânica (GSR)

### **Comunicação:**
- **Bluetooth LE** com UUIDs específicos por sensor
- **Bridge HTTP** automático via `ble_bridge.py`
- **Fallback** para simulação sem hardware

### **Endpoints API:**
```http
POST /api/esp32/data          # Receber dados do ESP32
GET  /api/esp32/status        # Verificar conexão
GET  /api/vital-signs/latest  # Últimos valores
GET  /api/alerts              # Alertas ativos
POST /api/analysis/run        # Executar análise IA
```

## 📱 USO NA FEIRA

### **Para Visitantes:**
1. **Acesse** a URL do sistema
2. **Clique** em tela cheia (ícone expandir)
3. **Observe** gráficos em tempo real
4. **Configure** perfil de exemplo
5. **Gere** relatório PDF personalizado

### **Entre Demonstrações:**
- **Botão "Limpar Dados"** para resetar
- **Status ESP32** visível no header
- **Modo simulação** automático se ESP32 desconectado

## 🧪 TESTES

### **Backend:**
```bash
curl http://localhost:8001/api/health
curl http://localhost:8001/api/vital-signs/latest
```

### **Frontend:**
- Acesse: `http://localhost:3000`
- Teste navegação entre seções
- Verifique gráficos em tempo real
- Teste geração de relatórios

### **Bridge Bluetooth:**
```bash
python ble_bridge.py --simulate  # Testa sem ESP32
```

## 📁 ESTRUTURA DO PROJETO

```
vitaltech/
├── backend/                    # API FastAPI
│   ├── server.py              # Servidor principal
│   ├── models.py              # Modelos de dados
│   ├── ai_analysis.py         # Análise IA Gemini
│   ├── mongodb_fallback.py    # Interface MongoDB
│   └── requirements.txt       # Dependências Python
├── frontend/                   # Interface React
│   ├── src/
│   │   ├── App.js            # Aplicação principal
│   │   ├── App.css           # Estilos globais
│   │   └── components/       # Componentes UI
│   ├── public/index.html     # HTML base
│   └── package.json          # Dependências Node
├── ble_bridge.py              # Bridge Bluetooth->HTTP
├── esp32_code.ino            # Código do microcontrolador
└── README.md                  # Esta documentação
```

## 🔧 PROBLEMAS COMUNS

### **Backend não inicia:**
- Verificar se MongoDB está rodando
- Conferir variáveis de ambiente
- Instalar dependências: `pip install -r requirements.txt`

### **Frontend não carrega:**
- Verificar URL do backend no .env
- Instalar dependências: `yarn install`
- Usar yarn, não npm

### **Gráficos em branco:**
- Aguardar alguns segundos para dados chegarem
- Verificar console do navegador (F12)
- Testar endpoint: `/api/vital-signs/latest`

### **ESP32 não conecta:**
- Verificar nome do dispositivo: "ESP32_S3_Health"
- Usar modo simulação: `--simulate`
- Instalar ble-serial: `pip install ble-serial`

## 🚀 DEPLOY EM PRODUÇÃO

### **Opção 1: Docker**
```dockerfile
# Dockerfile exemplo
FROM python:3.11
COPY backend/ /app/backend/
WORKDIR /app/backend
RUN pip install -r requirements.txt
CMD ["python", "server.py"]
```

### **Opção 2: VPS/Cloud**
1. Configure variáveis de ambiente
2. Use proxy reverso (nginx)
3. Configure SSL/HTTPS
4. MongoDB em nuvem (Atlas)

## 📞 SUPORTE

- **Logs Backend**: `tail -f /var/log/supervisor/backend.*.log`
- **Console Frontend**: F12 > Console
- **Status API**: GET `/api/health`
- **Verificar ESP32**: GET `/api/esp32/status`

## 🏆 CARACTERÍSTICAS TÉCNICAS

- **Tempo Real**: Atualização a cada 3 segundos
- **Precisão**: Filtros Butterworth + Kalman (ESP32)
- **Escalabilidade**: Até 2000 registros em memória
- **IA**: Google Gemini para análise médica
- **Compatibilidade**: Desktop + Mobile
- **Performance**: Otimizado para apresentações

---

**Desenvolvido para Feira de Inovação**  
Sistema completo de monitoramento de sinais vitais com IA integrada.