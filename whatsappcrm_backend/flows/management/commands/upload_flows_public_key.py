# whatsappcrm_backend/flows/management/commands/upload_flows_public_key.py

"""
Management command to upload the flows signing public key to Meta.
Required before publishing WhatsApp Flows.
"""

import os
from django.core.management.base import BaseCommand, CommandError
from meta_integration.models import MetaAppConfig
from flows.whatsapp_flow_service import WhatsAppFlowService


class Command(BaseCommand):
    help = 'Upload flows signing public key to Meta. Required before publishing flows.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--key-path',
            type=str,
            default='flow_signing_public.pem',
            help='Path to the public key file (default: flow_signing_public.pem in current directory)'
        )

    def handle(self, *args, **options):
        key_path = options['key_path']

        # Get active Meta app config
        try:
            meta_config = MetaAppConfig.objects.get_active_config()
        except MetaAppConfig.DoesNotExist:
            raise CommandError('No active Meta App Configuration found. Please configure one in the admin.')
        except MetaAppConfig.MultipleObjectsReturned:
            raise CommandError('Multiple active Meta App Configurations found. Please ensure only one is active.')

        self.stdout.write(self.style.SUCCESS(f'Using Meta config: {meta_config.name}'))
        self.stdout.write(f'Phone Number ID: {meta_config.phone_number_id}')

        # Check if key file exists
        if not os.path.exists(key_path):
            raise CommandError(
                f'Public key file not found: {key_path}\n\n'
                f'Generate it with:\n'
                f'  openssl genpkey -algorithm RSA -out flow_signing_private.pem -pkeyopt rsa_keygen_bits:2048\n'
                f'  openssl rsa -in flow_signing_private.pem -pubout -out flow_signing_public.pem\n\n'
                f'Then run this command again with the correct path.'
            )

        self.stdout.write(f'Using public key file: {key_path}')

        # Initialize service and upload
        service = WhatsAppFlowService(meta_config)
        
        self.stdout.write('\nUploading flows public key...')
        success = service.upload_flows_public_key(key_path)

        if success:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✓ Public key uploaded successfully!\n\n'
                    'Next steps:\n'
                    '1. In WhatsApp Business Manager, whitelist your domain:\n'
                    '   Flows → Settings → Data exchange domain allowlist\n'
                    '   Add: backend.hanna.co.zw\n\n'
                    '2. Then publish your flows:\n'
                    '   python manage.py sync_whatsapp_flows --flow payment --publish\n'
                )
            )
        else:
            raise CommandError(
                'Failed to upload public key. Check logs for details.\n\n'
                'Common issues:\n'
                '- Phone number ID not set in MetaAppConfig\n'
                '- Invalid access token\n'
                '- Network connectivity issue'
            )
