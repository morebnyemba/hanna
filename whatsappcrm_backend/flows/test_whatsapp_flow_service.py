"""
Unit tests for WhatsAppFlowService update_flow_json fix.
Tests that the file parameter is correctly sent as multipart/form-data.
"""
import json
import time
from unittest.mock import Mock, patch, call
from django.test import TestCase
from flows.whatsapp_flow_service import WhatsAppFlowService
from flows.models import WhatsAppFlow
from meta_integration.models import MetaAppConfig


class WhatsAppFlowServiceUpdateFlowJsonTest(TestCase):
    """Test the update_flow_json method uses multipart/form-data correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.meta_config = Mock(spec=MetaAppConfig)
        self.meta_config.access_token = "test_access_token"
        self.meta_config.api_version = "v23.0"
        self.meta_config.waba_id = "1234567890"
        
        self.service = WhatsAppFlowService(self.meta_config)
        
        # Create a mock WhatsAppFlow
        self.whatsapp_flow = Mock(spec=WhatsAppFlow)
        self.whatsapp_flow.flow_id = "test_flow_id_123"
        self.whatsapp_flow.name = "test_flow"
        self.whatsapp_flow.friendly_name = "Test Flow"
        self.whatsapp_flow.flow_json = {
            "version": "3.0",
            "screens": [
                {
                    "id": "WELCOME",
                    "title": "Welcome"
                }
            ]
        }
        self.whatsapp_flow.sync_status = 'draft'
        self.whatsapp_flow.save = Mock()
    
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_sends_file_parameter(self, mock_post):
        """Test that update_flow_json sends file as multipart/form-data"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        # Call the method
        result = self.service.update_flow_json(self.whatsapp_flow)
        
        # Verify the result
        self.assertTrue(result)
        
        # Verify requests.post was called
        self.assertTrue(mock_post.called)
        
        # Get the call arguments
        call_args = mock_post.call_args
        
        # Verify the URL
        expected_url = f"https://graph.facebook.com/v23.0/{self.whatsapp_flow.flow_id}/assets"
        self.assertEqual(call_args[0][0], expected_url)
        
        # Verify headers (should NOT include Content-Type for multipart)
        headers = call_args[1]['headers']
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['Authorization'], 'Bearer test_access_token')
        self.assertNotIn('Content-Type', headers)
        
        # Verify data parameter (form fields)
        data = call_args[1]['data']
        self.assertIn('name', data)
        self.assertEqual(data['name'], 'flow.json')  # Asset filename, not flow name
        self.assertIn('asset_type', data)
        self.assertEqual(data['asset_type'], 'FLOW_JSON')
        
        # Verify files parameter (the file upload)
        files = call_args[1]['files']
        self.assertIn('file', files)
        
        # Verify the file tuple structure: (filename, content, content_type)
        file_tuple = files['file']
        self.assertEqual(len(file_tuple), 3)
        self.assertEqual(file_tuple[0], 'flow.json')  # filename
        self.assertEqual(file_tuple[2], 'application/json')  # content type
        
        # Verify the file content is valid JSON
        file_content = file_tuple[1]
        parsed_json = json.loads(file_content)
        self.assertEqual(parsed_json['version'], '3.0')
        self.assertIn('screens', parsed_json)
    
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_without_flow_id(self, mock_post):
        """Test that update_flow_json fails gracefully without flow_id"""
        self.whatsapp_flow.flow_id = None
        
        result = self.service.update_flow_json(self.whatsapp_flow)
        
        # Should return False
        self.assertFalse(result)
        
        # Should not call requests.post
        self.assertFalse(mock_post.called)
    
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_handles_api_error(self, mock_post):
        """Test that update_flow_json handles API errors properly"""
        # Setup mock response with error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'error': {
                'message': 'Bad request',
                'type': 'OAuthException',
                'code': 100
            }
        }
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value = mock_response
        
        result = self.service.update_flow_json(self.whatsapp_flow)
        
        # Should return False on error
        self.assertFalse(result)
        
        # Verify sync_status was set to 'error'
        # Last save call should have set sync_status to 'error'
        self.assertEqual(self.whatsapp_flow.sync_status, 'error')


