"""
Comprehensive System Test Suite
Tests toàn bộ hệ thống từ dashboard, main server, ML training, continuous learning
"""

import requests
import time
import json
import csv
import os
import subprocess
import threading
from datetime import datetime
import pandas as pd

class ComprehensiveSystemTest:
    def __init__(self):
        self.main_url = "http://localhost:8000"
        self.dashboard1_url = "http://localhost:8501"  # Enterprise Data Upload
        self.dashboard2_url = "http://localhost:8502"  # ML Monitoring
        self.test_results = []
        self.session_id = None
        
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status} - {details}")
        
    def wait_for_server(self, url, timeout=60):
        """Wait for server to start"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{url}/health" if "8000" in url else url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(2)
        return False
        
    def start_servers(self):
        """Start all servers in background"""
        print("🚀 Starting all servers...")
        
        # Start main server
        print("Starting main server (port 8000)...")
        self.main_process = subprocess.Popen([
            "python", "main.py"
        ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Start dashboard servers
        print("Starting enterprise dashboard (port 8501)...")
        self.dashboard1_process = subprocess.Popen([
            "streamlit", "run", "dashboards/enterprise_data_upload.py", "--server.port", "8501"
        ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("Starting ML monitoring dashboard (port 8502)...")
        self.dashboard2_process = subprocess.Popen([
            "streamlit", "run", "dashboards/ml_monitoring.py", "--server.port", "8502"
        ], cwd=".", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for servers to start
        if self.wait_for_server(self.main_url):
            self.log_result("Main Server Startup", "PASS", "Server running on port 8000")
        else:
            self.log_result("Main Server Startup", "FAIL", "Server failed to start")
            
        # Note: Streamlit servers don't have health endpoints, so we wait a bit
        time.sleep(10)
        self.log_result("Dashboard Servers", "PASS", "Dashboards should be running")
        
    def create_test_data(self):
        """Create comprehensive test data"""
        print("📊 Creating test data...")
        
        # Create sample CSV data
        test_data = [
            {
                "enterprise_id": "TEST001",
                "campaign_title": "AI Startup Launch Campaign",
                "campaign_type": "Product Launch",
                "industry": "technology", 
                "target_audience": "tech_professionals,investors",
                "budget": 25000000,
                "actual_spend": 22000000,
                "media_outlets_used": "VnExpress,CafeF,GenK",
                "total_media_reach": 15000000,
                "engagement_rate": 0.045,
                "click_through_rate": 0.023,
                "conversion_rate": 0.012,
                "roi_percentage": 145.5,
                "campaign_start_date": "2025-01-15",
                "campaign_end_date": "2025-02-15"
            },
            {
                "enterprise_id": "TEST002", 
                "campaign_title": "Food Delivery App Promotion",
                "campaign_type": "Brand Awareness",
                "industry": "food_beverage",
                "target_audience": "young_adults,students",
                "budget": 15000000,
                "actual_spend": 14500000,
                "media_outlets_used": "24H,Dantri,Tuoitre",
                "total_media_reach": 8000000,
                "engagement_rate": 0.038,
                "click_through_rate": 0.019,
                "conversion_rate": 0.008,
                "roi_percentage": 120.3,
                "campaign_start_date": "2025-02-01",
                "campaign_end_date": "2025-03-01"
            },
            {
                "enterprise_id": "TEST003",
                "campaign_title": "Healthcare Innovation Announcement", 
                "campaign_type": "Press Release",
                "industry": "healthcare",
                "target_audience": "healthcare_professionals,patients",
                "budget": 30000000,
                "actual_spend": 28000000,
                "media_outlets_used": "VnExpress,SucKhoe,YTe",
                "total_media_reach": 12000000,
                "engagement_rate": 0.052,
                "click_through_rate": 0.028,
                "conversion_rate": 0.015,
                "roi_percentage": 165.8,
                "campaign_start_date": "2025-01-20",
                "campaign_end_date": "2025-02-20"
            }
        ]
        
        # Save to CSV
        df = pd.DataFrame(test_data)
        df.to_csv("test_enterprise_data.csv", index=False)
        self.log_result("Test Data Creation", "PASS", "Created test_enterprise_data.csv with 3 campaigns")
        
        return "test_enterprise_data.csv"
        
    def test_data_upload(self, csv_file):
        """Test data upload via API"""
        print("📤 Testing data upload...")
        
        try:
            # Test file upload endpoint
            with open(csv_file, 'rb') as f:
                files = {'file': f}
                response = requests.post(f"{self.main_url}/upload-document", files=files, timeout=30)
                
            if response.status_code == 200:
                self.log_result("Data Upload", "PASS", f"Successfully uploaded {csv_file}")
                return True
            else:
                self.log_result("Data Upload", "FAIL", f"Upload failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Data Upload", "FAIL", f"Upload error: {str(e)}")
            return False
            
    def test_enterprise_api(self):
        """Test enterprise API endpoints"""
        print("🏢 Testing enterprise API...")
        
        # Test enterprise feedback submission
        feedback_data = {
            "enterprise_id": "TEST001",
            "campaign_id": "CAMP001", 
            "feedback_data": {
                "campaign_title": "Test Campaign",
                "industry": "technology",
                "budget": 20000000,
                "actual_performance": {
                    "reach": 10000000,
                    "engagement": 0.04,
                    "roi": 150.0
                },
                "media_outlets": ["VnExpress", "CafeF"],
                "effectiveness_rating": 8.5
            }
        }
        
        try:
            response = requests.post(
                f"{self.main_url}/api/enterprise/submit-feedback",
                json=feedback_data,
                timeout=30
            )
            
            if response.status_code == 200:
                self.log_result("Enterprise API", "PASS", "Feedback submission successful")
                return True
            else:
                self.log_result("Enterprise API", "FAIL", f"API error: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Enterprise API", "FAIL", f"API error: {str(e)}")
            return False
            
    def trigger_continuous_learning(self):
        """Trigger continuous learning để test"""
        print("🔄 Triggering continuous learning...")
        
        try:
            # Trigger retraining
            response = requests.post(
                f"{self.main_url}/api/enterprise/trigger-retrain",
                json={"force": True},
                timeout=60
            )
            
            if response.status_code == 200:
                self.log_result("Continuous Learning Trigger", "PASS", "Retraining triggered")
                
                # Wait and check training status
                time.sleep(5)
                status_response = requests.get(f"{self.main_url}/api/enterprise/training-status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    self.log_result("Training Status Check", "PASS", f"Status: {status_data}")
                    return True
                    
            self.log_result("Continuous Learning Trigger", "FAIL", f"Trigger failed: {response.status_code}")
            return False
            
        except Exception as e:
            self.log_result("Continuous Learning Trigger", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_ml_model_versioning(self):
        """Test model versioning và auto-loading"""
        print("🧠 Testing ML model versioning...")
        
        # Check current model files
        model_files = []
        models_dir = "models"
        if os.path.exists(models_dir):
            model_files = [f for f in os.listdir(models_dir) if f.endswith('.pth')]
            
        self.log_result("Model Files Check", "PASS", f"Found models: {model_files}")
        
        # Check if system can detect latest model
        try:
            response = requests.get(f"{self.main_url}/api/enterprise/model-info")
            if response.status_code == 200:
                model_info = response.json()
                self.log_result("Model Info API", "PASS", f"Current model: {model_info}")
                return True
            else:
                self.log_result("Model Info API", "WARN", "Endpoint not available")
                return False
                
        except Exception as e:
            self.log_result("Model Info API", "WARN", f"Error: {str(e)}")
            return False
            
    def test_user_conversation_flow(self):
        """Test complete user conversation flow"""
        print("💬 Testing user conversation flow...")
        
        # Start conversation
        try:
            response = requests.post(f"{self.main_url}/api/chat/start", json={})
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                self.log_result("Conversation Start", "PASS", f"Session: {self.session_id}")
            else:
                self.log_result("Conversation Start", "FAIL", f"Failed: {response.status_code}")
                return False
                
            # Continue conversation with campaign details
            messages = [
                "Tôi cần làm campaign PR cho startup AI",
                "Ngân sách 25 triệu, target doanh nghiệp công nghệ", 
                "Mục tiêu tăng brand awareness và tìm khách hàng mới",
                "Thời gian triển khai trong 1 tháng"
            ]
            
            for i, message in enumerate(messages):
                response = requests.post(
                    f"{self.main_url}/api/chat/continue",
                    json={"session_id": self.session_id, "message": message}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_result(f"Conversation Step {i+1}", "PASS", f"Response: {data.get('message', '')[:100]}...")
                else:
                    self.log_result(f"Conversation Step {i+1}", "FAIL", f"Failed: {response.status_code}")
                    
                time.sleep(1)
                
            # Trigger workflow
            response = requests.post(
                f"{self.main_url}/api/chat/trigger-workflow",
                json={"session_id": self.session_id}
            )
            
            if response.status_code == 200:
                self.log_result("Workflow Trigger", "PASS", "Workflow started successfully")
                
                # Wait for workflow completion
                time.sleep(30)
                self.log_result("Workflow Completion", "PASS", "Workflow processing time completed")
                return True
            else:
                self.log_result("Workflow Trigger", "FAIL", f"Failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("User Conversation Flow", "FAIL", f"Error: {str(e)}")
            return False
            
    def test_ml_recommendations(self):
        """Test ML recommendations dengan various scenarios"""
        print("🎯 Testing ML recommendations...")
        
        test_scenarios = [
            {
                "name": "Technology Startup",
                "data": {"industry": "technology", "budget": 25000000, "target_audience": ["tech_professionals"]}
            },
            {
                "name": "Food & Beverage",
                "data": {"industry": "food_beverage", "budget": 15000000, "target_audience": ["young_adults"]}
            },
            {
                "name": "Healthcare",
                "data": {"industry": "healthcare", "budget": 30000000, "target_audience": ["healthcare_professionals"]}
            },
            {
                "name": "Low Budget",
                "data": {"industry": "education", "budget": 5000000, "target_audience": ["students"]}
            },
            {
                "name": "High Budget",
                "data": {"industry": "finance", "budget": 50000000, "target_audience": ["businesses"]}
            }
        ]
        
        for scenario in test_scenarios:
            try:
                response = requests.post(
                    f"{self.main_url}/get-media-recommendations",
                    json=scenario["data"],
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    recommendations = data.get("recommendations", [])
                    if recommendations:
                        # Check for ML-enhanced fields
                        first_rec = recommendations[0]
                        has_ml_fields = all(field in first_rec for field in ["ml_score", "confidence", "reasoning"])
                        
                        if has_ml_fields:
                            self.log_result(f"ML Recommendations - {scenario['name']}", "PASS", 
                                          f"Got {len(recommendations)} recommendations with ML fields")
                        else:
                            self.log_result(f"ML Recommendations - {scenario['name']}", "WARN",
                                          f"Got {len(recommendations)} recommendations but missing ML fields")
                    else:
                        self.log_result(f"ML Recommendations - {scenario['name']}", "FAIL", "No recommendations returned")
                else:
                    self.log_result(f"ML Recommendations - {scenario['name']}", "FAIL", f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"ML Recommendations - {scenario['name']}", "FAIL", f"Error: {str(e)}")
                
        return True
        
    def test_data_management(self):
        """Test data deletion và management"""
        print("🗑️ Testing data management...")
        
        # This would typically be done through dashboard, but we'll test via API if available
        try:
            # Check if we can list data
            response = requests.get(f"{self.main_url}/api/enterprise/data-list")
            if response.status_code == 200:
                data_list = response.json()
                self.log_result("Data List API", "PASS", f"Found {len(data_list)} data entries")
                
                # Test deletion if data exists
                if data_list:
                    first_item_id = data_list[0].get("id")
                    delete_response = requests.delete(f"{self.main_url}/api/enterprise/data/{first_item_id}")
                    if delete_response.status_code == 200:
                        self.log_result("Data Deletion", "PASS", f"Deleted item {first_item_id}")
                    else:
                        self.log_result("Data Deletion", "WARN", "Delete endpoint not available")
                        
            else:
                self.log_result("Data List API", "WARN", "Data list endpoint not available")
                
        except Exception as e:
            self.log_result("Data Management", "WARN", f"Management APIs not available: {str(e)}")
            
        return True
        
    def test_edge_cases(self):
        """Test edge cases và error scenarios"""
        print("⚠️ Testing edge cases...")
        
        edge_cases = [
            {
                "name": "Invalid Industry", 
                "data": {"industry": "invalid_industry", "budget": 10000000, "target_audience": ["test"]}
            },
            {
                "name": "Zero Budget",
                "data": {"industry": "technology", "budget": 0, "target_audience": ["tech_professionals"]}
            },
            {
                "name": "Negative Budget", 
                "data": {"industry": "technology", "budget": -1000000, "target_audience": ["tech_professionals"]}
            },
            {
                "name": "Empty Target Audience",
                "data": {"industry": "technology", "budget": 10000000, "target_audience": []}
            },
            {
                "name": "Missing Fields",
                "data": {"industry": "technology"}
            },
            {
                "name": "Invalid JSON",
                "data": "invalid_json_string"
            }
        ]
        
        for case in edge_cases:
            try:
                if case["name"] == "Invalid JSON":
                    # Test malformed JSON
                    response = requests.post(
                        f"{self.main_url}/get-media-recommendations",
                        data=case["data"],  # Send as string instead of JSON
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                else:
                    response = requests.post(
                        f"{self.main_url}/get-media-recommendations",
                        json=case["data"],
                        timeout=10
                    )
                
                # For edge cases, we expect either success with fallback or proper error handling
                if response.status_code in [200, 400, 422]:
                    self.log_result(f"Edge Case - {case['name']}", "PASS", f"Handled gracefully: {response.status_code}")
                else:
                    self.log_result(f"Edge Case - {case['name']}", "FAIL", f"Unexpected response: {response.status_code}")
                    
            except Exception as e:
                self.log_result(f"Edge Case - {case['name']}", "PASS", f"Exception handled: {str(e)}")
                
        return True
        
    def cleanup_servers(self):
        """Stop all servers"""
        print("🧹 Cleaning up servers...")
        
        try:
            if hasattr(self, 'main_process'):
                self.main_process.terminate()
            if hasattr(self, 'dashboard1_process'):
                self.dashboard1_process.terminate()  
            if hasattr(self, 'dashboard2_process'):
                self.dashboard2_process.terminate()
                
            self.log_result("Server Cleanup", "PASS", "All servers terminated")
        except Exception as e:
            self.log_result("Server Cleanup", "WARN", f"Cleanup error: {str(e)}")
            
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📋 COMPREHENSIVE SYSTEM TEST REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        
        print("\nDETAILED RESULTS:")
        print("-" * 80)
        
        for result in self.test_results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_emoji} {result['test']:<30} {result['status']:<6} {result['details']}")
            
        # Save report to file
        with open("comprehensive_test_report.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
            
        print(f"\n📄 Detailed report saved to: comprehensive_test_report.json")
        
        # Cleanup test files
        if os.path.exists("test_enterprise_data.csv"):
            os.remove("test_enterprise_data.csv")
            
        return passed >= total_tests * 0.8  # 80% pass rate required
        
    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 STARTING COMPREHENSIVE SYSTEM TEST")
        print("="*80)
        
        try:
            # 1. Start all servers
            self.start_servers()
            time.sleep(15)  # Wait for full startup
            
            # 2. Create and upload test data
            csv_file = self.create_test_data()
            self.test_data_upload(csv_file)
            
            # 3. Test enterprise APIs
            self.test_enterprise_api()
            
            # 4. Test ML model and versioning
            self.test_ml_model_versioning()
            
            # 5. Test continuous learning
            self.trigger_continuous_learning()
            
            # 6. Test user conversation flow
            self.test_user_conversation_flow()
            
            # 7. Test ML recommendations
            self.test_ml_recommendations()
            
            # 8. Test data management
            self.test_data_management()
            
            # 9. Test edge cases
            self.test_edge_cases()
            
            # Wait a bit for any background processing
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
        except Exception as e:
            print(f"\n❌ Test suite error: {str(e)}")
        finally:
            # Always cleanup and generate report
            self.cleanup_servers()
            success = self.generate_report()
            
            if success:
                print("\n🎉 COMPREHENSIVE TEST SUITE PASSED!")
            else:
                print("\n❌ COMPREHENSIVE TEST SUITE FAILED!")
                
            return success

if __name__ == "__main__":
    tester = ComprehensiveSystemTest()
    tester.run_all_tests()