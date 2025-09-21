# Conteúdo do server_mongodb.py (versão limpa)
# Copiando todo o conteúdo do server_mongodb.py para server.py

from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
import random
import json
import uuid

# Importar configurações e modelos
from mongodb_fallback import mongodb_fallback
from models import *
from ai_analysis import analyzer

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis globais para simulação
simulation_task = None
simulation_active = False

# === LIFESPAN EVENTS (SUBSTITUI on_event) ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos de inicialização e finalização da aplicação"""
    # STARTUP
    logger.info("VitalTech API iniciando...")
    
    try:
        await mongodb_fallback.initialize()
        logger.info("MongoDB conectado com sucesso")
    except Exception as e:
        logger.error(f"Erro na conexão MongoDB: {e}")
    
    # Iniciar simulação automaticamente (para demonstração)
    global simulation_active, simulation_task
    simulation_active = True
    simulation_task = asyncio.create_task(simulation_loop())
    logger.info("Simulação de dados iniciada automaticamente")
    
    yield  # Aplicação roda aqui
    
    # SHUTDOWN
    logger.info("VitalTech API finalizando...")
    
    simulation_active = False
    if simulation_task:
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass
    
    logger.info("Simulação parada")

# Criar app FastAPI com lifespan
app = FastAPI(
    title="VitalTech API", 
    version="1.0.0",
    lifespan=lifespan
)
api_router = APIRouter(prefix="/api")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variáveis globais para simulação
simulation_task = None
simulation_active = False

# === ENDPOINTS BÁSICOS ===

@api_router.get("/")
async def root():
    """Endpoint de teste"""
    return {"message": "VitalTech API - Sistema de Monitoramento de Sinais Vitais"}

@api_router.get("/health")
async def health_check():
    """Verificação de saúde da API"""
    try:
        await mongodb_fallback.initialize()
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "database": "mongodb_connected",
            "simulation": "active" if simulation_active else "inactive"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# === SIMULAÇÃO DE DADOS ===

async def generate_realistic_vital_signs():
    """Gerar sinais vitais realistas para demonstração"""
    now = datetime.utcnow()
    
    # Valores base com variações realistas
    base_values = {
        "heart_rate": 75 + random.randint(-15, 15),
        "blood_pressure": 120 + random.randint(-20, 20),
        "oxygen_saturation": 98 + random.randint(-3, 2),
        "temperature": 36.5 + random.uniform(-0.5, 1.0),
        "gsr": 400 + random.randint(-150, 150)
    }
    
    # Ocasionalmente gerar anomalias para demonstração
    if random.random() < 0.1:  # 10% chance de anomalia
        anomaly_type = random.choice(list(base_values.keys()))
        if anomaly_type == "heart_rate":
            base_values[anomaly_type] = random.choice([45, 130])
        elif anomaly_type == "blood_pressure":
            base_values[anomaly_type] = random.choice([85, 165])
        elif anomaly_type == "oxygen_saturation":
            base_values[anomaly_type] = random.randint(88, 93)
        elif anomaly_type == "temperature":
            base_values[anomaly_type] = random.choice([35.2, 38.5])
    
    readings = []
    
    readings.append(HeartRateReading(
        value=base_values["heart_rate"],
        timestamp=now
    ))
    
    readings.append(BloodPressureReading(
        value=base_values["blood_pressure"],
        systolic=base_values["blood_pressure"],
        diastolic=base_values["blood_pressure"] - 40,
        timestamp=now
    ))
    
    readings.append(OxygenSaturationReading(
        value=base_values["oxygen_saturation"],
        timestamp=now
    ))
    
    readings.append(TemperatureReading(
        value=round(base_values["temperature"], 1),
        timestamp=now
    ))
    
    readings.append(GSRReading(
        value=base_values["gsr"],
        timestamp=now
    ))
    
    return readings

