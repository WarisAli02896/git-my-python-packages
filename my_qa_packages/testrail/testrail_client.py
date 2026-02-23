import requests
from typing import List, Optional, Dict
from requests.auth import HTTPBasicAuth


class TestRailClient:
    """
    Client for interacting with TestRail API.
    Supports creating test runs, executing test cases, and updating test status.
    """
    
    # TestRail status IDs
    STATUS_PASSED = 1
    STATUS_BLOCKED = 2
    STATUS_UNTESTED = 3
    STATUS_RETEST = 4
    STATUS_FAILED = 5
    
    def __init__(
        self,
        base_url: str = None,
        username: str = None,
        api_key: str = None,
        config: dict = None
    ):
        """
        Initialize TestRail client.
        
        Args:
            base_url: TestRail base URL (e.g., 'https://yourcompany.testrail.io')
            username: TestRail username/email
            api_key: TestRail API key
            config: Dictionary containing configuration parameters
        """
        # If connection configuration provided in config parameter then set all values in individual variables
        if config:
            base_url = config.get("base_url")
            username = config.get("username")
            api_key = config.get("api_key")
        
        # Validation for checking all required values provided
        if not all([base_url, username, api_key]):
            raise ValueError("Missing required TestRail configuration parameters: base_url, username, and api_key are required")
        
        # Ensure base_url doesn't end with /
        self.base_url = base_url.rstrip('/')
        # Strip whitespace from username and API key (common issue)
        self.username = username.strip() if username else username
        self.api_key = api_key.strip() if api_key else api_key
        
        # Setup authentication
        # TestRail uses HTTP Basic Auth with email as username and API key as password
        self.auth = HTTPBasicAuth(self.username, self.api_key)
        self.headers = {
            'Content-Type': 'application/json'
        }
        
        # Test connection (optional - can be disabled if needed)
        self._test_connection()
    
    def _test_connection(self):
        """Test the connection to TestRail API."""
        try:
            # Use get_projects endpoint which is universally available and tests auth
            endpoint = '/index.php?/api/v2/get_projects'
            response = self._make_request('GET', endpoint)
            if response:
                print(f"Connected to TestRail successfully")
                return True
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg:
                print(f"\nAuthentication failed!")
                print(f"Please verify:")
                print(f"  1. Your API key is correct (get it from TestRail > My Settings > API)")
                print(f"  2. Your username/email is correct: {self.username}")
                print(f"  3. Your base URL is correct: {self.base_url}")
                print(f"\nNote: API keys are case-sensitive and should not have extra spaces")
                print(f"\nTo get your API key:")
                print(f"  1. Log in to TestRail: {self.base_url}")
                print(f"  2. Click your profile icon (top right)")
                print(f"  3. Go to 'My Settings' or 'User Settings'")
                print(f"  4. Click on 'API' or 'API Keys' tab")
                print(f"  5. Copy your API key (or generate a new one if needed)")
            raise
    
    def _make_request(self, method: str, endpoint: str, data: dict = None) -> Optional[Dict]:
        """
        Make HTTP request to TestRail API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload (for POST/PUT requests)
        
        Returns:
            Response JSON as dictionary or None
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, auth=self.auth, headers=self.headers)
            elif method.upper() == 'POST':
                response = requests.post(url, auth=self.auth, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, auth=self.auth, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else None
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {e.response.status_code}"
            if e.response.content:
                try:
                    error_detail = e.response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {e.response.text}"
            print(f"TestRail API request failed: {error_msg}")
            raise
        except requests.exceptions.RequestException as e:
            print(f"TestRail API request error: {e}")
            raise
    
    def get_project_by_name(self, project_name: str) -> Optional[Dict]:
        """
        Get project information by project name.
        
        Args:
            project_name: Name of the project
        
        Returns:
            Project dictionary or None if not found
        """
        try:
            response = self._make_request('GET', '/index.php?/api/v2/get_projects')
            if response:
                # Handle paginated response (TestRail API v2 returns paginated data)
                if isinstance(response, dict) and 'projects' in response:
                    projects = response.get('projects', [])
                elif isinstance(response, list):
                    projects = response
                else:
                    projects = []
                
                # Search for project by name
                for project in projects:
                    if isinstance(project, dict) and project.get('name') == project_name:
                        print(f"Found project '{project_name}' with ID: {project.get('id')}")
                        return project
                
                print(f"Project '{project_name}' not found")
                return None
        except Exception as e:
            print(f"Error getting project by name: {e}")
            raise
    
    def create_test_run(
        self,
        project_name: str,
        test_case_ids: List[int],
        suite_id: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        milestone_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Create a test run in TestRail.
        
        Args:
            project_name: Name of the project
            test_case_ids: List of test case IDs to include in the run
            suite_id: Suite ID (optional)
            name: Test run name (optional, defaults to timestamp-based name)
            description: Test run description (optional)
            milestone_id: Milestone ID (optional)
            assigned_to_id: User ID to assign the run to (optional)
        
        Returns:
            Created test run dictionary or None
        """
        project = self.get_project_by_name(project_name)
        if not project:
            raise ValueError(f"Project '{project_name}' not found")
        
        project_id = project.get('id')
        
        run_data = {
            'case_ids': test_case_ids
        }
        
        if suite_id:
            run_data['suite_id'] = suite_id
        
        if name:
            run_data['name'] = name
        else:
            from datetime import datetime
            run_data['name'] = f"Test Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if description:
            run_data['description'] = description
        
        if milestone_id:
            run_data['milestone_id'] = milestone_id
        
        if assigned_to_id:
            run_data['assignedto_id'] = assigned_to_id
        
        try:
            endpoint = f'/index.php?/api/v2/add_run/{project_id}'
            test_run = self._make_request('POST', endpoint, run_data)
            
            if test_run:
                print(f"Test run created successfully with ID: {test_run.get('id')}")
                print(f"Test run name: {test_run.get('name')}")
                print(f"Test cases included: {len(test_case_ids)}")
            
            return test_run
            
        except Exception as e:
            print(f"Error creating test run: {e}")
            raise
    
    def update_test_case_status(
        self,
        run_id: int,
        case_id: int,
        status: int,
        comment: Optional[str] = None,
        elapsed: Optional[str] = None,
        defects: Optional[str] = None,
        version: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Update the status of a test case result in a test run.
        
        Args:
            run_id: Test run ID
            case_id: Test case ID
            status: Status ID (1=Passed, 2=Blocked, 3=Untested, 4=Retest, 5=Failed)
            comment: Optional comment for the test result
            elapsed: Optional time elapsed (e.g., "30s", "1m 30s")
            defects: Optional defect IDs (comma-separated)
            version: Optional version string
        
        Returns:
            Updated test result dictionary or None
        """
        try:
            result_data = {
                'status_id': status
            }
            
            if comment:
                result_data['comment'] = comment
            
            if elapsed:
                result_data['elapsed'] = elapsed
            
            if defects:
                result_data['defects'] = defects
            
            if version:
                result_data['version'] = version
            
            add_result_endpoint = f'/index.php?/api/v2/add_result_for_case/{run_id}/{case_id}'
            result = self._make_request('POST', add_result_endpoint, result_data)
            
            if result:
                status_names = {
                    1: "Passed",
                    2: "Blocked",
                    3: "Untested",
                    4: "Retest",
                    5: "Failed"
                }
                status_name = status_names.get(status, "Unknown")
                print(f"Test case {case_id} status updated to '{status_name}' in run {run_id}")
            
            return result
            
        except Exception as e:
            print(f"Error updating test case status: {e}")
            raise
    
    def update_test_case_status_batch(
        self,
        run_id: int,
        results: List[Dict]
    ) -> Optional[List[Dict]]:
        """
        Update multiple test case results in a test run (batch update).
        
        Args:
            run_id: Test run ID
            results: List of dictionaries, each containing:
                - case_id: Test case ID
                - status: Status ID
                - comment: Optional comment
                - elapsed: Optional time elapsed
                - defects: Optional defect IDs
                - version: Optional version
        
        Returns:
            List of updated test result dictionaries
        """
        try:
            endpoint = f'/index.php?/api/v2/add_results_for_cases/{run_id}'
            updated_results = self._make_request('POST', endpoint, {'results': results})
            
            if updated_results:
                print(f"Updated {len(results)} test case results in run {run_id}")
            
            return updated_results
            
        except Exception as e:
            print(f"Error updating test case statuses in batch: {e}")
            raise
    
    def get_sections(self, project_id: int, suite_id: int = None) -> List[Dict]:
        """Get all sections in a project/suite."""
        try:
            endpoint = f'/index.php?/api/v2/get_sections/{project_id}'
            if suite_id:
                endpoint += f'&suite_id={suite_id}'
            response = self._make_request('GET', endpoint)
            if isinstance(response, dict) and 'sections' in response:
                return response.get('sections', [])
            elif isinstance(response, list):
                return response
            return []
        except Exception as e:
            print(f"Error getting sections: {e}")
            raise

    def add_section(self, project_id: int, name: str, suite_id: int = None, parent_id: int = None) -> Optional[Dict]:
        """Create a new section in a project."""
        try:
            data = {'name': name}
            if suite_id:
                data['suite_id'] = suite_id
            if parent_id:
                data['parent_id'] = parent_id
            endpoint = f'/index.php?/api/v2/add_section/{project_id}'
            section = self._make_request('POST', endpoint, data)
            if section:
                print(f"Section '{name}' created with ID: {section.get('id')}")
            return section
        except Exception as e:
            print(f"Error creating section: {e}")
            raise

    def get_cases(self, project_id: int, suite_id: int = None) -> List[Dict]:
        """Get all test cases in a project/suite."""
        try:
            endpoint = f'/index.php?/api/v2/get_cases/{project_id}'
            if suite_id:
                endpoint += f'&suite_id={suite_id}'
            response = self._make_request('GET', endpoint)
            if isinstance(response, dict) and 'cases' in response:
                return response.get('cases', [])
            elif isinstance(response, list):
                return response
            return []
        except Exception as e:
            print(f"Error getting cases: {e}")
            raise

    def add_case(self, section_id: int, title: str, **kwargs) -> Optional[Dict]:
        """
        Create a new test case in a section.

        Args:
            section_id: Section ID to add the case to
            title: Test case title
            **kwargs: Additional fields (e.g., type_id, priority_id, refs)
        """
        try:
            data = {'title': title, **kwargs}
            endpoint = f'/index.php?/api/v2/add_case/{section_id}'
            case = self._make_request('POST', endpoint, data)
            if case:
                print(f"Case '{title}' created with ID: C{case.get('id')}")
            return case
        except Exception as e:
            print(f"Error creating case: {e}")
            raise

    def get_test_run(self, run_id: int) -> Optional[Dict]:
        """
        Get test run information.
        
        Args:
            run_id: Test run ID
        
        Returns:
            Test run dictionary or None
        """
        try:
            endpoint = f'/index.php?/api/v2/get_run/{run_id}'
            test_run = self._make_request('GET', endpoint)
            return test_run
        except Exception as e:
            print(f"Error getting test run: {e}")
            raise
    
    def get_tests_in_run(self, run_id: int) -> Optional[List[Dict]]:
        """
        Get all tests in a test run.
        
        Args:
            run_id: Test run ID
        
        Returns:
            List of test dictionaries
        """
        try:
            endpoint = f'/index.php?/api/v2/get_tests/{run_id}'
            tests = self._make_request('GET', endpoint)
            return tests
        except Exception as e:
            print(f"Error getting tests in run: {e}")
            raise