class WhatsAppFlowServiceListFlowsTest(TestCase):
    """Test the list_flows and find_flow_by_name methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.meta_config = Mock(spec=MetaAppConfig)
        self.meta_config.access_token = "test_access_token"
        self.meta_config.api_version = "v23.0"
        self.meta_config.waba_id = "1234567890"
        
        self.service = WhatsAppFlowService(self.meta_config)
    
    @patch('flows.whatsapp_flow_service.requests.get')
    def test_list_flows_success(self, mock_get):
        """Test that list_flows retrieves flows from Meta"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'flow_1', 'name': 'Test Flow 1_v1.02'},
                {'id': 'flow_2', 'name': 'Test Flow 2_v1.02'}
            ]
        }
        mock_get.return_value = mock_response
        
        flows = self.service.list_flows()
        
        self.assertEqual(len(flows), 2)
        self.assertEqual(flows[0]['id'], 'flow_1')
        self.assertEqual(flows[1]['name'], 'Test Flow 2_v1.02')
    
    @patch('flows.whatsapp_flow_service.requests.get')
    def test_list_flows_handles_pagination(self, mock_get):
        """Test that list_flows handles paginated results"""
        # First page
        response1 = Mock()
        response1.status_code = 200
        response1.json.return_value = {
            'data': [{'id': 'flow_1', 'name': 'Flow 1'}],
            'paging': {'next': 'https://graph.facebook.com/next_page'}
        }
        
        # Second page
        response2 = Mock()
        response2.status_code = 200
        response2.json.return_value = {
            'data': [{'id': 'flow_2', 'name': 'Flow 2'}]
        }
        
        mock_get.side_effect = [response1, response2]
        
        flows = self.service.list_flows()
        
        self.assertEqual(len(flows), 2)
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('flows.whatsapp_flow_service.requests.get')
    def test_list_flows_handles_error(self, mock_get):
        """Test that list_flows returns empty list on error"""
        mock_get.side_effect = Exception("Network error")
        
        flows = self.service.list_flows()
        
        self.assertEqual(flows, [])
    
    @patch('flows.whatsapp_flow_service.requests.get')
    def test_find_flow_by_name_found(self, mock_get):
        """Test that find_flow_by_name finds existing flow"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'flow_123', 'name': 'Solar Installation Request (Interactive)_v1.02'},
                {'id': 'flow_456', 'name': 'Another Flow_v1.02'}
            ]
        }
        mock_get.return_value = mock_response
        
        flow_id = self.service.find_flow_by_name('Solar Installation Request (Interactive)_v1.02')
        
        self.assertEqual(flow_id, 'flow_123')
    
    @patch('flows.whatsapp_flow_service.requests.get')
    def test_find_flow_by_name_not_found(self, mock_get):
        """Test that find_flow_by_name returns None when flow not found"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'flow_456', 'name': 'Another Flow_v1.02'}
            ]
        }
        mock_get.return_value = mock_response
        
        flow_id = self.service.find_flow_by_name('Nonexistent Flow_v1.02')
        
        self.assertIsNone(flow_id)


