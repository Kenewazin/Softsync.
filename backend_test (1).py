#!/usr/bin/env python3
"""
SoftSync Backend API Testing Suite
Tests all endpoints for the monthly organization web app
"""

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class SoftSyncAPITester:
    def __init__(self, base_url="https://timekeep-33.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        self.test_email = f"test_{datetime.now().strftime('%H%M%S')}@example.com"
        self.test_password = "TestPass123!"
        self.test_name = "Test User"

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, use_auth: bool = False) -> tuple[bool, Any]:
        """Make HTTP request and validate response"""
        url = f"{self.base_url}/api/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if use_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"
            
            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            if not success:
                return False, f"Expected {expected_status}, got {response.status_code}. Response: {response_data}"
            
            return True, response_data
            
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.ConnectionError:
            return False, "Connection error"
        except Exception as e:
            return False, f"Request error: {str(e)}"

    def test_health_check(self):
        """Test API health endpoint"""
        success, response = self.make_request('GET', '/health')
        self.log_test("Health Check", success, 
                     "" if success else str(response), response)
        return success

    def test_user_registration(self):
        """Test user registration"""
        data = {
            "email": self.test_email,
            "password": self.test_password,
            "name": self.test_name
        }
        
        success, response = self.make_request('POST', '/auth/register', data)
        
        if success and isinstance(response, dict):
            self.token = response.get('token')
            self.user_id = response.get('user_id')
            success = bool(self.token and self.user_id)
            
        self.log_test("User Registration", success, 
                     "" if success else str(response), response)
        return success

    def test_user_login(self):
        """Test user login"""
        data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        success, response = self.make_request('POST', '/auth/login', data)
        
        if success and isinstance(response, dict):
            token = response.get('token')
            if token:
                self.token = token  # Update token from login
                
        self.log_test("User Login", success, 
                     "" if success else str(response), response)
        return success

    def test_get_user_profile(self):
        """Test getting user profile"""
        success, response = self.make_request('GET', '/auth/me', use_auth=True)
        
        if success and isinstance(response, dict):
            success = response.get('email') == self.test_email
            
        self.log_test("Get User Profile", success, 
                     "" if success else str(response), response)
        return success

    def test_update_profile(self):
        """Test updating user profile"""
        data = {
            "country": "MX",
            "timezone": "America/Mexico_City",
            "gender": "female"
        }
        
        success, response = self.make_request('PUT', '/auth/profile', data, use_auth=True)
        
        if success and isinstance(response, dict):
            success = (response.get('country') == 'MX' and 
                      response.get('gender') == 'female' and
                      response.get('onboarding_complete') == True)
            
        self.log_test("Update Profile", success, 
                     "" if success else str(response), response)
        return success

    def test_create_event(self):
        """Test creating an event"""
        data = {
            "title": "Test Event",
            "description": "Test event description",
            "date": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "time": "15:30",
            "notify": True,
            "notify_minutes_before": 5
        }
        
        success, response = self.make_request('POST', '/events', data, 200, use_auth=True)
        
        if success and isinstance(response, dict):
            self.test_event_id = response.get('event_id')
            success = bool(self.test_event_id and response.get('title') == 'Test Event')
            
        self.log_test("Create Event", success, 
                     "" if success else str(response), response)
        return success

    def test_get_events(self):
        """Test getting user events"""
        success, response = self.make_request('GET', '/events', use_auth=True)
        
        if success and isinstance(response, list):
            success = len(response) > 0
            
        self.log_test("Get Events", success, 
                     "" if success else str(response), response)
        return success

    def test_natural_language_parsing(self):
        """Test AI natural language parsing"""
        data = {
            "text": "Reunión de trabajo mañana a las 2 de la tarde",
            "user_timezone": "America/Mexico_City",
            "user_country": "MX"
        }
        
        success, response = self.make_request('POST', '/events/parse', data, use_auth=True)
        
        if success and isinstance(response, dict):
            success = bool(response.get('title') and response.get('date') and response.get('time'))
            
        self.log_test("Natural Language Parsing", success, 
                     "" if success else str(response), response)
        return success

    def test_delete_event(self):
        """Test deleting an event"""
        if not hasattr(self, 'test_event_id'):
            self.log_test("Delete Event", False, "No event ID available")
            return False
            
        success, response = self.make_request('DELETE', f'/events/{self.test_event_id}', use_auth=True)
        
        self.log_test("Delete Event", success, 
                     "" if success else str(response), response)
        return success

    def test_cycle_tracking_create(self):
        """Test cycle tracking (for female users)"""
        data = {
            "start_date": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            "cycle_length": 28,
            "period_length": 5,
            "notes": "Test cycle data"
        }
        
        success, response = self.make_request('POST', '/cycle', data, 200, use_auth=True)
        
        if success and isinstance(response, dict):
            self.test_cycle_id = response.get('cycle_id')
            success = bool(self.test_cycle_id)
            
        self.log_test("Create Cycle Data", success, 
                     "" if success else str(response), response)
        return success

    def test_get_cycles(self):
        """Test getting cycle history"""
        success, response = self.make_request('GET', '/cycle', use_auth=True)
        
        if success and isinstance(response, list):
            success = len(response) > 0
            
        self.log_test("Get Cycle History", success, 
                     "" if success else str(response), response)
        return success

    def test_cycle_prediction(self):
        """Test cycle prediction"""
        success, response = self.make_request('GET', '/cycle/prediction', use_auth=True)
        
        if success and isinstance(response, dict):
            success = bool(response.get('avg_cycle_length') or response.get('message'))
            
        self.log_test("Cycle Prediction", success, 
                     "" if success else str(response), response)
        return success

    def test_notifications(self):
        """Test upcoming notifications"""
        success, response = self.make_request('GET', '/notifications/upcoming', use_auth=True)
        
        if success and isinstance(response, list):
            success = True  # Empty list is valid
            
        self.log_test("Get Notifications", success, 
                     "" if success else str(response), response)
        return success

    def test_logout(self):
        """Test user logout"""
        success, response = self.make_request('POST', '/auth/logout', use_auth=True)
        
        self.log_test("User Logout", success, 
                     "" if success else str(response), response)
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting SoftSync API Tests...")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic health check
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
        
        # Authentication flow
        if not self.test_user_registration():
            print("❌ Registration failed - stopping tests")
            return False
            
        if not self.test_user_login():
            print("❌ Login failed - stopping tests")
            return False
            
        if not self.test_get_user_profile():
            print("❌ Get profile failed - stopping tests")
            return False
        
        # Profile setup (onboarding)
        if not self.test_update_profile():
            print("❌ Profile update failed - stopping tests")
            return False
        
        # Event management
        self.test_create_event()
        self.test_get_events()
        self.test_natural_language_parsing()
        self.test_delete_event()
        
        # Cycle tracking (female users only)
        self.test_cycle_tracking_create()
        self.test_get_cycles()
        self.test_cycle_prediction()
        
        # Notifications
        self.test_notifications()
        
        # Cleanup
        self.test_logout()
        
        return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = SoftSyncAPITester()
    
    try:
        success = tester.run_all_tests()
        tester.print_summary()
        
        # Save detailed results
        with open('/app/test_reports/backend_test_results.json', 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': tester.tests_passed/tester.tests_run if tester.tests_run > 0 else 0,
                'results': tester.test_results
            }, f, indent=2)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())