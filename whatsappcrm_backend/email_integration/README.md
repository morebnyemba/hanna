# Email Integration Module

This module handles email account management and attachment processing for the WhatsApp CRM system.

## Features

- IMAP email account configuration
- Secure password storage with encryption
- Email attachment fetching and processing
- AI-powered invoice extraction from attachments

## Security: Encrypted Password Storage

### Overview

IMAP passwords are stored encrypted in the database using the `django-encrypted-model-fields` library. This ensures that sensitive credentials are protected at rest.

### How It Works

When you save an `EmailAccount` with a password:
1. The password is automatically encrypted using Fernet symmetric encryption before being stored in the database
2. When you retrieve an `EmailAccount`, the password is automatically decrypted
3. The encryption/decryption is transparent - no code changes needed in management commands or views

### Configuration

The encryption key is configured in Django settings:

```python
# Derived from DJANGO_SECRET_KEY by default
FIELD_ENCRYPTION_KEY = os.getenv('FIELD_ENCRYPTION_KEY', SECRET_KEY)
```

#### Environment Variables

- `FIELD_ENCRYPTION_KEY` (optional): Custom Fernet key for encryption. If not provided, a key is derived from `DJANGO_SECRET_KEY`
- `DJANGO_SECRET_KEY` (required): Django's secret key, also used to derive the encryption key if `FIELD_ENCRYPTION_KEY` is not set

**Important**: For production deployments:
1. Ensure `DJANGO_SECRET_KEY` is set to a strong, unique value
2. Optionally, set `FIELD_ENCRYPTION_KEY` to a separate Fernet key for added security
3. Generate a Fernet key using: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### Migration from Plain Text Passwords

If you have existing email accounts with plain text passwords, they will be automatically encrypted when you:
1. Apply the migration: `python manage.py migrate email_integration`
2. Save each account (the field will encrypt on save)

Existing code that reads `account.imap_password` will continue to work without changes.

## Models

### EmailAccount

Stores IMAP email account credentials for fetching emails.

**Fields:**
- `name`: Friendly name for the account
- `imap_host`: IMAP server hostname
- `imap_user`: IMAP username
- `imap_password`: Encrypted IMAP password (using `EncryptedCharField`)
- `port`: IMAP port (default: 993)
- `ssl_protocol`: SSL/TLS protocol version
- `is_active`: Enable/disable email fetching

### EmailAttachment

Stores email attachments fetched from IMAP accounts.

### ParsedInvoice

Stores structured invoice data extracted from attachments.

### AdminEmailRecipient

Stores admin email addresses for critical error notifications.

## Management Commands

### idle_email_fetcher

Runs persistent IMAP IDLE workers to listen for new emails across all active accounts.

```bash
python manage.py idle_email_fetcher
```

### fetch_mailu_attachments

Fetches attachments from all active email accounts once.

```bash
python manage.py fetch_mailu_attachments
```

## Testing

Run the test suite:

```bash
python manage.py test email_integration
```

### Encryption Tests

The test suite includes specific tests for password encryption:
- `test_password_is_encrypted_in_database`: Verifies passwords are encrypted in the database
- `test_password_decryption_on_read`: Verifies passwords are decrypted when read
- `test_password_update_preserves_encryption`: Verifies updates maintain encryption

## Security Best Practices

1. **Never commit encryption keys**: Keep `FIELD_ENCRYPTION_KEY` and `DJANGO_SECRET_KEY` in environment variables or secrets management
2. **Use strong keys**: Generate cryptographically secure keys for production
3. **Rotate keys periodically**: Plan for key rotation (requires re-encrypting data)
4. **Backup encrypted data**: Ensure backups include the encryption key securely stored separately
5. **Access control**: Limit who can access the encryption keys and database

## Dependencies

- `django-encrypted-model-fields`: Provides transparent field-level encryption
- `cryptography`: Underlying encryption library (Fernet)
- `imapclient`: IMAP client for email fetching
