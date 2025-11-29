# Stripe Webhook Troubleshooting Guide

## Quick Diagnostic Steps

### 1. Test if Webhook Endpoint is Accessible

Visit this URL in your browser (replace with your Railway domain):
```
https://rippleskillshare.up.railway.app/payments/webhooks/stripe/
```

**Expected Response:**
```json
{
  "status": "ok",
  "message": "Webhook endpoint is accessible",
  "webhook_secret_configured": true,
  "stripe_secret_configured": true
}
```

**If you get a 404:**
- Check that Railway has deployed the latest code
- Verify the URL path matches exactly: `/payments/webhooks/stripe/`
- Check Railway deployment logs for errors

**If `webhook_secret_configured` is `false`:**
- The `STRIPE_WEBHOOK_SECRET` environment variable is not set in Railway
- Go to Railway → Variables → Add `STRIPE_WEBHOOK_SECRET`

### 2. Check Stripe Dashboard for Webhook Events

1. Go to [Stripe Dashboard → Webhooks](https://dashboard.stripe.com/test/webhooks)
2. Click on your webhook endpoint
3. Check the **"Recent events"** section

**What to look for:**
- ✅ **200 OK** - Webhook is working correctly
- ❌ **400 Bad Request** - Signature verification failed (check `STRIPE_WEBHOOK_SECRET`)
- ❌ **404 Not Found** - URL is wrong or not accessible
- ❌ **500 Internal Server Error** - There's an error in the webhook handler

### 3. Check Railway Logs

In Railway dashboard:
1. Go to your project → **Deployments**
2. Click on the latest deployment
3. View **Logs**

**Look for:**
- `STRIPE WEBHOOK RECEIVED` - Webhook is being called
- `✓ Webhook signature verified successfully` - Signature verification passed
- `✓ Received Stripe webhook: checkout.session.completed` - Event received
- `✓ Successfully processed checkout.session.completed` - Enrollment created

**Error messages to watch for:**
- `❌ Invalid signature` - Webhook secret mismatch
- `❌ Missing metadata` - Payment metadata not set correctly
- `❌ Error processing checkout.session.completed` - Error in enrollment creation

### 4. Verify Environment Variables in Railway

Go to Railway → **Variables** and verify these are set:

```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Important:**
- All three must be set
- `STRIPE_WEBHOOK_SECRET` must match the signing secret from Stripe Dashboard
- No extra spaces or quotes around the values

### 5. Test Payment Flow

1. Make a test payment on your Railway site
2. Use Stripe test card: `4242 4242 4242 4242`
3. Complete the payment
4. Check:
   - Stripe Dashboard → Webhooks → Recent events (should show `checkout.session.completed`)
   - Railway logs (should show webhook processing)
   - Your database (should have new enrollment)

## Common Issues and Fixes

### Issue: "Invalid signature" errors

**Symptoms:**
- Stripe Dashboard shows `400 Bad Request`
- Railway logs show: `❌ Invalid signature`

**Fix:**
1. Go to Stripe Dashboard → Webhooks → Your endpoint
2. Click "Reveal" next to "Signing secret"
3. Copy the **entire** secret (starts with `whsec_`)
4. Go to Railway → Variables
5. Update `STRIPE_WEBHOOK_SECRET` with the exact value
6. Redeploy Railway (or wait for auto-deploy)

### Issue: Webhook events not appearing

**Symptoms:**
- No events in Stripe Dashboard → Recent events
- Payment succeeds but enrollment doesn't happen

**Possible causes:**
1. **Webhook URL is wrong**
   - Check the URL in Stripe Dashboard matches exactly: `https://rippleskillshare.up.railway.app/payments/webhooks/stripe/`
   - Must be HTTPS, not HTTP
   - Must have trailing slash `/`

2. **Webhook endpoint not accessible**
   - Test the GET endpoint (see Step 1 above)
   - Check Railway deployment is live
   - Check Railway logs for startup errors

3. **Events not selected**
   - Go to Stripe Dashboard → Webhooks → Your endpoint
   - Click "Edit"
   - Ensure `checkout.session.completed` is selected
   - Save changes

### Issue: Payment succeeds but user not enrolled

**Symptoms:**
- Payment completes successfully
- Webhook shows `200 OK` in Stripe Dashboard
- But user is not enrolled in the class

**Check Railway logs for:**
- `✓ Successfully processed checkout.session.completed` - If missing, webhook handler failed
- `❌ Missing metadata` - Payment metadata not set correctly
- `❌ Error processing checkout.session.completed` - Error in enrollment creation

**Fix:**
1. Check Railway logs for the exact error
2. Verify payment metadata includes `class_id` and `user_id`
3. Check that the class and user exist in the database

### Issue: Webhook works locally but not on Railway

**Common causes:**
1. **Webhook secret not set in Railway**
   - Local: Stripe CLI handles this automatically
   - Railway: Must manually set `STRIPE_WEBHOOK_SECRET`

2. **Different Stripe keys**
   - Local: Using test keys from `.env`
   - Railway: Must use same test keys (or switch to live keys)

3. **URL differences**
   - Local: `http://localhost:8000/payments/webhooks/stripe/`
   - Railway: `https://rippleskillshare.up.railway.app/payments/webhooks/stripe/`
   - Must configure Railway URL in Stripe Dashboard

## Debugging Checklist

- [ ] Webhook endpoint is accessible (GET request returns JSON)
- [ ] `STRIPE_WEBHOOK_SECRET` is set in Railway
- [ ] Webhook secret in Railway matches Stripe Dashboard
- [ ] Webhook URL in Stripe Dashboard is correct (HTTPS, trailing slash)
- [ ] `checkout.session.completed` event is selected in Stripe Dashboard
- [ ] Railway deployment is live and running
- [ ] Railway logs show webhook being received
- [ ] Payment metadata includes `class_id` and `user_id`
- [ ] Test payment completes successfully
- [ ] Stripe Dashboard shows webhook events with `200 OK`

## Still Not Working?

1. **Check Railway logs** - Look for error messages with `❌` prefix
2. **Check Stripe Dashboard** - View webhook event details and response
3. **Test the endpoint** - Use the GET endpoint to verify accessibility
4. **Verify environment variables** - Double-check all three Stripe variables are set
5. **Check webhook secret** - Ensure it matches exactly (copy-paste, no spaces)

## Need More Help?

Share these details:
1. Railway logs (last 50 lines after a test payment)
2. Stripe Dashboard → Webhooks → Recent events (screenshot)
3. Response from GET endpoint test
4. Railway environment variables (masked values)

