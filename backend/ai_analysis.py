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
model = genai.GenerativeModel('gemini-1.5-flash')

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
            # Preparar dados para análise
            analysis_data = self._prepare_analysis_data(vital_signs, patient_profile)
            
            # Gerar prompt para IA
            prompt = self._generate_analysis_prompt(analysis_data)
            
            # Executar análise com Gemini
            response = await self._execute_gemini_analysis(prompt)
            
            # Processar resposta e gerar alertas
            analysis_result = self._process_gemini_response(response, vital_signs)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Erro na análise IA: {e}")
            return self._generate_fallback_analysis(vital_signs)
    
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
    
    def _generate_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Gerar prompt estruturado para o Gemini"""
        
        prompt = f"""
Você é um assistente médico especializado em análise de sinais vitais. Analise os seguintes dados:

DADOS DO PACIENTE:
{json.dumps(data.get('patient_profile', {}), indent=2, ensure_ascii=False)}

SINAIS VITAIS COLETADOS (últimos registros):
{json.dumps(data.get('statistics', {}), indent=2, ensure_ascii=False)}

CONTEXTO CLÍNICO:
- Total de leituras: {data.get('total_readings', 0)}
- Timestamp da análise: {data.get('timestamp', 'N/A')}

PARÂMETROS NORMAIS DE REFERÊNCIA:
- Frequência Cardíaca: 60-100 bpm
- Pressão Arterial: 90-140 mmHg  
- Saturação O2: 95-100%
- Temperatura: 36.0-37.5°C
- Resistência Galvânica: 200-800Ω

TAREFAS DE ANÁLISE:
1. Avalie cada sinal vital individualmente
2. Identifique valores fora dos parâmetros normais
3. Analise correlações entre os diferentes sinais
4. Identifique possíveis condições médicas baseadas na combinação de sinais
5. Forneça recomendações específicas

POSSÍVEIS CONDIÇÕES A CONSIDERAR:
- Taquicardia/Bradicardia
- Hipertensão/Hipotensão
- Hipóxia
- Febre/Hipotermia
- Estresse/Ansiedade (GSR elevado)
- Desidratação
- Arritmias
- Insuficiência cardíaca
- Problemas circulatórios

FORMATO DE RESPOSTA (JSON):
{{
    "health_status": "normal|attention|concerning|critical",
    "analysis_summary": "Resumo geral do estado de saúde",
    "individual_assessments": {{
        "heart_rate": "Avaliação específica da FC",
        "blood_pressure": "Avaliação específica da PA",
        "oxygen_saturation": "Avaliação específica da SpO2",
        "temperature": "Avaliação específica da temperatura",
        "gsr": "Avaliação específica da resistência galvânica"
    }},
    "combined_assessment": "Análise combinada dos sinais",
    "recommendations": ["Recomendação 1", "Recomendação 2", "..."],
    "alerts": [
        {{
            "level": "warning|critical|emergency",
            "title": "Título do alerta",
            "message": "Descrição detalhada",
            "sensor_type": "heart_rate|blood_pressure|etc"
        }}
    ],
    "confidence_score": 0.85
}}

Seja preciso, objetivo e focado na segurança do paciente. Use terminologia médica apropriada mas acessível.
"""
        return prompt
    
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
            # Tentar extrair JSON da resposta
            json_start = gemini_response.find('{')
            json_end = gemini_response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = gemini_response[json_start:json_end]
                ai_data = json.loads(json_str)
            else:
                # Fallback se não encontrar JSON válido
                ai_data = self._parse_text_response(gemini_response)
            
            # Criar alertas baseados na resposta IA
            alerts = []
            for alert_data in ai_data.get('alerts', []):
                alert = Alert(
                    level=AlertLevel(alert_data.get('level', 'warning')),
                    title=alert_data.get('title', 'Alerta IA'),
                    message=alert_data.get('message', 'Anomalia detectada'),
                    sensor_type=alert_data.get('sensor_type'),
                    ai_analysis=gemini_response[:500] + "..." if len(gemini_response) > 500 else gemini_response
                )
                alerts.append(alert)
            
            # Retornar análise estruturada
            return AIAnalysisResponse(
                analysis_summary=ai_data.get('analysis_summary', 'Análise realizada'),
                health_status=ai_data.get('health_status', 'normal'),
                individual_assessments=ai_data.get('individual_assessments', {}),
                combined_assessment=ai_data.get('combined_assessment', 'Sinais vitais analisados'),
                recommendations=ai_data.get('recommendations', []),
                alerts_generated=alerts,
                confidence_score=ai_data.get('confidence_score', 0.7)
            )
            
        except Exception as e:
            logger.error(f"Erro ao processar resposta Gemini: {e}")
            return self._generate_fallback_analysis(vital_signs)
    
    def _parse_text_response(self, text_response: str) -> Dict[str, Any]:
        """Parse fallback para respostas não-JSON"""
        return {
            "health_status": "attention",
            "analysis_summary": f"Análise realizada: {text_response[:200]}...",
            "individual_assessments": {},
            "combined_assessment": "Análise baseada em resposta textual",
            "recommendations": ["Consultar médico se sintomas persistirem"],
            "alerts": [],
            "confidence_score": 0.5
        }
    
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
            analysis_summary="Análise baseada em regras de fallback",
            health_status="attention" if alerts else "normal",
            individual_assessments=assessments,
            combined_assessment="Análise realizada por regras automáticas",
            recommendations=["Monitorar sinais vitais", "Consultar médico se necessário"],
            alerts_generated=alerts,
            confidence_score=0.6
        )

# Instância global do analisador
analyzer = VitalSignsAnalyzer()