# Generated manually for integrations app initial models

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ZohoCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.CharField(help_text='Zoho OAuth Client ID', max_length=255, verbose_name='Client ID')),
                ('client_secret', models.CharField(help_text='Zoho OAuth Client Secret', max_length=255, verbose_name='Client Secret')),
                ('access_token', models.TextField(blank=True, help_text='Current OAuth access token', null=True, verbose_name='Access Token')),
                ('refresh_token', models.TextField(blank=True, help_text='OAuth refresh token for obtaining new access tokens', null=True, verbose_name='Refresh Token')),
                ('expires_in', models.DateTimeField(blank=True, help_text='When the current access token expires', null=True, verbose_name='Token Expiration')),
                ('scope', models.CharField(blank=True, default='ZohoInventory.items.READ', help_text='OAuth scope permissions', max_length=500, verbose_name='Scope')),
                ('organization_id', models.CharField(blank=True, help_text='Zoho organization/company ID', max_length=255, null=True, verbose_name='Organization ID')),
                ('api_domain', models.CharField(default='https://inventory.zoho.com', help_text='Zoho API domain (e.g., https://inventory.zoho.com, https://inventory.zoho.eu)', max_length=255, verbose_name='API Domain')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Zoho Credential',
                'verbose_name_plural': 'Zoho Credentials',
            },
        ),
    ]
