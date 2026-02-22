# whatsappcrm_backend/admin_api/tests.py
"""
Tests for Admin API endpoints
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from customer_data.models import InstallationRequest, CustomerProfile
from conversations.models import Contact
from warranty.models import Technician
from admin_api.models import FailedTask, TaskProgress


class AdminInstallationRequestAPITestCase(TestCase):
    """Test cases for Admin Installation Request API"""

    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create non-admin user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='userpass123'
        )
        
        # Create technician user
        self.tech_user = User.objects.create_user(
            username='technician',
            email='tech@test.com',
            password='techpass123'
        )
        
        # Create a contact for customer profile
        self.contact = Contact.objects.create(
            whatsapp_id='1234567890',
            name='Test Contact',
            phone_number='+1234567890'
        )
        
        # Create customer profile
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='John',
            last_name='Doe',
            email='john@test.com'
        )
        
        # Create technician
        self.technician = Technician.objects.create(
            user=self.tech_user,
            specialization='Solar Installation',
            contact_phone='+1234567890'
        )
        
        # Create installation request with dynamic date
        future_date = (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%d %H:%M')
        self.installation = InstallationRequest.objects.create(
            customer=self.customer,
            status='pending',
            installation_type='solar',
            full_name='John Doe',
            address='123 Test Street',
            contact_phone='+1234567890',
            preferred_datetime=future_date,
        )
        
        # Set up API client
        self.client = APIClient()

    def test_list_installations_as_admin(self):
        """Test listing installations as admin user"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/crm-api/admin-panel/installation-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_installations_as_non_admin(self):
        """Test listing installations as non-admin user (should fail)"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/crm-api/admin-panel/installation-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_installation_as_admin(self):
        """Test retrieving a specific installation as admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.installation.id)
        self.assertEqual(response.data['full_name'], 'John Doe')
        self.assertEqual(response.data['status'], 'pending')

    def test_create_installation_as_admin(self):
        """Test creating a new installation request as admin"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Use dynamic date for test
        future_date = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d %H:%M')
        
        data = {
            'customer': self.customer.pk,
            'status': 'pending',
            'installation_type': 'starlink',
            'full_name': 'Jane Smith',
            'address': '456 Another Street',
            'contact_phone': '+9876543210',
            'preferred_datetime': future_date,
        }
        
        response = self.client.post(
            '/crm-api/admin-panel/installation-requests/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['full_name'], 'Jane Smith')
        self.assertEqual(response.data['installation_type'], 'starlink')

    def test_update_installation_as_admin(self):
        """Test updating an installation request as admin"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Use dynamic date for test
        future_date = (timezone.now() + timedelta(days=8)).strftime('%Y-%m-%d %H:%M')
        
        data = {
            'customer': self.customer.pk,
            'status': 'scheduled',
            'installation_type': 'solar',
            'full_name': 'John Doe Updated',
            'address': '123 Test Street',
            'contact_phone': '+1234567890',
            'preferred_datetime': future_date,
        }
        
        response = self.client.put(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'John Doe Updated')
        self.assertEqual(response.data['status'], 'scheduled')

    def test_delete_installation_as_admin(self):
        """Test deleting an installation request as admin"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify it's deleted
        self.assertFalse(
            InstallationRequest.objects.filter(id=self.installation.id).exists()
        )

    def test_mark_completed_action(self):
        """Test marking installation as completed via custom action"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/mark_completed/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['data']['status'], 'completed')
        
        # Verify in database
        self.installation.refresh_from_db()
        self.assertEqual(self.installation.status, 'completed')

    def test_assign_technicians_action(self):
        """Test assigning technicians to installation via custom action"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'technician_ids': [self.technician.id]
        }
        
        response = self.client.post(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/assign_technicians/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify technician was assigned
        self.installation.refresh_from_db()
        self.assertEqual(self.installation.technicians.count(), 1)
        self.assertEqual(self.installation.technicians.first().id, self.technician.id)

    def test_filter_by_status(self):
        """Test filtering installations by status"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create another installation with different status and dynamic date
        future_date = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M')
        InstallationRequest.objects.create(
            customer=self.customer,
            status='completed',
            installation_type='solar',
            full_name='Jane Doe',
            address='789 Another Street',
            contact_phone='+1111111111',
            preferred_datetime=future_date,
        )
        
        response = self.client.get(
            '/crm-api/admin-panel/installation-requests/?status=pending'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'pending')

    def test_search_installations(self):
        """Test searching installations"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(
            '/crm-api/admin-panel/installation-requests/?search=John'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get('/crm-api/admin-panel/installation-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class FailedTaskModelTestCase(TestCase):
    """Test cases for the FailedTask model (dead letter queue)"""

    def test_create_failed_task(self):
        """Test creating a failed task record"""
        task = FailedTask.objects.create(
            task_id='test-task-id-123',
            task_name='meta_integration.tasks.send_whatsapp_message_task',
            args=[1, 2],
            kwargs={'key': 'value'},
            exception_type='ValueError',
            exception_message='Test error message',
            traceback='Traceback...',
            retries=3,
        )
        self.assertEqual(task.status, 'failed')
        self.assertEqual(task.task_id, 'test-task-id-123')
        self.assertEqual(task.retries, 3)
        self.assertIsNotNone(task.created_at)
        self.assertIsNone(task.resolved_at)

    def test_failed_task_unique_id(self):
        """Test that task_id is unique"""
        FailedTask.objects.create(
            task_id='unique-id-1',
            task_name='test.task',
            exception_type='Error',
            exception_message='msg',
        )
        with self.assertRaises(Exception):
            FailedTask.objects.create(
                task_id='unique-id-1',
                task_name='test.task',
                exception_type='Error',
                exception_message='msg',
            )


class TaskProgressModelTestCase(TestCase):
    """Test cases for the TaskProgress model"""

    def test_create_task_progress(self):
        """Test creating a task progress record"""
        progress = TaskProgress.objects.create(
            task_id='progress-task-123',
            task_name='test.long_running_task',
            status='started',
            progress_percent=0,
            message='Task started',
        )
        self.assertEqual(progress.status, 'started')
        self.assertEqual(progress.progress_percent, 0)

    def test_update_task_progress(self):
        """Test updating task progress"""
        progress = TaskProgress.objects.create(
            task_id='progress-task-456',
            task_name='test.task',
            status='progress',
            progress_percent=50,
            message='Halfway done',
        )
        progress.progress_percent = 100
        progress.status = 'completed'
        progress.result = {'processed': 100}
        progress.save()

        progress.refresh_from_db()
        self.assertEqual(progress.progress_percent, 100)
        self.assertEqual(progress.status, 'completed')
        self.assertEqual(progress.result, {'processed': 100})


class FailedTaskAPITestCase(TestCase):
    """Test cases for the FailedTask API endpoints"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin_task',
            email='admin_task@test.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='user_task',
            email='user_task@test.com',
            password='userpass123'
        )
        self.client = APIClient()

        self.failed_task = FailedTask.objects.create(
            task_id='api-test-task-001',
            task_name='meta_integration.tasks.send_whatsapp_message_task',
            args=[42, 7],
            kwargs={},
            exception_type='ConnectionError',
            exception_message='Connection refused',
            retries=5,
        )

    def test_list_failed_tasks_as_admin(self):
        """Test listing failed tasks as admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/crm-api/admin-panel/failed-tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_failed_tasks_non_admin(self):
        """Test non-admin cannot access failed tasks"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/crm-api/admin-panel/failed-tasks/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_resolve_failed_task(self):
        """Test resolving a failed task"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            f'/crm-api/admin-panel/failed-tasks/{self.failed_task.id}/resolve/'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.failed_task.refresh_from_db()
        self.assertEqual(self.failed_task.status, 'resolved')
        self.assertIsNotNone(self.failed_task.resolved_at)

    def test_unauthenticated_access(self):
        """Test unauthenticated access is rejected"""
        response = self.client.get('/crm-api/admin-panel/failed-tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskProgressAPITestCase(TestCase):
    """Test cases for the TaskProgress API endpoints"""

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin_progress',
            email='admin_progress@test.com',
            password='adminpass123'
        )
        self.client = APIClient()

        self.task_progress = TaskProgress.objects.create(
            task_id='progress-api-001',
            task_name='test.long_task',
            status='progress',
            progress_percent=50,
            message='Processing...',
        )

    def test_list_task_progress_as_admin(self):
        """Test listing task progress as admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/crm-api/admin-panel/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_task_progress_is_read_only(self):
        """Test that task progress endpoint is read-only"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            '/crm-api/admin-panel/tasks/',
            {'task_id': 'new-task', 'task_name': 'test'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class BaseTaskWithRetryTestCase(TestCase):
    """Test cases for the BaseTaskWithRetry class"""

    def test_base_task_class_attributes(self):
        """Test that BaseTaskWithRetry has correct attributes"""
        from whatsappcrm_backend.celery import BaseTaskWithRetry
        self.assertEqual(BaseTaskWithRetry.max_retries, 5)
        self.assertEqual(BaseTaskWithRetry.retry_backoff, 60)
        self.assertEqual(BaseTaskWithRetry.retry_backoff_max, 3600)
        self.assertTrue(BaseTaskWithRetry.retry_jitter)

    def test_base_task_autoretry(self):
        """Test that BaseTaskWithRetry auto-retries on Exception"""
        from whatsappcrm_backend.celery import BaseTaskWithRetry
        self.assertIn(Exception, BaseTaskWithRetry.autoretry_for)


class QueryPerformanceMiddlewareTestCase(TestCase):
    """Test cases for the QueryPerformanceMiddleware"""

    def test_middleware_initializes(self):
        """Test that middleware initializes correctly"""
        from whatsappcrm_backend.middleware import QueryPerformanceMiddleware
        middleware = QueryPerformanceMiddleware(get_response=lambda r: r)
        self.assertIsNotNone(middleware)
        self.assertIsInstance(middleware.slow_query_threshold_ms, float)

    def test_middleware_processes_request(self):
        """Test that middleware processes a request without error"""
        from whatsappcrm_backend.middleware import QueryPerformanceMiddleware
        factory = RequestFactory()
        request = factory.get('/test/')

        def mock_response(request):
            from django.http import HttpResponse
            return HttpResponse('OK')

        middleware = QueryPerformanceMiddleware(get_response=mock_response)
        response = middleware(request)
        self.assertEqual(response.status_code, 200)
