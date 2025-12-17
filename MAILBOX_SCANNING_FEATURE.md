# Mailbox Scanning Feature - Missing Attachments Detection

## Overview

This document describes the mailbox scanning feature added to the idle email fetcher service, which ensures no email attachments are missed by actively checking the mailbox for attachments that don't exist in the database.

## Problem Statement

**Original Issue**: Email attachments could be missed due to:
- Service downtime or restarts
- Initial processing failures
- Network interruptions during email receipt
- IMAP connection issues

**Solution Needed**: A mechanism to retroactively check the mailbox and retrieve any attachments that aren't in the database.

## Solution: Mailbox Scanning in Idle Fetcher

### What It Does

The idle email fetcher now includes periodic mailbox scanning that:

1. **Checks Recent Emails**: Scans emails from the last N days in the mailbox (default: 2 days)
2. **Compares with Database**: For each email attachment, checks if it exists in the database
3. **Retrieves Missing Attachments**: Downloads and saves any attachments not found in the system
4. **Processes Automatically**: Queues missing attachments for Gemini AI processing

### When It Runs

- **On Connection**: Immediately when the service connects or reconnects to the mailbox
- **Periodically**: Every ~2 hours during idle times (4 IDLE cycles × 29 minutes each)

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Idle Email Fetcher Service                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ├──► Real-Time IDLE Processing
                                │    (New emails as they arrive)
                                │
                                └──► Periodic Mailbox Scanning ◄── NEW
                                     (Check for missing attachments)
                                     
┌─────────────────────────────────────────────────────────────────┐
│              Periodic Mailbox Scanning Process                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    Connect to IMAP Server
                                │
                                ▼
              Search emails: SINCE (2 days ago)
                                │
                                ▼
                    For each email found:
                                │
                    ┌───────────┴───────────┐
                    │   Extract attachments │
                    └───────────┬───────────┘
                                │
                                ▼
              Check if attachment exists in DB
              (by filename + sender + date)
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
            Exists in DB              Missing from DB
            (Skip it)                 (Download & Save)
                                            │
                                            ▼
                              Queue for Gemini Processing
```

## Implementation Details

### Function: `check_recent_emails_for_missing_attachments(account, server)`

**Purpose**: Scans mailbox for emails from recent days and retrieves missing attachments

**Parameters**:
- `account`: EmailAccount instance
- `server`: Connected IMAPClient instance

**Process**:
1. Get configurable days setting: `EMAIL_ATTACHMENT_REPROCESS_DAYS` (default: 2)
2. Calculate cutoff date: `timezone.now() - timedelta(days=N)`
3. Search mailbox: `server.search(['SINCE', date_str])`
4. For each email:
   - Extract attachment metadata (filename, sender, date)
   - Check database: `EmailAttachment.objects.filter(...).exists()`
   - If not exists: Download, save, and queue for processing

**Duplicate Detection**:
```python
existing = EmailAttachment.objects.filter(
    account=account,
    filename=filename,
    sender=sender,
    email_date=email_date_obj
).exists()
```

### Integration: `monitor_account(account)` Function

**Enhancements**:
- Added `idle_cycle_count` to track IDLE cycles
- Set `CHECK_INTERVAL_CYCLES = 4` (~2 hours between checks)
- Perform initial check on connection
- Increment counter after each IDLE cycle
- Trigger check when counter reaches interval

**Code Structure**:
```python
idle_cycle_count = 0
CHECK_INTERVAL_CYCLES = 4

# On connection:
check_recent_emails_for_missing_attachments(account, server)

# In IDLE loop:
idle_cycle_count += 1
if idle_cycle_count >= CHECK_INTERVAL_CYCLES:
    check_recent_emails_for_missing_attachments(account, server)
    idle_cycle_count = 0
