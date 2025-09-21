#!/usr/bin/env python3
"""
Bridge Bluetooth para ESP32 VitalTech
Conecta via BLE ao ESP32 e envia dados para a API web
"""

import asyncio
import requests
import json
import time
from datetime import datetime
import logging

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    print("❌ Erro: Instale a biblioteca bleak")
    print("Execute: pip install bleak requests")
    exit(1)

# Configurações
ESP32_NAME = "ESP32_S3_Health"
SERVICE_UUID = "49535343-FE7D-4AE5-8FA9-9FAFD205E455"
API_URL = "https://vitaltech-monitor.preview.emergentagent.com/api/esp32/data"

# UUIDs das características
CHAR_BPM = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_SPO2 = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_TEMP = "6E400004-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_PRESS = "6E400005-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_GSR = "6E400006-B5A3-F393-E0A9-E50E24DCCA9E"

# Características MPU6050
CHAR_AX = "6E400007-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_AY = "6E400008-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_AZ = "6E400009-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_GX = "6E40000A-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_GY = "6E40000B-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_GZ = "6E40000C-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_PITCH = "6E40000D-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_ROLL = "6E40000E-B5A3-F393-E0A9-E50E24DCCA9E"
CHAR_YAW = "6E40000F-B5A3-F393-E0A9-E50E24DCCA9E"

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ESP32Bridge:
    def __init__(self):
        self.sensor_data = {}
        self.mpu_data = {}
        self.last_send_time = 0
        self.send_interval = 3.0  # Enviar a cada 3 segundos
        
    def notification_handler(self, sender, data):
        """Manipular notificações BLE do ESP32"""
        try:
            value = data.decode('utf-8').strip()
            uuid = sender.uuid
            
            # Sensores principais
            if uuid == CHAR_BPM:
                self.sensor_data['bpm'] = float(value)
                logger.debug(f"BPM: {value}")
            elif uuid == CHAR_SPO2:
                self.sensor_data['spo2'] = float(value)
                logger.debug(f"SpO2: {value}")
            elif uuid == CHAR_TEMP:
                self.sensor_data['temperature'] = float(value)
                logger.debug(f"Temperatura: {value}")
            elif uuid == CHAR_PRESS:
                self.sensor_data['pressure'] = float(value)
                logger.debug(f"Pressão: {value}")
            elif uuid == CHAR_GSR:
                self.sensor_data['gsr'] = float(value)
                logger.debug(f"GSR: {value}")
            
            # Dados MPU6050
            elif uuid == CHAR_AX:
                self.mpu_data['ax'] = float(value)
            elif uuid == CHAR_AY:
                self.mpu_data['ay'] = float(value)
            elif uuid == CHAR_AZ:
                self.mpu_data['az'] = float(value)
            elif uuid == CHAR_GX:
                self.mpu_data['gx'] = float(value)
            elif uuid == CHAR_GY:
                self.mpu_data['gy'] = float(value)
            elif uuid == CHAR_GZ:
                self.mpu_data['gz'] = float(value)
            elif uuid == CHAR_PITCH:
                self.mpu_data['pitch'] = float(value)
            elif uuid == CHAR_ROLL:
                self.mpu_data['roll'] = float(value)
            elif uuid == CHAR_YAW:
                self.mpu_data['yaw'] = float(value)
            
            # Verificar se é hora de enviar dados
            current_time = time.time()
            if current_time - self.last_send_time >= self.send_interval:
                self.send_to_api()
                self.last_send_time = current_time
                
        except Exception as e:
            logger.error(f"Erro ao processar notificação: {e}")

    def send_to_api(self):
        """Enviar dados para a API web"""
        try:
            # Preparar dados completos
            full_data = {
                **self.sensor_data,
                **self.mpu_data,
                'device_id': 'esp32_real',
                'timestamp': datetime.now().isoformat()
            }
            
            # Enviar apenas se tiver dados suficientes
            if len(self.sensor_data) >= 2:  # Pelo menos 2 sensores
                response = requests.post(API_URL, json=full_data, timeout=5)
                if response.status_code == 200:
                    logger.info(f"✅ Dados enviados: BPM={self.sensor_data.get('bpm', 'N/A')}, SpO2={self.sensor_data.get('spo2', 'N/A')}, Temp={self.sensor_data.get('temperature', 'N/A')}")
                else:
                    logger.warning(f"❌ Erro API: {response.status_code} - {response.text}")
            else:
                logger.debug("Aguardando mais dados dos sensores...")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erro de conexão com API: {e}")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar dados: {e}")

    async def find_esp32(self):
        """Buscar ESP32 via Bluetooth"""
        logger.info("🔍 Procurando ESP32...")
        
        try:
            devices = await BleakScanner.discover(timeout=10.0)
            
            for device in devices:
                if device.name and ESP32_NAME in device.name:
                    logger.info(f"✅ ESP32 encontrado: {device.name} ({device.address})")
                    return device
            
            logger.warning(f"❌ ESP32 '{ESP32_NAME}' não encontrado")
            logger.info("Dispositivos disponíveis:")
            for device in devices:
                if device.name:
                    logger.info(f"  - {device.name} ({device.address})")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar dispositivos: {e}")
            return None

    async def connect_and_receive(self):
        """Conectar ao ESP32 e receber dados"""
        esp32_device = await self.find_esp32()
        
        if not esp32_device:
            return False
        
        try:
            async with BleakClient(esp32_device.address) as client:
                logger.info(f"🔗 Conectado ao ESP32: {esp32_device.name}")
                
                # Verificar se o serviço existe
                services = await client.get_services()
                service_found = False
                for service in services:
                    if service.uuid.upper() == SERVICE_UUID.upper():
                        service_found = True
                        break
                
                if not service_found:
                    logger.error(f"❌ Serviço {SERVICE_UUID} não encontrado")
                    return False
                
                # Inscrever-se nas notificações dos sensores principais
                characteristics = [
                    CHAR_BPM, CHAR_SPO2, CHAR_TEMP, CHAR_PRESS, CHAR_GSR
                ]
                
                # Adicionar características MPU6050
                mpu_characteristics = [
                    CHAR_AX, CHAR_AY, CHAR_AZ, CHAR_GX, CHAR_GY, CHAR_GZ,
                    CHAR_PITCH, CHAR_ROLL, CHAR_YAW
                ]
                
                all_characteristics = characteristics + mpu_characteristics
                
                connected_chars = 0
                for char_uuid in all_characteristics:
                    try:
                        await client.start_notify(char_uuid, self.notification_handler)
                        connected_chars += 1
                        logger.debug(f"Inscrito na característica: {char_uuid}")
                    except Exception as e:
                        logger.warning(f"Não foi possível se inscrever em {char_uuid}: {e}")
                
                logger.info(f"📡 Inscrito em {connected_chars}/{len(all_characteristics)} características")
                logger.info("🎯 Recebendo dados... (Ctrl+C para parar)")
                
                # Manter conexão ativa
                try:
                    while True:
                        await asyncio.sleep(1)
                        
                        # Verificar se ainda está conectado
                        if not client.is_connected:
                            logger.warning("⚠️ Conexão perdida")
                            break
                            
                except KeyboardInterrupt:
                    logger.info("🛑 Parando bridge...")
                    
                return True
                
        except Exception as e:
            logger.error(f"❌ Erro de conexão: {e}")
            return False

async def main():
    """Função principal"""
    bridge = ESP32Bridge()
    
    logger.info("🚀 VitalTech ESP32 Bridge iniciado")
    logger.info(f"📡 Procurando: {ESP32_NAME}")
    logger.info(f"🌐 API: {API_URL}")
    
    max_attempts = 5
    attempt = 1
    
    while attempt <= max_attempts:
        logger.info(f"🔄 Tentativa {attempt}/{max_attempts}")
        
        success = await bridge.connect_and_receive()
        
        if success:
            logger.info("✅ Sessão concluída com sucesso")
        else:
            logger.warning(f"❌ Falha na tentativa {attempt}")
            
        if attempt < max_attempts:
            logger.info("⏳ Aguardando 10 segundos antes da próxima tentativa...")
            await asyncio.sleep(10)
            
        attempt += 1
    
    logger.info("🔚 Bridge finalizado")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bridge interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")