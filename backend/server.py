from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
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
from firebase_config import get_firestore_db
from models import *
from ai_analysis import analyzer

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Firebase com fallback para MongoDB
try:
    from firebase_config import get_firestore_db
    USE_FIREBASE = True
    logger.info("Firebase configurado com sucesso")
except Exception as e:
    logger.warning(f"Firebase não disponível, usando MongoDB: {e}")
    USE_FIREBASE = False

from mongodb_fallback import mongodb_fallback

# Criar app FastAPI
app = FastAPI(title="VitalTech API", version="1.0.0")
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
        db = get_firestore_db()
        # Teste simples de conexão
        test_ref = db.collection('health_check').document('test')
        test_ref.set({'timestamp': datetime.utcnow(), 'status': 'ok'})
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "firebase": "connected",
            "simulation": "active" if simulation_active else "inactive"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

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
            base_values[anomaly_type] = random.choice([45, 130])  # Bradicardia ou taquicardia
        elif anomaly_type == "blood_pressure":
            base_values[anomaly_type] = random.choice([85, 165])  # Hipo ou hipertensão
        elif anomaly_type == "oxygen_saturation":
            base_values[anomaly_type] = random.randint(88, 93)  # Hipóxia leve
        elif anomaly_type == "temperature":
            base_values[anomaly_type] = random.choice([35.2, 38.5])  # Hipo ou hipertermia
    
    readings = []
    
    # Criar leituras para cada sensor
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
    db = get_firestore_db()
    
    logger.info("Iniciando simulação de dados...")
    
    while simulation_active:
        try:
            # Gerar novos sinais vitais
            vital_signs = await generate_realistic_vital_signs()
            
            # Salvar no Firestore
            batch = db.batch()
            for reading in vital_signs:
                doc_ref = db.collection('vital_signs').document()
                batch.set(doc_ref, reading.dict())
            
            batch.commit()
            
            # Executar análise IA a cada 3 leituras
            if random.random() < 0.3:  # 30% chance de análise
                readings_data = [reading.dict() for reading in vital_signs]
                analysis = await analyzer.analyze_vital_signs(readings_data)
                
                # Salvar análise
                analysis_ref = db.collection('ai_analyses').document()
                analysis_ref.set(analysis.dict())
                
                # Salvar alertas se houver
                if analysis.alerts_generated:
                    for alert in analysis.alerts_generated:
                        alert_ref = db.collection('alerts').document()
                        alert_ref.set(alert.dict())
            
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

# === ENDPOINTS DE SINAIS VITAIS ===

@api_router.post("/vital-signs")
async def save_vital_sign(vital_sign: Dict[str, Any]):
    """Salvar novo sinal vital"""
    try:
        db = get_firestore_db()
        
        # Adicionar timestamp se não existir
        if 'timestamp' not in vital_sign:
            vital_sign['timestamp'] = datetime.utcnow()
        
        # Salvar no Firestore
        doc_ref = db.collection('vital_signs').document()
        doc_ref.set(vital_sign)
        
        return {"message": "Sinal vital salvo", "id": doc_ref.id}
        
    except Exception as e:
        logger.error(f"Erro ao salvar sinal vital: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/vital-signs")
async def get_vital_signs(limit: int = 50, hours: int = 24):
    """Buscar sinais vitais recentes"""
    try:
        db = get_firestore_db()
        
        # Calcular timestamp limite
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Consultar Firestore
        query = db.collection('vital_signs') \
                 .where('timestamp', '>=', cutoff_time) \
                 .order_by('timestamp', direction='DESCENDING') \
                 .limit(limit)
        
        docs = query.stream()
        vital_signs = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            vital_signs.append(data)
        
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
        db = get_firestore_db()
        
        # Buscar último registro de cada tipo
        sensor_types = ["heart_rate", "blood_pressure", "oxygen_saturation", "temperature", "gsr"]
        latest_readings = {}
        
        for sensor_type in sensor_types:
            query = db.collection('vital_signs') \
                     .where('sensor_type', '==', sensor_type) \
                     .order_by('timestamp', direction='DESCENDING') \
                     .limit(1)
            
            docs = list(query.stream())
            if docs:
                data = docs[0].to_dict()
                data['id'] = docs[0].id
                latest_readings[sensor_type] = data
        
        return latest_readings
        
    except Exception as e:
        logger.error(f"Erro ao buscar últimos sinais: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/vital-signs/summary/{period}")
