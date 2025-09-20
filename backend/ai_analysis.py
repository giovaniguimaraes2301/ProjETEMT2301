import google.generativeai as genai
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
from models import Alert, AlertLevel, AIAnalysisResponse, SensorType
import logging

# Configurar Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Usar modelo mais simples para evitar problemas de autenticação
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    AI_ENABLED = True
except Exception as e:
    logging.warning(f"Erro ao configurar Gemini: {e}")
    AI_ENABLED = False
    model = None

logger = logging.getLogger(__name__)

class VitalSignsAnalyzer:
    """Analisador de sinais vitais usando Google Gemini"""
    
    def __init__(self):
        self.thresholds = {
            "heart_rate": {"normal": (60, 100), "warning": (50, 120), "critical": (40, 150)},
            "blood_pressure": {"normal": (90, 140), "warning": (80, 160), "critical": (70, 180)},
            "oxygen_saturation": {"normal": (95, 100), "warning": (90, 94), "critical": (0, 89)},
            "temperature": {"normal": (36.0, 37.5), "warning": (35.0, 38.5), "critical": (34.0, 40.0)},
            "gsr": {"normal": (200, 800), "warning": (100, 1000), "critical": (50, 1500)}
        }
    
    async def analyze_vital_signs(self, vital_signs: List[Dict[str, Any]], 
                                patient_profile: Optional[Dict[str, Any]] = None) -> AIAnalysisResponse:
        """Análise completa dos sinais vitais usando IA"""
        try:
            # Se IA não está disponível, usar análise por regras
            if not AI_ENABLED:
                logger.info("IA não disponível, usando análise por regras")
                return self._generate_fallback_analysis(vital_signs)
            
            # Preparar dados para análise
            analysis_data = self._prepare_analysis_data(vital_signs, patient_profile)
            
            # Gerar prompt para IA  
            prompt = self._generate_simple_prompt(analysis_data)
            
            # Executar análise com Gemini (com timeout)
            try:
                response = await asyncio.wait_for(
                    self._execute_gemini_analysis(prompt), 
                    timeout=10.0
                )
                # Processar resposta e gerar alertas
                analysis_result = self._process_gemini_response(response, vital_signs)
                return analysis_result
            except asyncio.TimeoutError:
                logger.warning("Timeout na análise IA, usando fallback")
                return self._generate_fallback_analysis(vital_signs)
            
        except Exception as e:
            logger.error(f"Erro na análise IA: {e}")
            return self._generate_fallback_analysis(vital_signs)
    
    def _generate_simple_prompt(self, data: Dict[str, Any]) -> str:
        """Gerar prompt simples para evitar problemas"""
        return f"""
Analise estes sinais vitais básicos:
{json.dumps(data.get('statistics', {}), indent=2)}

Responda apenas: NORMAL, ATENÇÃO ou CRÍTICO
"""
    
    def _prepare_analysis_data(self, vital_signs: List[Dict[str, Any]], 
                             patient_profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Preparar dados estruturados para análise"""
        
        # Agrupar por tipo de sensor
        grouped_data = {}
        for reading in vital_signs:
            sensor_type = reading.get('sensor_type', 'unknown')
            if sensor_type not in grouped_data:
                grouped_data[sensor_type] = []
            grouped_data[sensor_type].append(reading)
        
        # Calcular estatísticas básicas
        stats = {}
        for sensor_type, readings in grouped_data.items():
            values = [r['value'] for r in readings if 'value' in r]
            if values:
                stats[sensor_type] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1],
                    "trend": self._calculate_trend(values)
                }
        
        return {
            "grouped_data": grouped_data,
            "statistics": stats,
            "patient_profile": patient_profile or {},
            "timestamp": datetime.utcnow().isoformat(),
            "total_readings": len(vital_signs)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcular tendência simples dos valores"""
        if len(values) < 2:
            return "stable"
        
        recent = values[-3:] if len(values) >= 3 else values
        if len(recent) < 2:
            return "stable"
            
        diff = recent[-1] - recent[0]
        if abs(diff) < 0.1:
            return "stable"
        elif diff > 0:
            return "increasing"
        else:
            return "decreasing"
    
    async def _execute_gemini_analysis(self, prompt: str) -> str:
        """Executar análise com Google Gemini"""
        try:
            # Executar em thread separada para não bloquear
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: model.generate_content(prompt)
            )
            return response.text
        except Exception as e:
            logger.error(f"Erro ao executar Gemini: {e}")
            raise
    
    def _process_gemini_response(self, gemini_response: str, 
                               vital_signs: List[Dict[str, Any]]) -> AIAnalysisResponse:
        """Processar resposta do Gemini e criar objeto estruturado"""
        try:
            # Análise simples da resposta
            response_lower = gemini_response.lower()
            
            if 'crítico' in response_lower or 'critical' in response_lower:
                health_status = 'critical'
            elif 'atenção' in response_lower or 'attention' in response_lower:
                health_status = 'attention'
            else:
                health_status = 'normal'
            
            # Gerar alertas baseados na análise de regras também
            alerts = []
            rule_analysis = self._generate_fallback_analysis(vital_signs)
            alerts.extend(rule_analysis.alerts_generated)
            
            # Retornar análise estruturada
            return AIAnalysisResponse(
                analysis_summary=f"Análise IA: {gemini_response[:200]}...",
                health_status=health_status,
                individual_assessments=rule_analysis.individual_assessments,
                combined_assessment=f"Análise combinada: {health_status}",
                recommendations=["Monitorar sinais vitais", "Consultar médico se necessário"],
                alerts_generated=alerts,
                confidence_score=0.8
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta Gemini: {e}")
            return self._generate_fallback_analysis(vital_signs)
    
    def _generate_fallback_analysis(self, vital_signs: List[Dict[str, Any]]) -> AIAnalysisResponse:
        """Análise de fallback baseada em regras simples"""
        alerts = []
        assessments = {}
        
        # Análise básica por regras
        for reading in vital_signs[-10:]:  # Últimas 10 leituras
            sensor_type = reading.get('sensor_type')
            value = reading.get('value', 0)
            
            if sensor_type in self.thresholds:
                thresholds = self.thresholds[sensor_type]
                
                if not (thresholds['normal'][0] <= value <= thresholds['normal'][1]):
                    level = AlertLevel.WARNING
                    if not (thresholds['warning'][0] <= value <= thresholds['warning'][1]):
                        level = AlertLevel.CRITICAL
                    
                    alert = Alert(
                        level=level,
                        title=f"{sensor_type.replace('_', ' ').title()} Anômalo",
                        message=f"Valor {value} fora do normal ({thresholds['normal']})",
                        sensor_type=SensorType(sensor_type),
                        trigger_value=value
                    )
                    alerts.append(alert)
                
                assessments[sensor_type] = f"Valor atual: {value} - {'Normal' if thresholds['normal'][0] <= value <= thresholds['normal'][1] else 'Atenção'}"
        
        return AIAnalysisResponse(
            analysis_summary="Análise baseada em regras de segurança",
            health_status="attention" if alerts else "normal",
            individual_assessments=assessments,
            combined_assessment="Análise realizada por regras automáticas",
            recommendations=["Monitorar sinais vitais", "Consultar médico se necessário"],
            alerts_generated=alerts,
            confidence_score=0.7
        )

# Instância global do analisador
analyzer = VitalSignsAnalyzer()