class WhatsAppFlowServiceSyncFlowTest(TestCase):
    """Test the sync_flow method with flow_id recovery"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.meta_config = Mock(spec=MetaAppConfig)
        self.meta_config.access_token = "test_access_token"
        self.meta_config.api_version = "v23.0"
        self.meta_config.waba_id = "1234567890"
        
        self.service = WhatsAppFlowService(self.meta_config)
        
        # Create a mock WhatsAppFlow without flow_id
        self.whatsapp_flow = Mock(spec=WhatsAppFlow)
        self.whatsapp_flow.flow_id = None
        self.whatsapp_flow.name = "test_flow"
        self.whatsapp_flow.friendly_name = "Test Flow"
        self.whatsapp_flow.flow_json = {"version": "3.0", "screens": []}
        self.whatsapp_flow.sync_status = 'draft'
        self.whatsapp_flow.save = Mock()
    
    @patch('flows.whatsapp_flow_service.WhatsAppFlowService.find_flow_by_name')
    @patch('flows.whatsapp_flow_service.WhatsAppFlowService.update_flow_json')
    def test_sync_flow_recovers_existing_flow_id(self, mock_update, mock_find):
        """Test that sync_flow recovers flow_id from Meta if flow exists"""
        # Flow exists on Meta
        mock_find.return_value = 'existing_flow_id_123'
        mock_update.return_value = True
        
        with patch.object(self.service, 'find_flow_by_name', mock_find):
            with patch.object(self.service, 'update_flow_json', mock_update):
                result = self.service.sync_flow(self.whatsapp_flow)
        
        # Should find the flow
        mock_find.assert_called_once()
        
        # Should set the flow_id
        self.assertEqual(self.whatsapp_flow.flow_id, 'existing_flow_id_123')
        
        # Should call update instead of create
        mock_update.assert_called_once_with(self.whatsapp_flow)
        
        # Should succeed
        self.assertTrue(result)
    
    @patch('flows.whatsapp_flow_service.WhatsAppFlowService.find_flow_by_name')
    @patch('flows.whatsapp_flow_service.WhatsAppFlowService.create_flow')
    def test_sync_flow_creates_new_flow_if_not_found(self, mock_create, mock_find):
        """Test that sync_flow creates new flow if not found on Meta"""
        # Flow doesn't exist on Meta
        mock_find.return_value = None
        mock_create.return_value = True
        
        with patch.object(self.service, 'find_flow_by_name', mock_find):
            with patch.object(self.service, 'create_flow', mock_create):
                result = self.service.sync_flow(self.whatsapp_flow)
        
        # Should look for the flow
        mock_find.assert_called_once()
        
        # Should call create since flow not found
        mock_create.assert_called_once_with(self.whatsapp_flow)
        
        # Should succeed
        self.assertTrue(result)
    
    @patch('flows.whatsapp_flow_service.WhatsAppFlowService.update_flow_json')
    def test_sync_flow_updates_if_flow_id_exists(self, mock_update):
        """Test that sync_flow updates directly if flow_id already exists"""
        # Flow already has flow_id
        self.whatsapp_flow.flow_id = 'known_flow_id'
        mock_update.return_value = True
        
        with patch.object(self.service, 'update_flow_json', mock_update):
            result = self.service.sync_flow(self.whatsapp_flow)
        
        # Should call update directly
        mock_update.assert_called_once_with(self.whatsapp_flow)
        
        # Should succeed
        self.assertTrue(result)


class WhatsAppFlowServiceRetryLogicTest(TestCase):
    """Test the retry logic for update_flow_json with Meta processing errors"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.meta_config = Mock(spec=MetaAppConfig)
        self.meta_config.access_token = "test_access_token"
        self.meta_config.api_version = "v23.0"
        self.meta_config.waba_id = "1234567890"
        
        self.service = WhatsAppFlowService(self.meta_config)
        
        # Create a mock WhatsAppFlow
        self.whatsapp_flow = Mock(spec=WhatsAppFlow)
        self.whatsapp_flow.flow_id = "test_flow_id_123"
        self.whatsapp_flow.name = "test_flow"
        self.whatsapp_flow.friendly_name = "Test Flow"
        self.whatsapp_flow.flow_json = {
            "version": "3.0",
            "screens": [{"id": "WELCOME", "title": "Welcome"}]
        }
        self.whatsapp_flow.sync_status = 'draft'
        self.whatsapp_flow.save = Mock()
    
    @patch('flows.whatsapp_flow_service.time.sleep')
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_retries_on_meta_processing_error(self, mock_post, mock_sleep):
        """Test that update_flow_json retries on Meta processing error 139001/4016012"""
        from requests.exceptions import HTTPError
        
        # First two attempts fail with Meta processing error
        error_response = Mock()
        error_response.status_code = 400
        error_response.json.return_value = {
            'error': {
                'message': 'Updating attempt failed',
                'type': 'OAuthException',
                'code': 139001,
                'error_subcode': 4016012,
                'is_transient': False,
                'error_user_title': 'Error while processing WELJ',
                'error_user_msg': 'Flow JSON has been saved, but processing has failed. Please try uploading flow JSON again.',
                'fbtrace_id': 'test_trace_id'
            }
        }
        error_response.raise_for_status.side_effect = HTTPError(response=error_response)
        
        # Third attempt succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'success': True}
        
        mock_post.side_effect = [error_response, error_response, success_response]
        
        result = self.service.update_flow_json(self.whatsapp_flow, max_retries=3)
        
        # Should succeed after retries
        self.assertTrue(result)
        
        # Should have made 3 attempts
        self.assertEqual(mock_post.call_count, 3)
        
        # Should have slept twice (between attempts 1-2 and 2-3)
        self.assertEqual(mock_sleep.call_count, 2)
        
        # Verify exponential backoff: 5s, 10s
        mock_sleep.assert_has_calls([call(5), call(10)])
        
        # Final status should be 'draft'
        self.assertEqual(self.whatsapp_flow.sync_status, 'draft')
    
    @patch('flows.whatsapp_flow_service.time.sleep')
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_fails_after_max_retries(self, mock_post, mock_sleep):
        """Test that update_flow_json fails after exhausting retries"""
        from requests.exceptions import HTTPError
        
        # All attempts fail with Meta processing error
        error_response = Mock()
        error_response.status_code = 400
        error_response.json.return_value = {
            'error': {
                'message': 'Updating attempt failed',
                'type': 'OAuthException',
                'code': 139001,
                'error_subcode': 4016012,
                'error_user_msg': 'Flow JSON has been saved, but processing has failed.'
            }
        }
        error_response.raise_for_status.side_effect = HTTPError(response=error_response)
        
        mock_post.return_value = error_response
        
        result = self.service.update_flow_json(self.whatsapp_flow, max_retries=3)
        
        # Should fail after all retries
        self.assertFalse(result)
        
        # Should have made 3 attempts
        self.assertEqual(mock_post.call_count, 3)
        
        # Should have slept twice
        self.assertEqual(mock_sleep.call_count, 2)
        
        # Final status should be 'error'
        self.assertEqual(self.whatsapp_flow.sync_status, 'error')
    
    @patch('flows.whatsapp_flow_service.time.sleep')
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_does_not_retry_non_retryable_errors(self, mock_post, mock_sleep):
        """Test that update_flow_json does not retry on non-retryable errors"""
        from requests.exceptions import HTTPError
        
        # Different error (not the Meta processing error)
        error_response = Mock()
        error_response.status_code = 401
        error_response.json.return_value = {
            'error': {
                'message': 'Invalid access token',
                'type': 'OAuthException',
                'code': 190
            }
        }
        error_response.raise_for_status.side_effect = HTTPError(response=error_response)
        
        mock_post.return_value = error_response
        
        result = self.service.update_flow_json(self.whatsapp_flow, max_retries=3)
        
        # Should fail immediately
        self.assertFalse(result)
        
        # Should have made only 1 attempt (no retries)
        self.assertEqual(mock_post.call_count, 1)
        
        # Should not have slept
        self.assertEqual(mock_sleep.call_count, 0)
        
        # Final status should be 'error'
        self.assertEqual(self.whatsapp_flow.sync_status, 'error')
    
    @patch('flows.whatsapp_flow_service.requests.post')
    def test_update_flow_json_succeeds_on_first_attempt(self, mock_post):
        """Test that update_flow_json succeeds on first attempt when no error"""
        # First attempt succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'success': True}
        
        mock_post.return_value = success_response
        
        result = self.service.update_flow_json(self.whatsapp_flow, max_retries=3)
        
        # Should succeed
        self.assertTrue(result)
        
        # Should have made only 1 attempt
        self.assertEqual(mock_post.call_count, 1)
        
        # Final status should be 'draft'
        self.assertEqual(self.whatsapp_flow.sync_status, 'draft')
