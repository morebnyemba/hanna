# whatsappcrm_backend/analytics/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .views import AdminAnalyticsView
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser

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
        # This is a simplified example. In a real app, you'd pass a mock request
        # to the view or refactor the view's logic into a separate function.
        try:
            analytics_view = AdminAnalyticsView()
            # We need to create a mock request object for the view
            from django.test import RequestFactory
            factory = RequestFactory()
            
            url = '/crm-api/analytics/admin/'
            if start_date and end_date:
                url += f'?start_date={start_date}&end_date={end_date}'

            request = factory.get(url)
            request.user = self.user
            
            # The view's get method is synchronous, so we run it in a thread
            data = await sync_to_async(analytics_view.get)(request).data
            
            await self.send(text_data=json.dumps({
                'type': 'analytics_update',
                'data': data
            }))
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
