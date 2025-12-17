# Email Attachment Processing Guide

## Overview

This document describes the automated email attachment processing system, including:
1. Scheduled reprocessing of unprocessed PDF attachments (Celery Beat task)
2. Real-time mailbox monitoring for missing attachments (Idle Email Fetcher)
3. Django admin management capabilities

## Features

### 1. Automated PDF Reprocessing (Scheduled Task)

The system includes a Celery Beat scheduled task that automatically checks for and reprocesses unprocessed PDF attachments from the last 2 days.

**Task Name:** `email_integration.reprocess_unprocessed_pdf_attachments`

**Schedule:** Every 4 hours (configurable in settings.py)

**Behavior:**
- Searches for PDF attachments with:
  - `processed = False`
  - `email_date >= (now - 2 days)`
  - `filename` ending with `.pdf` (case-insensitive)
- Queues each matching attachment for Gemini AI processing
- Logs all actions for monitoring and debugging
- Returns a summary message with the count of queued attachments

**Configuration:**

The schedule can be modified in `whatsappcrm_backend/whatsappcrm_backend/settings.py`:

```python
CELERY_BEAT_SCHEDULE = {
    'reprocess-unprocessed-pdf-attachments': {
        'task': 'email_integration.reprocess_unprocessed_pdf_attachments',
        # Runs every 4 hours - adjust as needed
        'schedule': crontab(minute=0, hour='*/4'),
    },
}
```

### 2. Idle Email Fetcher - Missing Attachments Detection

The idle email fetcher now includes automatic detection and retrieval of missing attachments from recent emails in the mailbox.

**Service:** `idle_email_fetcher` management command

**Behavior:**
- Monitors mailbox in real-time for new emails (IDLE protocol)
- **NEW:** Periodically checks emails from the last 2 days in the mailbox
- Compares attachments in those emails with what exists in the database
- If attachments don't exist in our system, automatically fetches and saves them
- Queues missing attachments for processing
- Runs every ~2 hours (4 IDLE cycles of 29 minutes each)
- Performs initial check on connection/reconnection

**How It Works:**
1. When the service starts or reconnects, it immediately scans the last 2 days of emails
2. For each email, it checks if attachments exist in the database (by filename, sender, and date)
3. If attachments are missing, they are downloaded and saved
4. Missing attachments are automatically queued for Gemini AI processing
5. This process repeats approximately every 2 hours during idle times

**Key Features:**
- Prevents missed attachments due to service downtime
- Catches attachments that failed to save during initial processing
- Uses the same configurable time window as the reprocessing task (`EMAIL_ATTACHMENT_REPROCESS_DAYS`)
- Duplicate detection prevents saving the same attachment multiple times

**Logs to Monitor:**
```
[AccountName] Checking for missing attachments from emails since DD-Mon-YYYY...
[AccountName] Found N emails from last X days. Checking for missing attachments...
[AccountName] Found missing attachment: filename.pdf (DB id: 123)
[AccountName] Retrieved N missing attachment(s) from recent emails.
[AccountName] All attachments from recent emails are already in the system.
```

### 3. Django Admin Actions

The Email Attachment admin interface (`/admin/email_integration/emailattachment/`) includes several actions for managing attachment processing:

#### Available Actions:

##### 1. Retrigger Gemini Processing
- **Description:** Reprocess selected attachments regardless of their current state
- **Use Case:** When you need to reprocess any attachment (processed or unprocessed)
- **Behavior:** 
  - Marks attachments as unprocessed
  - Queues them for Gemini AI processing
  - Works with any file type

##### 2. Reprocess Unprocessed PDF Attachments (Last 2 Days)
- **Description:** Specifically targets unprocessed PDF attachments
- **Use Case:** Manual trigger to process PDFs that haven't been processed yet
- **Behavior:**
  - Filters selection to only include unprocessed PDFs
  - Marks them as unprocessed (if not already)
  - Queues them for processing
  - Shows a message indicating how many PDFs were queued

##### 3. Mark as Unprocessed
- **Description:** Mark selected attachments as unprocessed
- **Use Case:** Reset processing status to allow automated systems to pick them up
- **Behavior:**
  - Sets `processed = False` for selected attachments
  - Does not immediately queue for processing
  - Useful when you want the scheduled task to handle it

