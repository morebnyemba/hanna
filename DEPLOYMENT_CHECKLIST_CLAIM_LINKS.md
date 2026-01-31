# Client Claim Links - Deployment Checklist

## Pre-Deployment

- [ ] Review all code changes
- [ ] Run tests (if any exist)
- [ ] Test migration on local database
- [ ] Verify frontend compiles without errors
- [ ] Backup production database

## Code Review

### Backend Changes
- [ ] `customer_data/models.py` - ClientClaimToken model added
- [ ] `customer_data/serializers.py` - Two new serializers added
- [ ] `customer_data/views.py` - Two new API views added
- [ ] `customer_data/urls.py` - Two new URL patterns added
- [ ] `customer_data/admin.py` - ClientClaimTokenAdmin added
- [ ] `installation_systems/admin.py` - Generate action added
- [ ] `customer_data/migrations/0005_clientclaimtoken.py` - Migration file created

### Frontend Changes
- [ ] `app/client/claim/[token]/page.tsx` - New claim page created
- [ ] No changes to existing pages (backward compatible)

## Testing Checklist

### Local Testing (Before Deployment)

1. **Run Migrations**
   - [ ] `python manage.py migrate customer_data`
   - [ ] Check no errors
   - [ ] Verify table created: `ClientClaimToken`

2. **Admin Interface**
   - [ ] Login to `/admin/`
   - [ ] Navigate to Installation System Records
   - [ ] Verify "Generate claim link(s)" action appears
   - [ ] Create test ISR with commissioned status
   - [ ] Generate claim token for test ISR
   - [ ] Navigate to Client Claim Tokens
   - [ ] Verify new token appears
   - [ ] Check token shows: address, customer, status, claim link

3. **Frontend Claim Page**
   - [ ] Open generated claim link in browser
   - [ ] Verify page loads (not 404)
   - [ ] Verify ISR details displayed correctly
   - [ ] Fill registration form with valid data
   - [ ] Submit form
   - [ ] Verify success message appears
   - [ ] Check redirected to `/client/dashboard`
   - [ ] Verify user created in Django admin
   - [ ] Verify CustomerProfile updated with user link

4. **Error Cases**
   - [ ] Test invalid token → shows "Invalid claim token"
   - [ ] Test already-claimed token → shows "Already claimed"
   - [ ] Test expired token → shows "Expired"
   - [ ] Test empty form fields → shows validation errors
   - [ ] Test mismatched passwords → shows error
   - [ ] Test weak password → shows error
   - [ ] Test duplicate email → shows error

5. **Token Properties**
   - [ ] Check token marked as claimed after registration
   - [ ] Check claimed_by_user filled
   - [ ] Check claimed_at timestamp set
   - [ ] Try using same token again → fails

## Staging Deployment

1. **Code Deployment**
   - [ ] Commit and push all changes
   - [ ] Pull changes on staging server
   - [ ] Verify no merge conflicts

2. **Run Migrations**
   - [ ] `python manage.py migrate customer_data --database=staging`
   - [ ] Verify migration succeeded
   - [ ] Check table exists in staging database

3. **Restart Services**
   - [ ] Restart Django backend
   - [ ] Restart Nginx
   - [ ] Rebuild Next.js if needed
   - [ ] Check health: `/health/` endpoint

4. **Smoke Test**
   - [ ] Login to staging admin
   - [ ] Generate test claim token
   - [ ] Test claim flow in staging frontend
   - [ ] Verify user created in staging database
   - [ ] Test error cases
   - [ ] Check logs for any errors

## Production Deployment

1. **Backup**
   - [ ] Create database backup
   - [ ] Store backup location and timestamp
   - [ ] Verify backup integrity

2. **Code Deployment**
   - [ ] Tag release in git (e.g., `v1.2.0-claim-links`)
   - [ ] Pull changes on production
   - [ ] Verify correct branch/commit

3. **Run Migrations**
   - [ ] `python manage.py migrate customer_data`
   - [ ] Verify migration succeeded
   - [ ] Check no errors in logs

4. **Restart Services**
   ```bash
   # Option A: Docker Compose
   docker-compose restart backend
   docker-compose restart frontend
   
   # Option B: Manual
   systemctl restart hanna-backend
   systemctl restart hanna-frontend
   ```

   - [ ] Backend restarted
   - [ ] Frontend restarted
   - [ ] Wait 1-2 minutes for services to be ready
   - [ ] Check health endpoints

5. **Verify Deployment**
   - [ ] Check Django admin loads: `/admin/`
   - [ ] Verify Installation System Records page loads
   - [ ] Verify Client Claim Tokens page exists
   - [ ] Check API endpoints respond:
     - [ ] POST `/crm-api/customer-data/claim/validate/` → 400 (no token)
     - [ ] POST `/crm-api/customer-data/claim/register/` → 400 (no token)
   - [ ] Test claim flow end-to-end

6. **Monitor**
   - [ ] Check error logs: `docker-compose logs backend`
   - [ ] Check frontend console for errors
   - [ ] Monitor CPU/memory usage
   - [ ] Check response times are normal

