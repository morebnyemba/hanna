# whatsappcrm_backend/analytics/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .views import AdminAnalyticsView
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
import datetime

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super().default(obj)

class AnalyticsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if isinstance(self.user, AnonymousUser) or not self.user.is_staff:
            await self.close()
        else:
            self.group_name = 'admin_analytics'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            await self.send_analytics_data()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')

        if message_type == 'date_range_change':
            start_date = text_data_json.get('start_date')
            end_date = text_data_json.get('end_date')
            await self.send_analytics_data(start_date=start_date, end_date=end_date)

    async def send_analytics_data(self, event=None, start_date=None, end_date=None):
        """
        Fetches analytics data and sends it to the client.
        """
        try:
            analytics_view = AdminAnalyticsView()
            from django.test import RequestFactory
            from rest_framework.request import Request
            factory = RequestFactory()
            
            url = '/crm-api/analytics/admin/'
            if start_date and end_date:
                url += f'?start_date={start_date}&end_date={end_date}'

            wsgi_request = factory.get(url)
            wsgi_request.user = self.user
            drf_request = Request(wsgi_request)
            
            response = await sync_to_async(analytics_view.get)(drf_request)
            data = response.data
            
            await self.send(text_data=json.dumps({
                'type': 'analytics_update',
                'data': data
            }, cls=DateEncoder))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def analytics_update(self, event):
        """
        Handler for the 'analytics_update' event.
        """
        await self.send_analytics_data()