async def get_vital_signs_summary(period: str):
    """Resumo estatístico dos sinais vitais"""
    try:
        db = get_firestore_db()
        
        # Calcular período
        if period == "daily":
            hours = 24
        elif period == "weekly":
            hours = 24 * 7
        elif period == "monthly":
            hours = 24 * 30
        else:
            hours = 24
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Buscar dados
        query = db.collection('vital_signs') \
                 .where('timestamp', '>=', cutoff_time)
        
        docs = query.stream()
        
        # Agrupar por tipo de sensor
        sensor_data = {}
        for doc in docs:
            data = doc.to_dict()
            sensor_type = data.get('sensor_type')
            value = data.get('value')
            
            if sensor_type and value is not None:
                if sensor_type not in sensor_data:
                    sensor_data[sensor_type] = []
                sensor_data[sensor_type].append(value)
        
        # Calcular estatísticas
        summary = {}
        for sensor_type, values in sensor_data.items():
            if values:
                summary[sensor_type] = {
                    "count": len(values),
                    "average": round(sum(values) / len(values), 2),
                    "minimum": min(values),
                    "maximum": max(values),
                    "latest": values[-1] if values else None
                }
        
        return {
            "period": period,
            "summary": summary,
            "total_readings": sum(len(values) for values in sensor_data.values())
        }
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE PERFIL ===

@api_router.get("/profile")
async def get_patient_profile():
    """Buscar perfil do paciente"""
    try:
        db = get_firestore_db()
        
        # Buscar perfil único (para feira)
        query = db.collection('patient_profiles').limit(1)
        docs = list(query.stream())
        
        if docs:
            data = docs[0].to_dict()
            data['id'] = docs[0].id
            return data
        else:
            # Retornar perfil padrão se não existir
            default_profile = PatientProfile()
            return default_profile.dict()
            
    except Exception as e:
        logger.error(f"Erro ao buscar perfil: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/profile")
