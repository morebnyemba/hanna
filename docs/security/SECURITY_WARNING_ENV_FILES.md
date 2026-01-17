# ⚠️ SECURITY WARNING: .env File Tracked in Git

## 🚨 Critical Security Issue

The `.env` file in `whatsappcrm_backend/.env` is currently being tracked in Git and has been committed with sensitive credentials.

**This is a security risk because:**
- The file contains SMTP passwords
- The file contains database passwords
- Anyone with access to the repository can see these credentials
- The credentials are visible in commit history

---

## 📋 Current Status

### Files Affected
- `whatsappcrm_backend/.env` - Contains production credentials
- `whatsappcrm_backend/.env.prod` - Contains production credentials
- `.env` - Root level env file

### Credentials Exposed
- SMTP password: `EMAIL_HOST_PASSWORD`
- Database password: `DB_PASSWORD`
- Redis password (in CELERY_BROKER_URL and REDIS_URL)
- WhatsApp App Secret: `WHATSAPP_APP_SECRET`
- Mailu IMAP password: `MAILU_IMAP_PASS`

---

## ✅ Immediate Actions Required

### 1. Change All Exposed Credentials

**IMPORTANT:** Since the credentials are in Git history, they should be considered compromised and changed immediately.

#### Change SMTP Password
1. Log into your email server admin panel
2. Change the password for `installations@hanna.co.zw`
3. Update the new password in `.env` file
4. Restart services

#### Change Database Password
1. Connect to PostgreSQL:
   ```bash
   docker exec -it whatsappcrm_db psql -U crm_user -d whatsapp_crm_dev
   ```
2. Change password:
   ```sql
   ALTER USER crm_user WITH PASSWORD 'new_secure_password_here';
   ```
3. Update `.env` file with new password
4. Restart services

#### Change Redis Password
1. Update `redis.conf` with new password
2. Update `.env` file:
   - `CELERY_BROKER_URL`
   - `REDIS_URL`
3. Restart Redis and services

#### Change WhatsApp App Secret
1. Go to Meta Developer Console
2. Regenerate app secret
3. Update `.env` file
4. Restart services

---

### 2. Stop Tracking .env Files

#### Remove from Git Tracking (Without Deleting)
```bash
# Navigate to repository
cd /home/runner/work/hanna/hanna

# Stop tracking .env files but keep them locally
git rm --cached whatsappcrm_backend/.env
git rm --cached whatsappcrm_backend/.env.prod
git rm --cached .env

# Commit the removal
git commit -m "Stop tracking .env files for security"

# Push changes
git push origin <branch-name>
```

#### Verify .gitignore
Ensure `.gitignore` contains:
```
.env
*.env
.env.*
whatsappcrm_backend/.env
whatsappcrm_backend/.env.*
```

---

### 3. Create Template Files

Create `.env.example` files with dummy values:

#### Create `whatsappcrm_backend/.env.example`
```bash
# --- Email/SMTP Settings ---
EMAIL_HOST=mail.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=user@example.com
EMAIL_HOST_PASSWORD=your_secure_password_here
DEFAULT_FROM_EMAIL=user@example.com

# --- Database Settings ---
DB_ENGINE='django.db.backends.postgresql'
DB_NAME='your_db_name'
DB_USER='your_db_user'
DB_PASSWORD='your_secure_db_password'
DB_HOST='db'
DB_PORT='5432'

# --- Celery Settings ---
CELERY_BROKER_URL='redis://:your_redis_password@redis:6379/0'

# --- Channels (WebSocket) Settings ---
REDIS_URL='redis://:your_redis_password@redis:6379/1'

# ... etc (copy structure from .env but use placeholders)
```

**Then commit the example files:**
```bash
git add whatsappcrm_backend/.env.example
git commit -m "Add .env.example template"
git push
```

---

## 🔐 Best Practices Going Forward

### For Development
1. **Never commit .env files** - They should always be in `.gitignore`
2. **Use .env.example** - Provide templates with dummy values
3. **Document required variables** - List all needed environment variables
4. **Use different credentials** - Dev and prod should have different credentials

### For Production
1. **Use environment variables** - Set via Docker Compose or hosting platform
2. **Use secrets management** - Consider Docker Secrets or Kubernetes Secrets
3. **Rotate credentials regularly** - Change passwords periodically
4. **Limit access** - Only give credentials to those who need them
5. **Use strong passwords** - Generate random, complex passwords
6. **Enable 2FA** - Where available (email, databases, etc.)

