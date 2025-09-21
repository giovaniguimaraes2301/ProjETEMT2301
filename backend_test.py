#!/usr/bin/env python3
"""
VitalTech Backend Testing Suite
Tests all backend API endpoints and functionality
"""

import asyncio
import aiohttp
import json
import sys
import os
import subprocess
import time
import signal
from datetime import datetime
from typing import Dict, Any, Optional

# Test configuration
BACKEND_URL = "https://vitaltech-monitor.preview.emergentagent.com/api"
LOCAL_BACKEND_URL = "http://localhost:8001/api"
TEST_TIMEOUT = 30

class VitalTechBackendTester:
    def __init__(self):
        self.session = None
        self.server_process = None
        self.test_results = []
        self.backend_url = BACKEND_URL  # Use production URL by default
        
    async def setup(self):
        """Setup test environment"""
        print("🔧 Setting up VitalTech Backend Tests...")
        
        # Create aiohttp session
        timeout = aiohttp.ClientTimeout(total=TEST_TIMEOUT)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        print(f"📡 Testing backend at: {self.backend_url}")
        
    async def cleanup(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
            
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
                
    def log_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
        
    async def test_server_startup(self):
        """Test 1: Verify backend server starts correctly"""
        print("\n🚀 Testing Backend Server Startup...")
        
        try:
            # Test if we can start the server locally
            print("Testing local server startup with 'python server.py'...")
            
            # Change to backend directory
            os.chdir('/app/backend')
            
            # Try to start server in background
            cmd = [sys.executable, 'server.py']
            self.server_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a bit for server to start
            await asyncio.sleep(3)
            
            # Check if process is still running
            if self.server_process.poll() is None:
                self.log_result("Server Startup", True, "Server started successfully without errors")
                
                # Try to connect to local server
                try:
                    async with self.session.get(f"{LOCAL_BACKEND_URL}/health") as response:
                        if response.status == 200:
                            self.log_result("Local Server Connection", True, "Successfully connected to local server")
                            self.backend_url = LOCAL_BACKEND_URL  # Switch to local for remaining tests
                        else:
                            self.log_result("Local Server Connection", False, f"Local server returned status {response.status}")
                except Exception as e:
                    self.log_result("Local Server Connection", False, f"Could not connect to local server: {str(e)}")
                    
            else:
                # Get error output
                stdout, stderr = self.server_process.communicate()
                error_msg = stderr if stderr else stdout
                self.log_result("Server Startup", False, f"Server failed to start: {error_msg}")
                
        except Exception as e:
            self.log_result("Server Startup", False, f"Error starting server: {str(e)}")
            
    async def test_basic_endpoints(self):
        """Test 2: Test basic API endpoints"""
        print("\n🔍 Testing Basic API Endpoints...")
        
        endpoints = [
            ("/", "Root endpoint"),
            ("/health", "Health check endpoint"),
            ("/vital-signs", "Vital signs endpoint")
        ]
        
        for endpoint, description in endpoints:
            try:
                url = f"{self.backend_url}{endpoint}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_result(f"GET {endpoint}", True, f"{description} working", {"response": data})
                    else:
                        self.log_result(f"GET {endpoint}", False, f"{description} returned status {response.status}")
                        
            except Exception as e:
                self.log_result(f"GET {endpoint}", False, f"Error testing {description}: {str(e)}")
                
    async def test_health_check_details(self):
        """Test 3: Detailed health check verification"""
        print("\n💓 Testing Health Check Details...")
        
        try:
            async with self.session.get(f"{self.backend_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check required fields
                    required_fields = ["status", "timestamp", "database", "simulation"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        self.log_result("Health Check Structure", True, "All required fields present", data)
                        
                        # Check database status
                        db_status = data.get("database", "unknown")
                        if "mongodb" in db_status.lower():
                            self.log_result("Database Connection", True, f"Database status: {db_status}")
                        else:
                            self.log_result("Database Connection", False, f"Unexpected database status: {db_status}")
                            
                        # Check simulation status
                        sim_status = data.get("simulation", "unknown")
                        self.log_result("Simulation Status", True, f"Simulation status: {sim_status}")
                        
                    else:
                        self.log_result("Health Check Structure", False, f"Missing fields: {missing_fields}")
                        
                else:
                    self.log_result("Health Check", False, f"Health endpoint returned status {response.status}")
                    
        except Exception as e:
            self.log_result("Health Check", False, f"Error testing health check: {str(e)}")
            
    async def test_esp32_endpoint(self):
        """Test 4: Test ESP32 data endpoint"""
        print("\n📡 Testing ESP32 Data Endpoint...")
        
        # Test ESP32 data submission
        test_esp32_data = {
            "bpm": 75.5,
            "spo2": 98.2,
            "temperature": 36.8,
            "pressure": 120,
            "gsr": 450,
            "device_id": "test_esp32",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with self.session.post(
                f"{self.backend_url}/esp32/data",
                json=test_esp32_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("ESP32 Data Submission", True, "ESP32 data accepted", data)
                else:
                    error_text = await response.text()
                    self.log_result("ESP32 Data Submission", False, f"ESP32 endpoint returned {response.status}: {error_text}")
                    
        except Exception as e:
            self.log_result("ESP32 Data Submission", False, f"Error testing ESP32 endpoint: {str(e)}")
            
        # Test ESP32 status endpoint
        try:
            async with self.session.get(f"{self.backend_url}/esp32/status") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("ESP32 Status Check", True, "ESP32 status endpoint working", data)
                else:
                    self.log_result("ESP32 Status Check", False, f"ESP32 status returned {response.status}")
                    
        except Exception as e:
            self.log_result("ESP32 Status Check", False, f"Error testing ESP32 status: {str(e)}")
            
    async def test_vital_signs_crud(self):
        """Test 5: Test vital signs CRUD operations"""
        print("\n📊 Testing Vital Signs CRUD Operations...")
        
        # Test POST vital sign
        test_vital_sign = {
            "sensor_type": "heart_rate",
            "value": 72.0,
            "unit": "bpm",
            "device_id": "test_device",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with self.session.post(
                f"{self.backend_url}/vital-signs",
                json=test_vital_sign
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Vital Signs POST", True, "Vital sign saved successfully", data)
                else:
                    error_text = await response.text()
                    self.log_result("Vital Signs POST", False, f"POST vital-signs returned {response.status}: {error_text}")
                    
        except Exception as e:
            self.log_result("Vital Signs POST", False, f"Error posting vital sign: {str(e)}")
            
        # Test GET vital signs
        try:
            async with self.session.get(f"{self.backend_url}/vital-signs?limit=10") as response:
                if response.status == 200:
                    data = await response.json()
                    vital_signs = data.get("vital_signs", [])
                    self.log_result("Vital Signs GET", True, f"Retrieved {len(vital_signs)} vital signs", {"count": len(vital_signs)})
                else:
                    self.log_result("Vital Signs GET", False, f"GET vital-signs returned {response.status}")
                    
        except Exception as e:
            self.log_result("Vital Signs GET", False, f"Error getting vital signs: {str(e)}")
            
        # Test GET latest vital signs
        try:
            async with self.session.get(f"{self.backend_url}/vital-signs/latest") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Latest Vital Signs", True, "Latest vital signs retrieved", data)
                else:
                    self.log_result("Latest Vital Signs", False, f"GET latest vital-signs returned {response.status}")
                    
        except Exception as e:
            self.log_result("Latest Vital Signs", False, f"Error getting latest vital signs: {str(e)}")
            
    async def test_simulation_functionality(self):
        """Test 6: Test data simulation functionality"""
        print("\n🎲 Testing Data Simulation Functionality...")
        
        # Test simulation start
        try:
            async with self.session.post(f"{self.backend_url}/simulation/start") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Simulation Start", True, "Simulation started successfully", data)
                else:
                    error_text = await response.text()
                    self.log_result("Simulation Start", False, f"Simulation start returned {response.status}: {error_text}")
                    
        except Exception as e:
            self.log_result("Simulation Start", False, f"Error starting simulation: {str(e)}")
            
        # Wait a bit for simulation to generate data
        await asyncio.sleep(2)
        
        # Test simulation stop
        try:
            async with self.session.post(f"{self.backend_url}/simulation/stop") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Simulation Stop", True, "Simulation stopped successfully", data)
                else:
                    self.log_result("Simulation Stop", False, f"Simulation stop returned {response.status}")
                    
        except Exception as e:
            self.log_result("Simulation Stop", False, f"Error stopping simulation: {str(e)}")
            
    async def test_ai_analysis(self):
        """Test 7: Test AI analysis functionality"""
        print("\n🧠 Testing AI Analysis Functionality...")
        
        # Test AI analysis run
        try:
            async with self.session.post(f"{self.backend_url}/analysis/run") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("AI Analysis Run", True, "AI analysis executed successfully", data)
                else:
                    error_text = await response.text()
                    self.log_result("AI Analysis Run", False, f"AI analysis returned {response.status}: {error_text}")
                    
        except Exception as e:
            self.log_result("AI Analysis Run", False, f"Error running AI analysis: {str(e)}")
            
        # Test latest analysis
        try:
            async with self.session.get(f"{self.backend_url}/analysis/latest") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Latest AI Analysis", True, "Latest analysis retrieved", data)
                else:
                    self.log_result("Latest AI Analysis", False, f"Latest analysis returned {response.status}")
                    
        except Exception as e:
            self.log_result("Latest AI Analysis", False, f"Error getting latest analysis: {str(e)}")
            
    async def test_profile_management(self):
        """Test 8: Test patient profile management"""
        print("\n👤 Testing Patient Profile Management...")
        
        # Test GET profile
        try:
            async with self.session.get(f"{self.backend_url}/profile") as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Profile GET", True, "Profile retrieved successfully", data)
                else:
                    self.log_result("Profile GET", False, f"Profile GET returned {response.status}")
                    
        except Exception as e:
            self.log_result("Profile GET", False, f"Error getting profile: {str(e)}")
            
        # Test POST profile
        test_profile = {
            "nome": "João Silva",
            "idade": 35,
            "genero": "masculino",
            "altura": 175.0,
            "peso": 70.0
        }
        
        try:
            async with self.session.post(
                f"{self.backend_url}/profile",
                json=test_profile
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("Profile POST", True, "Profile saved successfully", data)
                else:
                    error_text = await response.text()
                    self.log_result("Profile POST", False, f"Profile POST returned {response.status}: {error_text}")
                    
        except Exception as e:
            self.log_result("Profile POST", False, f"Error saving profile: {str(e)}")
            
    async def test_alerts_system(self):
        """Test 9: Test alerts system"""
        print("\n🚨 Testing Alerts System...")
        
        try:
            async with self.session.get(f"{self.backend_url}/alerts?limit=10") as response:
                if response.status == 200:
                    data = await response.json()
                    alerts = data.get("alerts", [])
                    self.log_result("Alerts GET", True, f"Retrieved {len(alerts)} alerts", {"count": len(alerts)})
                else:
                    self.log_result("Alerts GET", False, f"Alerts GET returned {response.status}")
                    
        except Exception as e:
            self.log_result("Alerts GET", False, f"Error getting alerts: {str(e)}")
            
    async def test_reports_functionality(self):
        """Test 10: Test reports functionality"""
        print("\n📋 Testing Reports Functionality...")
        
        periods = ["daily", "weekly", "monthly"]
        
        for period in periods:
            try:
                async with self.session.get(f"{self.backend_url}/reports/data/{period}") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_result(f"Report {period.title()}", True, f"{period.title()} report generated", {"period": period})
                    else:
                        self.log_result(f"Report {period.title()}", False, f"{period.title()} report returned {response.status}")
                        
            except Exception as e:
                self.log_result(f"Report {period.title()}", False, f"Error generating {period} report: {str(e)}")
                
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🧪 Starting VitalTech Backend Test Suite")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Run all tests
            await self.test_server_startup()
            await self.test_basic_endpoints()
            await self.test_health_check_details()
            await self.test_esp32_endpoint()
            await self.test_vital_signs_crud()
            await self.test_simulation_functionality()
            await self.test_ai_analysis()
            await self.test_profile_management()
            await self.test_alerts_system()
            await self.test_reports_functionality()
            
        finally:
            await self.cleanup()
            
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
                    
        print("\n📊 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}: {result['message']}")

async def main():
    """Main test runner"""
    tester = VitalTechBackendTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())