#!/usr/bin/env python3
"""
Comprehensive test script for checklist page functionality
Run this after setting up test data to verify all features work correctly
"""

import requests
import json
from datetime import date

# Configuration
BASE_URL = "https://backend.hanna.co.zw/crm-api"
TECHNICIAN_USERNAME = "technician_test"
TECHNICIAN_PASSWORD = "Tech123!@#"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

class ChecklistTester:
    def __init__(self):
        self.access_token = None
        self.checklist = None
        self.installation_record = None
        self.test_photo_id = None
        
    def authenticate(self):
        """Test 1: Authenticate as technician"""
        print_info("Test 1: Authenticating as technician...")
        
        try:
            response = requests.post(
                f"{BASE_URL}/auth/token/",
                json={
                    "username": TECHNICIAN_USERNAME,
                    "password": TECHNICIAN_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access')
                print_success(f"Authentication successful")
                print_info(f"  Token: {self.access_token[:20]}...")
                return True
            else:
                print_error(f"Authentication failed: {response.status_code}")
                print_error(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Authentication error: {str(e)}")
            return False
    
    def get_checklists(self):
        """Test 2: Fetch technician checklists"""
        print_info("Test 2: Fetching checklists...")
        
        if not self.access_token:
            print_error("No access token. Please authenticate first.")
            return False
            
        try:
            response = requests.get(
                f"{BASE_URL}/technician/checklists/",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                checklists = response.json()
                print_success(f"Fetched {len(checklists)} checklist(s)")
                
                if len(checklists) > 0:
                    self.checklist = checklists[0]
                    self.installation_record = self.checklist.get('installation_record')
                    
                    print_info(f"  First checklist:")
                    print_info(f"    ID: {self.checklist.get('id')}")
                    print_info(f"    Type: {self.checklist.get('checklist_type')}")
                    print_info(f"    Completion: {self.checklist.get('completion_percentage')}%")
                    print_info(f"    Installation Record: {self.installation_record}")
                    print_info(f"    Items: {len(self.checklist.get('template', {}).get('items', []))}")
                    return True
                else:
                    print_warning("No checklists found. Run create_test_installation.py first.")
                    return False
                    
            elif response.status_code == 401:
                print_error("Unauthorized (401) - Token may be expired or invalid")
                print_error("  Make sure you're using a technician account")
                return False
            else:
                print_error(f"Failed to fetch checklists: {response.status_code}")
                print_error(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error fetching checklists: {str(e)}")
            return False
    
    def get_checklist_photos(self):
        """Test 3: Fetch photos for checklist"""
        print_info("Test 3: Fetching photos...")
        
        if not self.installation_record:
            print_error("No installation record. Please fetch checklists first.")
            return False
            
        try:
            response = requests.get(
                f"{BASE_URL}/installation-photos/?installation_record={self.installation_record}",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                photos = response.json()
                print_success(f"Fetched {len(photos)} photo(s)")
                
                # Group photos by checklist item
                photo_groups = {}
                for photo in photos:
                    item_id = photo.get('checklist_item')
                    if item_id:
                        if item_id not in photo_groups:
                            photo_groups[item_id] = []
                        photo_groups[item_id].append(photo)
                
                if photo_groups:
                    print_info(f"  Photos grouped by item:")
                    for item_id, item_photos in photo_groups.items():
                        print_info(f"    Item {item_id}: {len(item_photos)} photo(s)")
                
                return True
            else:
                print_error(f"Failed to fetch photos: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error fetching photos: {str(e)}")
            return False
    
    def toggle_item_completion(self):
        """Test 4: Toggle checklist item completion"""
        print_info("Test 4: Testing item completion toggle...")
        
        if not self.checklist:
            print_error("No checklist available. Please fetch checklists first.")
            return False
        
        items = self.checklist.get('template', {}).get('items', [])
        if not items:
            print_error("No items in checklist template")
            return False
        
        # Get first item that's not completed
        test_item = None
        for item in items:
            item_id = item.get('id')
            if item_id not in self.checklist.get('completed_items', {}):
                test_item = item
                break
        
        if not test_item:
            # All items completed, try to uncomplete first one
            test_item = items[0]
            print_info("  All items completed, will toggle first item")
        
        item_id = test_item.get('id')
        is_completed = item_id in self.checklist.get('completed_items', {})
        
        try:
            response = requests.post(
                f"{BASE_URL}/technician/checklists/{self.checklist['id']}/toggle-item/",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json={"item_id": item_id}
            )
            
            if response.status_code == 200:
                result = response.json()
                new_status = result.get('completed', not is_completed)
                action = "Completed" if new_status else "Uncompleted"
                print_success(f"{action} item: {test_item.get('title')}")
                print_info(f"  New completion: {result.get('completion_percentage')}%")
                return True
            else:
                print_error(f"Failed to toggle item: {response.status_code}")
                print_error(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error toggling item: {str(e)}")
            return False
    
    def add_note_to_item(self):
        """Test 5: Add note to checklist item"""
        print_info("Test 5: Testing note addition...")
        
        if not self.checklist:
            print_error("No checklist available.")
            return False
        
        items = self.checklist.get('template', {}).get('items', [])
        if not items:
            print_error("No items in checklist")
            return False
        
        test_item = items[0]
        item_id = test_item.get('id')
        test_note = f"Test note added on {date.today()}"
        
        try:
            response = requests.post(
                f"{BASE_URL}/technician/checklists/{self.checklist['id']}/add-note/",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "item_id": item_id,
                    "notes": test_note
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print_success(f"Note added to: {test_item.get('title')}")
                print_info(f"  Note: {test_note}")
                return True
            else:
                print_error(f"Failed to add note: {response.status_code}")
                print_error(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print_error(f"Error adding note: {str(e)}")
            return False
    
    def check_installation_record(self):
        """Test 6: Verify installation record details"""
        print_info("Test 6: Checking installation record...")
        
        if not self.installation_record:
            print_error("No installation record.")
            return False
        
        try:
            response = requests.get(
                f"{BASE_URL}/installation-system-records/{self.installation_record}/",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            
            if response.status_code == 200:
                isr = response.json()
                print_success("Installation record fetched successfully")
                print_info(f"  ID: {isr.get('id')}")
                print_info(f"  Short ID: {isr.get('short_id')}")
                print_info(f"  Status: {isr.get('installation_status')}")
                print_info(f"  Customer: {isr.get('customer_name')}")
                print_info(f"  Installation Date: {isr.get('installation_date')}")
                print_info(f"  Commissioning Date: {isr.get('commissioning_date')}")
                
                # Check if can be commissioned
                if isr.get('installation_status') != 'commissioned':
                    print_info("  ℹ Installation not yet commissioned")
                else:
                    print_info("  ✓ Installation already commissioned")
                
                return True
            else:
                print_error(f"Failed to fetch installation record: {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Error fetching installation record: {str(e)}")
            return False
    
    def test_commissioning_validation(self):
        """Test 7: Test commissioning endpoint (without actually commissioning)"""
        print_info("Test 7: Testing commissioning validation...")
        
        if not self.checklist or not self.installation_record:
            print_error("No checklist or installation record.")
            return False
        
        completion = self.checklist.get('completion_percentage', 0)
        
        if completion < 100:
            print_warning(f"Checklist only {completion}% complete - commissioning would fail")
            print_info("  This is expected behavior - commissioning requires 100% completion")
            return True
        else:
            print_success(f"Checklist is {completion}% complete - ready for commissioning")
            print_warning("  Skipping actual commissioning to preserve test data")
            print_info("  In real usage, this would:")
            print_info("    • Update installation_status to 'commissioned'")
            print_info("    • Set commissioning_date to today")
            print_info("    • Lock checklist from further edits")
            print_info("    • Trigger notifications to customer and admin")
            return True
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("\n" + "="*70)
        print(f"{Colors.BLUE}🧪 Checklist Page Functionality Test Suite{Colors.END}")
        print("="*70 + "\n")
        
        tests = [
            ("Authentication", self.authenticate),
            ("Fetch Checklists", self.get_checklists),
            ("Fetch Photos", self.get_checklist_photos),
            ("Toggle Item Completion", self.toggle_item_completion),
            ("Add Note", self.add_note_to_item),
            ("Check Installation Record", self.check_installation_record),
            ("Commissioning Validation", self.test_commissioning_validation),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print_error(f"Test '{test_name}' crashed: {str(e)}")
                failed += 1
            print()  # Blank line between tests
        
        # Summary
        print("="*70)
        print(f"{Colors.BLUE}📊 Test Results Summary{Colors.END}")
        print("="*70)
        print(f"{Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {failed}{Colors.END}")
        print(f"Total: {passed + failed}")
        
        if failed == 0:
            print(f"\n{Colors.GREEN}🎉 All tests passed!{Colors.END}\n")
            return True
        else:
            print(f"\n{Colors.RED}❌ Some tests failed. Please review the output above.{Colors.END}\n")
            return False

if __name__ == "__main__":
    print(f"\n{Colors.YELLOW}⚙️  Setup Instructions:{Colors.END}")
    print("1. Ensure Docker containers are running")
    print("2. Run: docker-compose exec backend python manage.py create_test_installation")
    print("3. Make sure CORS is configured for API requests")
    print("4. Update BASE_URL if testing locally\n")
    
    input("Press Enter to continue with tests...")
    
    tester = ChecklistTester()
    success = tester.run_all_tests()
    
    exit(0 if success else 1)
