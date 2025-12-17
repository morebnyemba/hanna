# Email Attachment Processing Guide

## Overview

This document describes the automated email attachment processing system, including scheduled reprocessing of unprocessed PDF attachments and Django admin management capabilities.

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

### 2. Django Admin Actions

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

To change from 2 days to a different period, modify the task in `email_integration/tasks.py`:

```python
# Change from 2 days to 7 days
two_days_ago = timezone.now() - timezone.timedelta(days=7)  # Changed from days=2
```

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
