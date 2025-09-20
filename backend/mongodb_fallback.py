from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MongoDBFallback:
    """Fallback para MongoDB enquanto Firebase não está configurado"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.initialized = False
    
    async def initialize(self):
        """Inicializar conexão MongoDB"""
        if not self.initialized:
            try:
                mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
                db_name = os.environ.get('DB_NAME', 'vitaltech')
                
                self.client = AsyncIOMotorClient(mongo_url)
                self.db = self.client[db_name]
                
                # Teste de conexão
                await self.db.command('ping')
                self.initialized = True
                logger.info("MongoDB conectado com sucesso")
                
            except Exception as e:
                logger.error(f"Erro ao conectar MongoDB: {e}")
                raise
    
    async def save_vital_sign(self, data: Dict[str, Any]) -> str:
        """Salvar sinal vital"""
        if not self.initialized:
            await self.initialize()
        
        if 'timestamp' not in data:
            data['timestamp'] = datetime.utcnow()
        
        result = await self.db.vital_signs.insert_one(data)
        return str(result.inserted_id)
    
    async def get_vital_signs(self, limit: int = 50, hours: int = 24) -> List[Dict[str, Any]]:
        """Buscar sinais vitais"""
        if not self.initialized:
            await self.initialize()
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        cursor = self.db.vital_signs.find({
            'timestamp': {'$gte': cutoff_time}
        }).sort('timestamp', -1).limit(limit)
        
        results = []
        async for doc in cursor:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            results.append(doc)
        
        return results
    
    async def get_latest_vital_signs(self) -> Dict[str, Any]:
        """Buscar últimos sinais por tipo"""
        if not self.initialized:
            await self.initialize()
        
        sensor_types = ["heart_rate", "blood_pressure", "oxygen_saturation", "temperature", "gsr"]
        latest_readings = {}
        
        for sensor_type in sensor_types:
            doc = await self.db.vital_signs.find_one(
                {'sensor_type': sensor_type},
                sort=[('timestamp', -1)]
            )
            if doc:
                doc['id'] = str(doc['_id'])
                del doc['_id']
                latest_readings[sensor_type] = doc
        
        return latest_readings
    
    async def save_profile(self, profile_data: Dict[str, Any]) -> str:
        """Salvar perfil do paciente"""
        if not self.initialized:
            await self.initialize()
        
        profile_data['updated_at'] = datetime.utcnow()
        
        # Verificar se já existe
        existing = await self.db.patient_profiles.find_one()
        if existing:
            await self.db.patient_profiles.update_one(
                {'_id': existing['_id']},
                {'$set': profile_data}
            )
            return str(existing['_id'])
        else:
            profile_data['created_at'] = datetime.utcnow()
            result = await self.db.patient_profiles.insert_one(profile_data)
            return str(result.inserted_id)
    
    async def get_profile(self) -> Optional[Dict[str, Any]]:
        """Buscar perfil do paciente"""
        if not self.initialized:
            await self.initialize()
        
        doc = await self.db.patient_profiles.find_one()
        if doc:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            return doc
        return None
    
    async def save_alert(self, alert_data: Dict[str, Any]) -> str:
        """Salvar alerta"""
        if not self.initialized:
            await self.initialize()
        
        if 'timestamp' not in alert_data:
            alert_data['timestamp'] = datetime.utcnow()
        
        result = await self.db.alerts.insert_one(alert_data)
        return str(result.inserted_id)
    
    async def get_alerts(self, limit: int = 20, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Buscar alertas"""
        if not self.initialized:
            await self.initialize()
        
        query = {}
        if resolved is not None:
            query['resolved'] = resolved
        
        cursor = self.db.alerts.find(query).sort('timestamp', -1).limit(limit)
        
        results = []
        async for doc in cursor:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            results.append(doc)
        
        return results
    
    async def save_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Salvar análise IA"""
        if not self.initialized:
            await self.initialize()
        
        if 'timestamp' not in analysis_data:
            analysis_data['timestamp'] = datetime.utcnow()
        
        result = await self.db.ai_analyses.insert_one(analysis_data)
        return str(result.inserted_id)
    
    async def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """Buscar última análise"""
        if not self.initialized:
            await self.initialize()
        
        doc = await self.db.ai_analyses.find_one(sort=[('timestamp', -1)])
        if doc:
            doc['id'] = str(doc['_id'])
            del doc['_id']
            return doc
        return None
    
    async def cleanup_demo_data(self) -> int:
        """Limpar dados demo"""
        if not self.initialized:
            await self.initialize()
        
        collections = ['vital_signs', 'alerts', 'ai_analyses']
        total_deleted = 0
        
        for collection_name in collections:
            result = await self.db[collection_name].delete_many({})
            total_deleted += result.deleted_count
        
        return total_deleted

# Instância global
mongodb_fallback = MongoDBFallback()