### For Team Collaboration
1. **Share .env.example** - Commit this to Git
2. **Share credentials securely** - Use password managers (1Password, Bitwarden, etc.)
3. **Document setup process** - Make it easy for new developers
4. **Review access regularly** - Remove access for former team members

---

## 📝 Cleanup Checklist

Use this checklist to secure your repository:

### Immediate (Do Now)
- [ ] Change SMTP password
- [ ] Change database password
- [ ] Change Redis password
- [ ] Change WhatsApp app secret
- [ ] Update all .env files with new credentials
- [ ] Restart all services

### Short Term (This Week)
- [ ] Stop tracking .env files in Git
- [ ] Create .env.example templates
- [ ] Verify .gitignore is correct
- [ ] Commit and push changes
- [ ] Test that everything still works

### Medium Term (This Month)
- [ ] Implement secrets management solution
- [ ] Document credential rotation process
- [ ] Set up password manager for team
- [ ] Review who has access to credentials
- [ ] Schedule regular credential rotation

### Optional (For Maximum Security)
- [ ] Rewrite Git history to remove credentials (WARNING: This is disruptive)
- [ ] Consider making repository private (if it's public)
- [ ] Implement CI/CD secret scanning
- [ ] Set up monitoring for unauthorized access

---

## 🔄 Rotating Credentials Process

### Regular Rotation Schedule
- **Critical credentials** (DB, Redis): Every 90 days
- **Application credentials** (SMTP, API keys): Every 180 days
- **Service tokens**: When team members leave or are reassigned

### Rotation Steps
1. Generate new credential
2. Update in secure location (password manager)
3. Update .env file on production server
4. Restart affected services
5. Test that everything works
6. Deactivate old credential
7. Document the change

---

## 🚫 What NOT to Do

### Don't Do These Things
- ❌ Don't commit .env files to Git
- ❌ Don't share credentials in plain text (email, Slack, etc.)
- ❌ Don't reuse passwords across services
- ❌ Don't use simple/guessable passwords
- ❌ Don't leave default credentials
- ❌ Don't hardcode credentials in source code
- ❌ Don't share production credentials with developers
- ❌ Don't skip credential rotation

---

## 📚 Additional Resources

### Password Managers (Team)
- **1Password** - Great for teams, has CLI tool
- **Bitwarden** - Open source, self-hostable
- **LastPass** - Popular, good team features

### Secrets Management (Advanced)
- **HashiCorp Vault** - Enterprise-grade secrets management
- **Docker Secrets** - Built into Docker Swarm
- **Kubernetes Secrets** - For K8s deployments
- **AWS Secrets Manager** - For AWS deployments
- **Azure Key Vault** - For Azure deployments

### Git History Cleanup (Advanced, Risky)
- **BFG Repo-Cleaner** - Removes files from Git history
- **git filter-branch** - Built-in but complex
- ⚠️ **WARNING**: These tools rewrite history and will cause issues for other developers

---

## 🆘 If Credentials Are Already Compromised

### Signs of Compromise
- Unexpected database changes
- Unauthorized emails sent
- Unusual API usage
- Suspicious login attempts
- Service disruptions

### Immediate Response
1. **Change all credentials immediately**
2. **Check logs for unauthorized access**
3. **Review recent changes to data**
4. **Enable 2FA on all services**
5. **Consider notifying affected users**
6. **Document the incident**

### Long-term Response
1. Implement monitoring and alerting
2. Regular security audits
3. Penetration testing
4. Security training for team
5. Incident response plan

---

## 📊 Current Repository Status

### Files Currently Tracked (Security Risk)
```
whatsappcrm_backend/.env          - Contains production credentials ⚠️
whatsappcrm_backend/.env.prod     - Contains production credentials ⚠️
.env                              - Contains credentials ⚠️
```

### Credentials in Git History
Since these files have been committed, the credentials are in Git history and should be considered publicly known.

**Action Required:** Change all credentials before they can be exploited.

---

## ✅ Summary

### What Happened
The .env file with production credentials was tracked in Git and committed to the repository.

### Risk Level
**HIGH** - Credentials are exposed in Git history and potentially publicly accessible.

### Immediate Actions
1. Change all exposed credentials (SMTP, DB, Redis, WhatsApp)
2. Stop tracking .env files
3. Create .env.example templates
4. Update .gitignore

### Long-term Actions
1. Implement proper secrets management
2. Regular credential rotation
3. Team security training
4. Monitoring and alerting

---

**Security Note:** This file was created to document the security issue discovered during notification system configuration. The issue predates the current changes but should be addressed immediately.

**Date Created:** 2025-12-09  
**Priority:** HIGH  
**Status:** ACTION REQUIRED
