# Generated manually for OAuth state storage

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OAuthState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(db_index=True, help_text='OAuth state token for CSRF protection', max_length=255, unique=True, verbose_name='State Token')),
                ('user_id', models.IntegerField(blank=True, help_text='ID of the user who initiated the OAuth flow', null=True, verbose_name='User ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('used', models.BooleanField(default=False, help_text='Whether this state token has been used', verbose_name='Used')),
            ],
            options={
                'verbose_name': 'OAuth State',
                'verbose_name_plural': 'OAuth States',
                'indexes': [
                    models.Index(fields=['state', 'used'], name='integration_state_u_idx'),
                    models.Index(fields=['created_at'], name='integration_created_idx'),
                ],
            },
        ),
    ]
