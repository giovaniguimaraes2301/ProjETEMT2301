# VitalTech - Sistema de Monitoramento de Sinais Vitais

Sistema completo para monitoramento de sinais vitais usando ESP32, MongoDB/Firebase e interface web responsiva.

## 🚀 INSTALAÇÃO RÁPIDA (Windows)

1. **Execute o instalador automático:**
   ```bash
   setup_windows.bat
   ```

2. **Inicie o sistema:**
   ```bash
   # Terminal 1 - Backend
   start_backend.bat
   
   # Terminal 2 - Frontend  
   start_frontend.bat
   ```

3. **Acesse:** http://localhost:3000

## 📖 GUIA DETALHADO

Consulte `SETUP_LOCAL.md` para instruções passo-a-passo completas.

---

## 🔧 RESOLUÇÃO DE PROBLEMAS COMUNS

### Backend não inicia
- Verifique se Python 3.10+ está instalado
- Execute: `pip install -r backend/requirements.txt`

### Frontend não carrega
- Verifique se Node.js está instalado
- Execute: `cd frontend && npm install`

### Dados não aparecem
- Verifique se MongoDB está rodando (localhost:27017)
- Ou configure MongoDB Atlas (nuvem)

## 📱 URLs do Sistema

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001/api
- **Documentação:** http://localhost:8001/docs