##### 4. Mark as Processed
- **Description:** Mark selected attachments as processed
- **Use Case:** Skip processing for certain attachments or mark false positives
- **Behavior:**
  - Sets `processed = True` for selected attachments
  - Prevents automated reprocessing

### 3. Enhanced Admin Interface

#### New Features:

##### File Type Column
- Displays the file extension (PDF, DOC, XLSX, etc.)
- Makes it easy to filter and identify PDFs visually
- Shown as uppercase for better readability

##### Enhanced Filters
- Filter by processing status (processed/unprocessed)
- Filter by email date
- Filter by sender
- Filter by email account

##### Improved Performance
- Uses `select_related('account')` for optimized database queries
- Reduces the number of database hits when displaying the list

## Usage Examples

### Scenario 1: Manual Reprocessing of Failed PDFs

1. Navigate to Django Admin → Email Integration → Email Attachments
2. Filter by:
   - Processed: No
   - Email date: Last 7 days
3. Optionally filter by file type by searching for ".pdf" in the filename
4. Select the attachments you want to reprocess
5. Choose "Reprocess unprocessed PDF attachments (last 2 days)" from the Actions dropdown
6. Click "Go"

### Scenario 2: Monitoring Scheduled Task

The scheduled task logs its activity. Check your logs for entries like:

```
[Reprocess PDFs Task] Starting scheduled task to reprocess unprocessed PDF attachments from last 2 days.
[Reprocess PDFs Task] Found 5 unprocessed PDF attachment(s) from the last 2 days.
[Reprocess PDFs Task] Queued PDF attachment 123 ('invoice.pdf') for processing.
[Reprocess PDFs Task] Successfully queued 5 out of 5 PDF attachments for reprocessing.
```

### Scenario 3: Forcing Reprocessing of a Previously Processed Attachment

1. Navigate to Django Admin → Email Integration → Email Attachments
2. Find the attachment (you can search by filename or sender)
3. Select the attachment
4. Choose "Retrigger Gemini processing" from the Actions dropdown
5. Click "Go"

The attachment will be reset to unprocessed and queued for processing immediately.

### Scenario 4: Monitoring Idle Fetcher for Missing Attachments

The idle email fetcher automatically checks for and retrieves missing attachments. Monitor its activity in the logs:

```
[Sales Inbox] Checking for missing attachments from emails since 15-Dec-2024...
[Sales Inbox] Found 45 emails from last 2 days. Checking for missing attachments...
[Sales Inbox] Found missing attachment: invoice_123.pdf (DB id: 456)
[Sales Inbox] Found missing attachment: receipt.pdf (DB id: 457)
[Sales Inbox] Retrieved 2 missing attachment(s) from recent emails.
```

If all attachments are already in the system:
```
[Sales Inbox] All attachments from recent emails are already in the system.
```

**What This Means:**
- The service is actively checking the mailbox for emails from the last 2 days
- Any attachments that weren't previously saved are now being retrieved
- This catches attachments missed due to service downtime or errors
- All newly found attachments are automatically queued for processing

## How The Complete System Works Together

The email attachment processing system uses three complementary approaches:

### 1. Real-Time Processing (Idle Fetcher - IDLE Mode)
- **When:** As new emails arrive
- **What:** Immediately saves and processes attachments from new emails
- **Purpose:** Primary method for handling incoming attachments

### 2. Missing Attachments Detection (Idle Fetcher - Periodic Check)
- **When:** Every ~2 hours during idle times + on connection
- **What:** Scans mailbox for emails from last 2 days and retrieves missing attachments
- **Purpose:** Catches attachments missed due to downtime, errors, or connection issues
- **How:** Compares mailbox contents with database to find gaps

### 3. Unprocessed PDF Reprocessing (Celery Beat Task)
- **When:** Every 4 hours
- **What:** Finds unprocessed PDF attachments in the database and retries processing
- **Purpose:** Ensures PDFs that failed processing are retried automatically

**Together, these three mechanisms ensure:**
- ✅ No attachments are missed during service downtime
- ✅ Failed processing attempts are automatically retried
- ✅ The system self-heals and catches up after interruptions
- ✅ All PDF attachments eventually get processed