```

## Configuration

### Settings

Uses existing Django setting:
```python
EMAIL_ATTACHMENT_REPROCESS_DAYS = int(os.getenv('EMAIL_ATTACHMENT_REPROCESS_DAYS', '2'))
```

**Environment Variable**:
```bash
EMAIL_ATTACHMENT_REPROCESS_DAYS=2  # Check last 2 days (default)
EMAIL_ATTACHMENT_REPROCESS_DAYS=7  # Check last 7 days (if needed)
```

**No additional configuration required** - the feature uses the same setting as the scheduled reprocessing task.

## Logging

### Log Messages to Monitor

#### Starting Check
```
[Account Name] Checking for missing attachments from emails since 15-Dec-2024...
```

#### Results Found
```
[Account Name] Found 45 emails from last 2 days. Checking for missing attachments...
[Account Name] Found missing attachment: invoice_123.pdf (DB id: 456)
[Account Name] Found missing attachment: receipt.pdf (DB id: 457)
[Account Name] Retrieved 2 missing attachment(s) from recent emails.
```

#### No Missing Attachments
```
[Account Name] All attachments from recent emails are already in the system.
```

#### Errors
```
[Account Name] Error checking recent emails for missing attachments: [error details]
```

## Benefits

### 1. Complete Coverage
- Combines real-time processing with retroactive scanning
- Ensures no attachments are permanently missed

### 2. Self-Healing
- Automatically recovers from service interruptions
- Catches up after downtime without manual intervention

### 3. Zero Configuration
- Uses existing settings
- Works automatically once deployed
- No separate service or task to manage

### 4. Efficient Operation
- Only checks recent emails (configurable window)
- Duplicate detection prevents redundant storage
- Runs during idle times to minimize impact

### 5. Comprehensive Logging
- All actions logged for monitoring
- Easy to verify the feature is working
- Helps troubleshoot any issues

## Complete System Architecture

With this feature, the email attachment processing system now has **three-layer coverage**:

### Layer 1: Real-Time Processing (Idle Fetcher - IDLE Mode)
- **When**: As new emails arrive
- **What**: Immediately saves and processes attachments
- **Coverage**: New emails only

### Layer 2: Mailbox Scanning (Idle Fetcher - Periodic Check) ◄── THIS FEATURE
- **When**: Every ~2 hours + on connection
- **What**: Scans mailbox for missing attachments from recent emails
- **Coverage**: Retroactive - catches missed attachments

### Layer 3: Database Reprocessing (Celery Beat Task)
- **When**: Every 4 hours
- **What**: Retries processing for unprocessed PDFs in database
- **Coverage**: Processing failures only

### Combined Result
✅ Real-time processing for new emails
✅ Retroactive scanning for missed attachments  
✅ Automatic reprocessing for failures  
**= Complete coverage with no gaps**

## Usage

### Starting the Service

```bash
python manage.py idle_email_fetcher
```

The mailbox scanning feature runs automatically as part of the idle email fetcher service.

### Monitoring

Watch the logs for:
1. Periodic "Checking for missing attachments..." messages
2. Reports of found missing attachments
3. Summary of retrieved attachments

### Troubleshooting

**Issue**: Feature not running  
**Check**: Verify idle_email_fetcher service is running  
**Solution**: Restart the service

**Issue**: Too many or too few emails being checked  
**Check**: `EMAIL_ATTACHMENT_REPROCESS_DAYS` setting  
**Solution**: Adjust the days value in settings or environment variable

**Issue**: Same attachments being downloaded repeatedly  
**Check**: Duplicate detection logic (filename + sender + date)  
**Solution**: Ensure email_date is being parsed correctly from emails

## Testing

### Manual Test

1. Stop the idle_email_fetcher service
2. Send test emails with PDF attachments
3. Verify attachments are NOT in the database
4. Start the idle_email_fetcher service
5. Watch logs for:
   - "Checking for missing attachments..."
   - "Found missing attachment: [filename]"
   - "Retrieved N missing attachment(s)"
6. Verify attachments are now in the database

### Automated Test Scenarios

See `email_integration/tests.py` for test coverage of:
- Real-time processing
- Duplicate detection
- Date filtering
- Processing status handling

## Performance Considerations

### Impact on IMAP Server
- **Minimal**: Only queries metadata, not full email content
- **Scheduled**: Runs every ~2 hours, not continuously
- **Filtered**: Only checks recent emails (2 days by default)

### Database Queries
- **Efficient**: Simple EXISTS queries with indexed fields
- **Selective**: Only queries for attachments being checked
- **Optimized**: Uses database indexes on account, filename, sender, date

### Network Usage
- **Moderate**: Downloads only missing attachments
- **Selective**: Duplicate detection prevents redundant downloads
- **Throttled**: Runs periodically, not on every IDLE cycle

## Security Considerations

### Data Handling
- Uses existing authentication (IMAP credentials)
- Same security model as real-time processing
- Duplicate detection prevents data duplication

### Error Handling
- Comprehensive try-catch blocks
- Errors logged but don't crash service
- Failed checks don't prevent future attempts

## Future Enhancements (Optional)

Possible improvements for future versions:

1. **Metrics Dashboard**: Track missing attachments over time
2. **Alert System**: Notify admins when many missing attachments found
3. **Configurable Interval**: Make check frequency configurable
4. **Selective Scanning**: Option to scan only for specific file types
5. **Manual Trigger**: Admin action to force immediate scan

## Summary

The mailbox scanning feature provides:
- ✅ Retroactive detection of missing attachments
- ✅ Automatic retrieval and processing
- ✅ Self-healing capability after interruptions
- ✅ Zero additional configuration
- ✅ Comprehensive logging for monitoring
- ✅ Efficient operation during idle times

Combined with real-time processing and scheduled reprocessing, this creates a robust, self-healing email attachment processing system that ensures **no attachments are missed or left unprocessed**.

## See Also

- [EMAIL_ATTACHMENT_PROCESSING.md](./EMAIL_ATTACHMENT_PROCESSING.md) - Complete system documentation
- [PR_SUMMARY_EMAIL_ATTACHMENTS.md](./PR_SUMMARY_EMAIL_ATTACHMENTS.md) - Implementation summary