async def simulation_loop():
    """Loop principal da simulação"""
    global simulation_active
    
    logger.info("Iniciando simulação de dados...")
    
    while simulation_active:
        try:
            # Gerar novos sinais vitais
            vital_signs = await generate_realistic_vital_signs()
            
            # Salvar no MongoDB
            for reading in vital_signs:
                await mongodb_fallback.save_vital_sign(reading.dict())
            
            # Executar análise IA ocasionalmente (sem bloquear)
            if random.random() < 0.1:  # 10% chance de análise (reduzido)
                try:
                    readings_data = [reading.dict() for reading in vital_signs]
                    analysis = await analyzer.analyze_vital_signs(readings_data)
                    
                    # Salvar no MongoDB
                    await mongodb_fallback.save_analysis(analysis.dict())
                    
                    # Salvar alertas se houver
                    if analysis.alerts_generated:
                        for alert in analysis.alerts_generated:
                            await mongodb_fallback.save_alert(alert.dict())
                except Exception as e:
                    logger.warning(f"Erro na análise IA (continuando): {e}")
            
            logger.debug(f"Dados simulados salvos: {len(vital_signs)} leituras")
            await asyncio.sleep(3)  # Intervalo de 3 segundos
            
        except Exception as e:
            logger.error(f"Erro na simulação: {e}")
            await asyncio.sleep(5)

@api_router.post("/simulation/start")
async def start_simulation(background_tasks: BackgroundTasks):
    """Iniciar simulação de dados"""
    global simulation_active, simulation_task
    
    if simulation_active:
        return {"message": "Simulação já está ativa"}
    
    simulation_active = True
    simulation_task = asyncio.create_task(simulation_loop())
    
    return {"message": "Simulação iniciada"}

@api_router.post("/simulation/stop")
async def stop_simulation():
    """Parar simulação de dados"""
    global simulation_active, simulation_task
    
    simulation_active = False
    if simulation_task:
        simulation_task.cancel()
        simulation_task = None
    
    return {"message": "Simulação parada"}

# === ENDPOINTS PARA ESP32 ===

