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

The encryption key is configured in Django settings. The application uses a Fernet key for symmetric encryption:

```python
# In development: derived from SECRET_KEY using SHA256 + base64 encoding
# In production: should be explicitly set via FIELD_ENCRYPTION_KEY env var
FIELD_ENCRYPTION_KEY = os.getenv('FIELD_ENCRYPTION_KEY')
if not FIELD_ENCRYPTION_KEY:
    # Fallback for development only
    key_material = hashlib.sha256(SECRET_KEY.encode()).digest()
    FIELD_ENCRYPTION_KEY = base64.urlsafe_b64encode(key_material).decode()
```

#### Environment Variables

- `FIELD_ENCRYPTION_KEY` (required for production): A securely generated Fernet key for encryption
  - Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `DJANGO_SECRET_KEY` (required): Django's secret key

**CRITICAL - Production Deployment:**

⚠️ **DO NOT rely on the development fallback in production!** The fallback derives a key from `SECRET_KEY` using simple SHA256 hashing, which is less secure than a dedicated encryption key.

**Required steps for production:**
1. Generate a dedicated Fernet key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
2. Set `FIELD_ENCRYPTION_KEY` environment variable to the generated key
3. Ensure `DJANGO_SECRET_KEY` is also set to a strong, unique value
4. Keep both keys secret and never commit them to version control

### Database Schema Change

**IMPORTANT**: The `EncryptedCharField` stores data as `TEXT` in the database (not `VARCHAR`). 

#### For New Installations:
No action needed - Django will create tables with the correct schema.

#### For Existing Installations:
If you have an existing database with the `email_integration_emailaccount` table, you need to manually alter the column type:

**PostgreSQL:**
```sql
ALTER TABLE email_integration_emailaccount 
ALTER COLUMN imap_password TYPE TEXT;
```

**MySQL:**
```sql
ALTER TABLE email_integration_emailaccount 
MODIFY COLUMN imap_password TEXT;
```

**SQLite:**
```sql
-- SQLite doesn't enforce types strictly, so no change needed
-- But for consistency, you can recreate the table with the new type
```

### Migration from Plain Text Passwords

After applying the schema change, existing plain text passwords will be automatically encrypted when:
1. Each account is saved (the field will encrypt on save)
2. Or run a data migration script to re-save all accounts

Existing code that reads `account.imap_password` will continue to work without changes - the encryption/decryption is transparent.

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