async def save_patient_profile(profile_data: Dict[str, Any]):
    """Salvar/atualizar perfil do paciente"""
    try:
        db = get_firestore_db()
        
        # Adicionar timestamp de atualização
        profile_data['updated_at'] = datetime.utcnow()
        
        # Verificar se já existe um perfil
        query = db.collection('patient_profiles').limit(1)
        docs = list(query.stream())
        
        if docs:
            # Atualizar perfil existente
            doc_ref = docs[0].reference
            doc_ref.update(profile_data)
            profile_id = docs[0].id
        else:
            # Criar novo perfil
            profile_data['created_at'] = datetime.utcnow()
            doc_ref = db.collection('patient_profiles').document()
            doc_ref.set(profile_data)
            profile_id = doc_ref.id
        
        return {"message": "Perfil salvo", "id": profile_id}
        
    except Exception as e:
        logger.error(f"Erro ao salvar perfil: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE ALERTAS ===

@api_router.get("/alerts")
async def get_alerts(limit: int = 20, resolved: Optional[bool] = None):
    """Buscar alertas"""
    try:
        db = get_firestore_db()
        
        query = db.collection('alerts') \
                 .order_by('timestamp', direction='DESCENDING') \
                 .limit(limit)
        
        if resolved is not None:
            query = query.where('resolved', '==', resolved)
        
        docs = query.stream()
        alerts = []
        
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            alerts.append(data)
        
        return {
            "alerts": alerts,
            "count": len(alerts)
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar alertas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Marcar alerta como resolvido"""
    try:
        db = get_firestore_db()
        
        doc_ref = db.collection('alerts').document(alert_id)
        doc_ref.update({
            'resolved': True,
            'resolved_at': datetime.utcnow()
        })
        
        return {"message": "Alerta resolvido"}
        
    except Exception as e:
        logger.error(f"Erro ao resolver alerta: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# === ENDPOINTS DE ANÁLISE IA ===

@api_router.post("/analysis/run")
async def run_ai_analysis():
    """Executar análise IA dos dados recentes"""
    try:
        db = get_firestore_db()
        
        # Buscar sinais vitais recentes
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        query = db.collection('vital_signs') \
                 .where('timestamp', '>=', cutoff_time) \
                 .limit(20)
        
        docs = list(query.stream())
        if not docs:
            return {"message": "Nenhum dado recente para análise"}
        
        # Preparar dados para análise
        vital_signs_data = []
        for doc in docs:
            data = doc.to_dict()
            vital_signs_data.append(data)
        
        # Buscar perfil do paciente
        profile_query = db.collection('patient_profiles').limit(1)
        profile_docs = list(profile_query.stream())
        patient_profile = profile_docs[0].to_dict() if profile_docs else None
        
        # Executar análise IA
        analysis = await analyzer.analyze_vital_signs(vital_signs_data, patient_profile)
        
        # Salvar análise
        analysis_ref = db.collection('ai_analyses').document()
        analysis_ref.set(analysis.dict())
        
        # Salvar alertas gerados
        if analysis.alerts_generated:
            batch = db.batch()
            for alert in analysis.alerts_generated:
                alert_ref = db.collection('alerts').document()
                batch.set(alert_ref, alert.dict())
            batch.commit()
        
        return {
            "message": "Análise executada",
            "analysis_id": analysis_ref.id,
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
        db = get_firestore_db()
        
        query = db.collection('ai_analyses') \
                 .order_by('timestamp', direction='DESCENDING') \
                 .limit(1)
        
        docs = list(query.stream())
        if docs:
            data = docs[0].to_dict()
            data['id'] = docs[0].id
            return data
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
        db = get_firestore_db()
        
        # Calcular período
        if period == "daily":
            hours = 24
        elif period == "weekly":
            hours = 24 * 7
        elif period == "monthly":
            hours = 24 * 30
        else:
            hours = 24
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Buscar dados do período
        vital_signs_query = db.collection('vital_signs') \
                           .where('timestamp', '>=', cutoff_time) \
                           .order_by('timestamp')
        
        alerts_query = db.collection('alerts') \
                      .where('timestamp', '>=', cutoff_time) \
                      .order_by('timestamp')
        
        vital_signs = []
        for doc in vital_signs_query.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            vital_signs.append(data)
        
        alerts = []
        for doc in alerts_query.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            alerts.append(data)
        
        # Buscar perfil
        profile_query = db.collection('patient_profiles').limit(1)
        profile_docs = list(profile_query.stream())
        patient_profile = profile_docs[0].to_dict() if profile_docs else {}
        
        return {
            "period": period,
            "patient_profile": patient_profile,
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
        db = get_firestore_db()
        
        collections = ['vital_signs', 'alerts', 'ai_analyses']
        deleted_count = 0
        
        for collection_name in collections:
            # Deletar documentos em lotes
            collection_ref = db.collection(collection_name)
            docs = collection_ref.limit(500).stream()
            
            batch = db.batch()
            batch_count = 0
            
            for doc in docs:
                batch.delete(doc.reference)
                batch_count += 1
                deleted_count += 1
                
                if batch_count >= 500:
                    batch.commit()
                    batch = db.batch()
                    batch_count = 0
            
            if batch_count > 0:
                batch.commit()
        
        return {
            "message": "Dados de demonstração limpos",
            "deleted_documents": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Incluir router na aplicação
app.include_router(api_router)

# Eventos de inicialização
@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação"""
    logger.info("VitalTech API iniciando...")
    
    # Testar conexão Firebase
    try:
        db = get_firestore_db()
        test_ref = db.collection('system').document('startup')
        test_ref.set({
            'timestamp': datetime.utcnow(),
            'status': 'started'
        })
        logger.info("Firebase conectado com sucesso")
    except Exception as e:
        logger.error(f"Erro na conexão Firebase: {e}")
    
    # Iniciar simulação automaticamente (para demonstração)
    global simulation_active, simulation_task
    simulation_active = True
    simulation_task = asyncio.create_task(simulation_loop())
    logger.info("Simulação de dados iniciada automaticamente")

@app.on_event("shutdown")
async def shutdown_event():
    """Limpeza na finalização"""
    logger.info("VitalTech API finalizando...")
    
    global simulation_active, simulation_task
    simulation_active = False
    if simulation_task:
        simulation_task.cancel()
    
    logger.info("Simulação parada")