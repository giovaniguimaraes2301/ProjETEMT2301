from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class SensorType(str, Enum):
    """Tipos de sensores suportados"""
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE = "blood_pressure"  
    OXYGEN_SATURATION = "oxygen_saturation"
    TEMPERATURE = "temperature"
    GSR = "gsr"  # Galvanic Skin Response
    POSTURE = "posture"  # MPU6050
    PRESSURE = "pressure"  # FSR402

class AlertLevel(str, Enum):
    """Níveis de alerta"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

# === SINAIS VITAIS ===
class VitalSign(BaseModel):
    """Modelo base para sinais vitais"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sensor_type: SensorType
    value: float
    unit: str
    device_id: str = "esp32_demo"  # ID fixo para demonstração
    raw_data: Optional[Dict[str, Any]] = None

class HeartRateReading(VitalSign):
    """Leitura de frequência cardíaca"""
    sensor_type: SensorType = SensorType.HEART_RATE
    unit: str = "bpm"
    
class BloodPressureReading(VitalSign):
    """Leitura de pressão arterial"""
    sensor_type: SensorType = SensorType.BLOOD_PRESSURE
    unit: str = "mmHg"
    systolic: Optional[float] = None
    diastolic: Optional[float] = None

class OxygenSaturationReading(VitalSign):
    """Leitura de saturação de oxigênio"""
    sensor_type: SensorType = SensorType.OXYGEN_SATURATION
    unit: str = "%"

class TemperatureReading(VitalSign):
    """Leitura de temperatura corporal"""
    sensor_type: SensorType = SensorType.TEMPERATURE
    unit: str = "°C"

class GSRReading(VitalSign):
    """Leitura de resistência galvânica da pele"""
    sensor_type: SensorType = SensorType.GSR
    unit: str = "Ω"

class PostureReading(VitalSign):
    """Leitura de postura/acelerômetro"""
    sensor_type: SensorType = SensorType.POSTURE
    unit: str = "degrees"
    x_axis: Optional[float] = None
    y_axis: Optional[float] = None
    z_axis: Optional[float] = None

# === PERFIL DO PACIENTE ===
class PatientProfile(BaseModel):
    """Perfil do paciente para uso único em feira"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str = "Visitante da Feira"
    idade: Optional[int] = None
    genero: Optional[str] = None
    altura: Optional[float] = None  # cm
    peso: Optional[float] = None    # kg
    grupo_sanguineo: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    cartao_saude: Optional[str] = None
    condicoes_medicas: Optional[str] = None
    alergias: Optional[str] = None
    medicacoes: Optional[str] = None
    contatos_emergencia: Optional[str] = None
    informacoes_adicionais: Optional[str] = None
    foto_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientProfileUpdate(BaseModel):
    """Modelo para atualização de perfil"""
    nome: Optional[str] = None
    idade: Optional[int] = None
    genero: Optional[str] = None
    altura: Optional[float] = None
    peso: Optional[float] = None
    grupo_sanguineo: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    endereco: Optional[str] = None
    cartao_saude: Optional[str] = None
    condicoes_medicas: Optional[str] = None
    alergias: Optional[str] = None
    medicacoes: Optional[str] = None
    contatos_emergencia: Optional[str] = None
    informacoes_adicionais: Optional[str] = None
    foto_url: Optional[str] = None

# === ALERTAS ===
class Alert(BaseModel):
    """Alerta médico gerado pela IA ou regras"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: AlertLevel
    title: str
    message: str
    sensor_type: Optional[SensorType] = None
    trigger_value: Optional[float] = None
    normal_range: Optional[str] = None
    recommendations: Optional[List[str]] = None
    ai_analysis: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

# === ANÁLISE IA ===
class AIAnalysisRequest(BaseModel):
    """Requisição para análise IA"""
    vital_signs: List[Dict[str, Any]]
    patient_profile: Optional[Dict[str, Any]] = None
    time_window: Optional[str] = "5m"  # 5 minutos, 1h, 24h, etc.

class AIAnalysisResponse(BaseModel):
    """Resposta da análise IA"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    analysis_summary: str
    health_status: str  # "normal", "attention", "concerning", "critical"
    individual_assessments: Dict[str, str]  # Por sensor
    combined_assessment: str
    recommendations: List[str]
    alerts_generated: List[Alert]
    confidence_score: float = 0.0

# === RELATÓRIOS ===
class ReportRequest(BaseModel):
    """Requisição para geração de relatórios"""
    period: str  # "daily", "weekly", "monthly"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_ai_analysis: bool = True
    format: str = "pdf"  # "pdf", "csv", "json"

class VitalSignsSummary(BaseModel):
    """Resumo dos sinais vitais para relatórios"""
    sensor_type: SensorType
    average: float
    minimum: float
    maximum: float
    count: int
    unit: str
    alerts_count: int

# === SIMULAÇÃO DE DADOS ===
class SimulationSettings(BaseModel):
    """Configurações para simulação de dados"""
    enabled: bool = True
    interval_seconds: int = 3
    realistic_variations: bool = True
    include_anomalies: bool = True
    anomaly_probability: float = 0.05  # 5% chance de anomalia