#!/usr/bin/env python3
"""
Bridge BLE ESP32 -> HTTP VitalTech
Usa ble-serial para capturar dados do ESP32 e enviar para API
"""

import asyncio
import json
import re
import requests
import time
from datetime import datetime
import logging
import argparse

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VitalTechBLEBridge:
    def __init__(self, api_url="http://localhost:8001/api", device_name="ESP32_S3_Health"):
        self.api_url = api_url
        self.device_name = device_name
        self.last_data = {}
        self.session = requests.Session()
        
    def parse_esp32_data(self, ble_data):
        """Parse dados recebidos do ESP32 via BLE"""
        try:
            # Dados vêm como string do BLE
            data_str = ble_data.decode('utf-8').strip()
            logger.debug(f"Dados recebidos: {data_str}")
            
            # Tentar extrair valores usando regex
            patterns = {
                'bpm': r'BPM:(\d+\.?\d*)',
                'spo2': r'SpO2:(\d+\.?\d*)',
                'temperature': r'TEMP:(\d+\.?\d*)',
                'pressure': r'PRESS:(\d+\.?\d*)',
                'gsr': r'GSR:(\d+\.?\d*)'
            }
            
            parsed_data = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, data_str)
                if match:
                    parsed_data[key] = float(match.group(1))
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Erro ao parsear dados: {e}")
            return {}
    
    def send_to_api(self, data):
        """Enviar dados para API VitalTech"""
        try:
            if not data:
                return False
                
            # Adicionar timestamp
            data['timestamp'] = datetime.utcnow().isoformat()
            data['device_id'] = 'esp32_real'
            
            response = self.session.post(
                f"{self.api_url}/esp32/data",
                json=data,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Dados enviados com sucesso: {data}")
                return True
            else:
                logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao enviar dados: {e}")
            return False
    
    async def run_bridge(self):
        """Loop principal do bridge"""
        logger.info(f"Iniciando bridge para dispositivo: {self.device_name}")
        
        try:
            # Importar ble-serial (instalar com: pip install ble-serial)
            from ble_serial.scan import scan_for_devices
            from ble_serial.ble_interface import BleInterface
            
            # Escanear dispositivos
            logger.info("Escaneando dispositivos BLE...")
            devices = await scan_for_devices(timeout=10)
            
            # Encontrar ESP32
            esp32_device = None
            for device in devices:
                if self.device_name in device.name:
                    esp32_device = device
                    break
            
            if not esp32_device:
                logger.error(f"Dispositivo {self.device_name} não encontrado")
                return
            
            logger.info(f"Conectando ao {esp32_device.name} ({esp32_device.address})")
            
            # Conectar ao dispositivo
            ble_interface = BleInterface(esp32_device.address)
            await ble_interface.connect()
            
            logger.info("Conectado! Aguardando dados...")
            
            # Loop de recepção de dados
            while True:
                try:
                    # Ler dados do BLE
                    data = await ble_interface.read(timeout=5)
                    
                    if data:
                        # Parsear dados
                        parsed_data = self.parse_esp32_data(data)
                        
                        if parsed_data:
                            # Enviar para API
                            success = self.send_to_api(parsed_data)
                            
                            if success:
                                self.last_data = parsed_data
                    
                    await asyncio.sleep(0.1)
                    
                except asyncio.TimeoutError:
                    logger.debug("Timeout na leitura - aguardando...")
                    continue
                except Exception as e:
                    logger.error(f"Erro no loop principal: {e}")
                    await asyncio.sleep(1)
                    
        except ImportError:
            logger.error("ble-serial não instalado. Instale com: pip install ble-serial")
        except Exception as e:
            logger.error(f"Erro geral: {e}")
    
    def run_simulation_mode(self):
        """Modo simulação para teste sem ESP32"""
        logger.info("Executando em modo simulação")
        
        import random
        
        while True:
            try:
                # Gerar dados simulados
                simulated_data = {
                    'bpm': round(random.uniform(60, 100), 1),
                    'spo2': round(random.uniform(95, 99), 1),
                    'temperature': round(random.uniform(36.0, 37.5), 1),
                    'pressure': random.randint(90, 140),
                    'gsr': round(random.uniform(200, 800), 2)
                }
                
                # Enviar para API
                self.send_to_api(simulated_data)
                
                time.sleep(3)  # Intervalo de 3 segundos
                
            except KeyboardInterrupt:
                logger.info("Simulação interrompida")
                break
            except Exception as e:
                logger.error(f"Erro na simulação: {e}")
                time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description='VitalTech BLE Bridge')
    parser.add_argument('--api-url', default='http://localhost:8001/api', help='URL da API VitalTech')
    parser.add_argument('--device', default='ESP32_S3_Health', help='Nome do dispositivo ESP32')
    parser.add_argument('--simulate', action='store_true', help='Executar simulação sem ESP32')
    
    args = parser.parse_args()
    
    bridge = VitalTechBLEBridge(args.api_url, args.device)
    
    try:
        if args.simulate:
            bridge.run_simulation_mode()
        else:
            asyncio.run(bridge.run_bridge())
    except KeyboardInterrupt:
        logger.info("Bridge interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}")

if __name__ == "__main__":
    main()