## Post-Deployment

1. **Documentation**
   - [ ] Share links with support team:
     - [ ] `CLAIM_LINK_QUICK_REFERENCE.md`
     - [ ] `CLIENT_SELF_ONBOARDING_GUIDE.md`
     - [ ] `CLAIM_LINK_VISUAL_GUIDE.md`
   - [ ] Update internal wiki/docs
   - [ ] Share with customer success team

2. **Training**
   - [ ] Train admin on how to generate claim links
   - [ ] Train support on troubleshooting
   - [ ] Demo the feature to team
   - [ ] Create internal FAQ

3. **Monitoring**
   - [ ] Set up metrics for:
     - [ ] Number of tokens generated
     - [ ] Number of tokens claimed
     - [ ] Claim success rate
     - [ ] Average time to claim
     - [ ] Failed claim attempts
   - [ ] Monitor for errors in logs
   - [ ] Check for expired tokens piling up

4. **Customer Communication**
   - [ ] Update onboarding emails with new process
   - [ ] Create help documentation for customers
   - [ ] Add FAQ to website/knowledge base
   - [ ] Send announcement to existing admins

## Rollback Plan

If issues occur, rollback as follows:

1. **Immediate Actions**
   - [ ] Identify issue in logs
   - [ ] Note affected users
   - [ ] Disable feature in admin if needed

2. **Database Rollback**
   - [ ] Restore from backup (if needed)
   - [ ] Revert migration: `python manage.py migrate customer_data 0004`

3. **Code Rollback**
   - [ ] Checkout previous version
   - [ ] Restart services
   - [ ] Verify system working

4. **Communication**
   - [ ] Notify support team
   - [ ] Inform affected customers
   - [ ] Create incident report

## Rollback Commands

```bash
# Revert migration (move to previous state)
python manage.py migrate customer_data 0004

# Or use zero to remove all customer_data migrations
python manage.py migrate customer_data zero

# Restart services
docker-compose restart backend

# Check status
docker-compose logs backend
```

## Files to Deploy

### Backend
- [x] `whatsappcrm_backend/customer_data/models.py` (modified)
- [x] `whatsappcrm_backend/customer_data/serializers.py` (modified)
- [x] `whatsappcrm_backend/customer_data/views.py` (modified)
- [x] `whatsappcrm_backend/customer_data/urls.py` (modified)
- [x] `whatsappcrm_backend/customer_data/admin.py` (modified)
- [x] `whatsappcrm_backend/installation_systems/admin.py` (modified)
- [x] `whatsappcrm_backend/customer_data/migrations/0005_clientclaimtoken.py` (new)

### Frontend
- [x] `hanna-management-frontend/app/client/claim/[token]/page.tsx` (new)

### Documentation (optional but recommended)
- [x] `CLIENT_SELF_ONBOARDING_GUIDE.md`
- [x] `CLAIM_LINK_QUICK_REFERENCE.md`
- [x] `CLAIM_LINK_VISUAL_GUIDE.md`
- [x] `IMPLEMENTATION_SUMMARY_CLAIM_LINKS.md`

## Success Criteria

✅ All tests pass
✅ Claim links can be generated from admin
✅ Clients can claim installations
✅ Users created with correct data
✅ Auto-login works after claiming
✅ Tokens properly marked as claimed
✅ Expired tokens show correct error
✅ Already-claimed tokens show correct error
✅ No errors in logs
✅ Response times normal
✅ Support team trained
✅ Documentation shared

## Issues Found During Testing

| Issue | Status | Resolution |
|-------|--------|------------|
| Example: "Token validation fails" | ✅ Fixed | Updated serializer validation |
| (Add any issues found) | | |

## Sign-Off

- [ ] Development Lead: _________________ Date: _______
- [ ] QA Lead: _________________ Date: _______
- [ ] DevOps Lead: _________________ Date: _______
- [ ] Product Manager: _________________ Date: _______

## Post-Deployment Notes

```
Date Deployed: ______________
Deployed By: ______________
Duration: ______________
Issues Encountered: ______________
Resolution: ______________
Deployment Successful: ☐ Yes ☐ No
```

## Future Improvements

- [ ] Email template for sending claim links
- [ ] Bulk email feature
- [ ] SMS sending integration
- [ ] QR code generation
- [ ] Dashboard for claim metrics
- [ ] Auto-reminder emails (day 7, 14, 21)
- [ ] Claim rate analytics
- [ ] Social login option
- [ ] One-time password (OTP) alternative

## Contacts

**Technical Support:**
- Backend Lead: _________________ Phone: _______
- Frontend Lead: _________________ Phone: _______
- DevOps: _________________ Phone: _______

**Business Support:**
- Product Manager: _________________ Email: _______
- Customer Success: _________________ Email: _______

---

**Total Estimated Time:** 2-3 hours
- Local testing: 45 min
- Staging deployment: 30 min
- Production deployment: 30 min
- Verification & monitoring: 30 min
- Training & documentation: 30 min