## Monitoring and Troubleshooting

### Checking Task Status

1. **Celery Beat Schedule:**
   - Ensure Celery Beat is running: `celery -A whatsappcrm_backend beat -l info`
   - Check that the task is in the schedule: Look for `reprocess-unprocessed-pdf-attachments` in the beat output

2. **Celery Workers:**
   - Ensure workers are running: `celery -A whatsappcrm_backend worker -l info`
   - Check worker logs for task execution

3. **Django Admin:**
   - Check the Email Attachments list for processing status
   - Review the "Extracted Data" field for any error messages

### Common Issues

#### PDFs Not Being Reprocessed

**Possible Causes:**
- Email date is older than 2 days
- Attachment is already marked as processed
- Celery Beat or workers are not running
- Task schedule is not configured correctly

**Solutions:**
- Verify the email date is within the last 2 days
- Use "Mark as unprocessed" admin action to reset status
- Restart Celery Beat and workers
- Check `settings.py` for correct task configuration

#### Processing Failures

**Possible Causes:**
- Gemini API issues (rate limits, API key, etc.)
- Invalid PDF format
- Network connectivity issues

**Solutions:**
- Check Celery worker logs for detailed error messages
- Review the `extracted_data` field in admin for error details
- Verify Gemini API configuration in AI Integration settings
- Use "Retrigger Gemini processing" to retry

## Technical Details

### Database Schema

The `EmailAttachment` model includes:
- `processed` (Boolean): Processing status
- `filename` (CharField): Original filename
- `email_date` (DateTimeField): Date from email header
- `extracted_data` (JSONField): Results from Gemini processing
- `account` (ForeignKey): Link to EmailAccount

### Task Dependencies

The scheduled task depends on:
- `EmailAttachment` model
- `process_attachment_with_gemini` task
- Django timezone utilities
- Celery Beat scheduler

### Performance Considerations

- The scheduled task uses efficient database queries with filtering
- Only PDFs from the last 2 days are considered to limit scope
- Tasks are queued asynchronously to avoid blocking
- Database indexes on `processed` and `email_date` improve query performance

## Configuration Options

### Adjusting the Time Window

The time window for checking unprocessed PDFs is configurable via environment variable or Django settings.

**Method 1: Environment Variable (Recommended for production)**

Add to your `.env` file:
```bash
# Number of days to look back for unprocessed PDFs (default: 2)
EMAIL_ATTACHMENT_REPROCESS_DAYS=7
```

**Method 2: Direct Settings Modification**

In `whatsappcrm_backend/whatsappcrm_backend/settings.py`:
```python
# Email Attachment Processing Settings
EMAIL_ATTACHMENT_REPROCESS_DAYS = 7  # Changed from default of 2 days
```

**Note:** Changes to environment variables require a restart of Celery workers and beat scheduler.

### Adjusting the Schedule

To change the frequency, modify `settings.py`:

```python
# Run every 2 hours instead of 4
'schedule': crontab(minute=0, hour='*/2'),

# Run daily at 2 AM
'schedule': crontab(minute=0, hour=2),

# Run every 30 minutes
'schedule': crontab(minute='*/30'),
```

## Testing

Comprehensive tests are available in `email_integration/tests.py`:

- `ReprocessUnprocessedPDFsTaskTests`: Tests for the scheduled task
- `AdminActionsTests`: Tests for admin actions

Run tests with:
```bash
python manage.py test email_integration.tests.ReprocessUnprocessedPDFsTaskTests
python manage.py test email_integration.tests.AdminActionsTests
```

## Support and Maintenance

### Logs

Monitor the following log entries:
- `[Reprocess PDFs Task]` - Scheduled task logs
- `[Gemini File API Task ID: ...]` - Individual processing logs
- Admin actions are logged with admin username

### Metrics

Track:
- Number of unprocessed PDFs over time
- Processing success/failure rates
- Average processing time per PDF
- Task execution frequency and duration

## See Also

- [Email Integration Documentation](./whatsappcrm_backend/email_integration/README.md) (if exists)
- [Celery Configuration](./whatsappcrm_backend/whatsappcrm_backend/celery.py)
- [AI Integration Setup](./whatsappcrm_backend/ai_integration/)