@api_router.post("/esp32/data")
async def receive_esp32_data(esp32_data: Dict[str, Any]):
    """Receber dados do ESP32 via Bluetooth/HTTP bridge"""
    try:
        # Mapear dados do ESP32 para formato interno
        readings = []
        timestamp = datetime.utcnow()
        
        # Extrair dados dos sensores
        if 'bpm' in esp32_data and esp32_data['bpm'] > 0:
            reading = HeartRateReading(
                value=float(esp32_data['bpm']),
                timestamp=timestamp,
                device_id="esp32_real"
            )
            readings.append(reading)
            
        if 'spo2' in esp32_data and esp32_data['spo2'] > 0:
            reading = OxygenSaturationReading(
                value=float(esp32_data['spo2']),
                timestamp=timestamp,
                device_id="esp32_real"
            )
            readings.append(reading)
            
        if 'temperature' in esp32_data:
            reading = TemperatureReading(
                value=float(esp32_data['temperature']),
                timestamp=timestamp,
                device_id="esp32_real"
            )
            readings.append(reading)
            
        if 'pressure' in esp32_data:
            reading = BloodPressureReading(
                value=float(esp32_data['pressure']),
                timestamp=timestamp,
                device_id="esp32_real"
            )
            readings.append(reading)
            
        if 'gsr' in esp32_data:
            reading = GSRReading(
                value=float(esp32_data['gsr']),
                timestamp=timestamp,
                device_id="esp32_real"
            )
            readings.append(reading)
        
        # Salvar no MongoDB
        for reading in readings:
            await mongodb_fallback.save_vital_sign(reading.dict())
        
        logger.info(f"Dados ESP32 salvos: {len(readings)} leituras")
        
        return {
            "message": "Dados ESP32 recebidos com sucesso",
            "readings_saved": len(readings),
            "timestamp": timestamp
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar dados ESP32: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/esp32/status")
async def get_esp32_status():
    """Verificar status de conexão ESP32"""
    try:
        # Verificar se há dados recentes do dispositivo real
        recent_readings = await mongodb_fallback.get_vital_signs(10, 1)  # Últimos 10 da última hora
        
        esp32_readings = [r for r in recent_readings if r.get('device_id') == 'esp32_real']
        
        is_connected = len(esp32_readings) > 0
        last_reading = esp32_readings[0] if esp32_readings else None
        
        return {
            "connected": is_connected,
            "last_reading": last_reading,
            "total_esp32_readings": len(esp32_readings),
            "checked_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Erro ao verificar status ESP32: {e}")
        return {
            "connected": False,
            "error": str(e),
            "checked_at": datetime.utcnow()
        }

@api_router.post("/vital-signs")
async def save_vital_sign(vital_sign: Dict[str, Any]):
    """Salvar novo sinal vital"""
    try:
        if 'timestamp' not in vital_sign:
            vital_sign['timestamp'] = datetime.utcnow()
        
        doc_id = await mongodb_fallback.save_vital_sign(vital_sign)
        return {"message": "Sinal vital salvo", "id": doc_id}
        
    except Exception as e:
        logger.error(f"Erro ao salvar sinal vital: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/vital-signs")
async def get_vital_signs(limit: int = 50, hours: int = 24):
    """Buscar sinais vitais recentes"""
    try:
        vital_signs = await mongodb_fallback.get_vital_signs(limit, hours)
        
        return {
            "vital_signs": vital_signs,
            "count": len(vital_signs),
            "period_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar sinais vitais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/vital-signs/latest")
async def get_latest_vital_signs():
    """Buscar últimos sinais vitais por tipo de sensor"""
    try:
        latest_readings = await mongodb_fallback.get_latest_vital_signs()
        return latest_readings
        
    except Exception as e:
        logger.error(f"Erro ao buscar últimos sinais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE PERFIL ===

@api_router.get("/profile")
async def get_patient_profile():
    """Buscar perfil do paciente"""
    try:
        profile = await mongodb_fallback.get_profile()
        if profile:
            return profile
        else:
            default_profile = PatientProfile()
            return default_profile.dict()
            
    except Exception as e:
        logger.error(f"Erro ao buscar perfil: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/profile")
async def save_patient_profile(profile_data: Dict[str, Any]):
    """Salvar/atualizar perfil do paciente"""
    try:
        profile_id = await mongodb_fallback.save_profile(profile_data)
        return {"message": "Perfil salvo", "id": profile_id}
        
    except Exception as e:
        logger.error(f"Erro ao salvar perfil: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE ALERTAS ===

@api_router.get("/alerts")
async def get_alerts(limit: int = 20, resolved: Optional[bool] = None):
    """Buscar alertas"""
    try:
        alerts = await mongodb_fallback.get_alerts(limit, resolved)
        
        return {
            "alerts": alerts,
            "count": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE ANÁLISE IA ===

@api_router.post("/analysis/run")
async def run_ai_analysis():
    """Executar análise IA dos dados recentes"""
    try:
        # Buscar sinais vitais recentes
        vital_signs = await mongodb_fallback.get_vital_signs(20, 1)  # Última hora
        
        if not vital_signs:
            return {"message": "Nenhum dado recente para análise"}
        
        # Buscar perfil do paciente
        patient_profile = await mongodb_fallback.get_profile()
        
        # Executar análise IA
        analysis = await analyzer.analyze_vital_signs(vital_signs, patient_profile)
        
        # Salvar análise
        analysis_id = await mongodb_fallback.save_analysis(analysis.dict())
        
        # Salvar alertas gerados
        if analysis.alerts_generated:
            for alert in analysis.alerts_generated:
                await mongodb_fallback.save_alert(alert.dict())
        
        return {
            "message": "Análise executada",
            "analysis_id": analysis_id,
            "health_status": analysis.health_status,
            "alerts_generated": len(analysis.alerts_generated)
        }
        
    except Exception as e:
        logger.error(f"Erro na análise IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analysis/latest")
async def get_latest_analysis():
    """Buscar última análise IA"""
    try:
        analysis = await mongodb_fallback.get_latest_analysis()
        if analysis:
            return analysis
        else:
            return {"message": "Nenhuma análise encontrada"}
            
    except Exception as e:
        logger.error(f"Erro ao buscar análise: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE RELATÓRIOS ===

@api_router.get("/reports/data/{period}")
async def get_report_data(period: str):
    """Buscar dados para relatórios"""
    try:
        if period == "daily":
            hours = 24
        elif period == "weekly":
            hours = 24 * 7
        elif period == "monthly":
            hours = 24 * 30
        else:
            hours = 24
        
        # Buscar dados do período
        vital_signs = await mongodb_fallback.get_vital_signs(1000, hours)
        alerts = await mongodb_fallback.get_alerts(100)
        patient_profile = await mongodb_fallback.get_profile()
        
        return {
            "period": period,
            "patient_profile": patient_profile or {},
            "vital_signs": vital_signs,
            "alerts": alerts,
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar dados do relatório: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === LIMPEZA DE DADOS (PARA FEIRA) ===

@api_router.post("/data/cleanup")
async def cleanup_demo_data():
    """Limpar dados de demonstração"""
    try:
        deleted_count = await mongodb_fallback.cleanup_demo_data()
        
        return {
            "message": "Dados de demonstração limpos",
            "deleted_documents": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Incluir router na aplicação
app.include_router(api_router)

# === EXECUÇÃO DO SERVIDOR ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)