# SendGrid Email Troubleshooting Guide

If emails are not being sent through SendGrid, follow these steps:

## 1. Verify Your Sender Email Address

**This is the #1 most common issue!**

SendGrid requires you to verify the sender email address before you can send emails.

### Steps to Verify Sender Email:

1. Go to [SendGrid Dashboard](https://app.sendgrid.com)
2. Navigate to **Settings** → **Sender Authentication**
3. Click **Verify a Single Sender**
4. Enter the email address you're using in `DEFAULT_FROM_EMAIL`
5. Fill out the form and click **Create**
6. Check your email inbox and click the verification link

**Important**: The email address in `DEFAULT_FROM_EMAIL` must match a verified sender in SendGrid.

## 2. Check Environment Variables

Make sure these are set correctly in Railway (or your deployment platform):

```env
SENDGRID_API_KEY=SG.your-actual-api-key-here
DEFAULT_FROM_EMAIL=your-verified-email@domain.com
USE_CONSOLE_EMAIL=False
```

### To verify in Railway:
1. Go to your Railway project
2. Click on your service
3. Go to **Variables** tab
4. Check that `SENDGRID_API_KEY` is set correctly

## 3. Check API Key Permissions

Your SendGrid API key needs "Mail Send" permissions:

1. Go to [SendGrid API Keys](https://app.sendgrid.com/settings/api_keys)
2. Click on your API key
3. Make sure **Mail Send** permission is enabled
4. If not, create a new API key with "Full Access" or "Restricted Access" with Mail Send enabled

## 4. Test Email Configuration

### Check Logs

When you start your Django server, you should see:

```
============================================================
Email Configuration:
  Backend: SendGrid SMTP
  Host: smtp.sendgrid.net
  Port: 587
  From Email: your-email@domain.com
  API Key: Set
============================================================
```

If you see "Console Backend" instead, check:
- Is `SENDGRID_API_KEY` set?
- Is `USE_CONSOLE_EMAIL=False`?

### Test Sending an Email

You can test by:
1. Registering a new user (this will send a verification email)
2. Using password reset (this will send a reset email)
3. Check the server logs for any error messages

## 5. Common Error Messages

### "550 The from address does not match a verified Sender Identity"

**Solution**: Verify your sender email in SendGrid (see step 1)

### "403 Forbidden" or "401 Unauthorized"

**Solution**: 
- Check your API key is correct
- Make sure API key has Mail Send permissions
- Regenerate API key if needed

### "Connection timeout" or "Connection refused"

**Solution**:
- Check your firewall/network settings
- Verify `EMAIL_HOST = 'smtp.sendgrid.net'` and `EMAIL_PORT = 587`
- Try port 465 with SSL instead (requires `EMAIL_USE_SSL = True`)

## 6. Check SendGrid Activity

1. Go to [SendGrid Activity](https://app.sendgrid.com/activity)
2. Look for your email sends
3. Check for any error messages or bounces
4. Click on failed sends to see the error reason

## 7. Email Going to Spam?

If emails are being sent but going to spam:

1. **Verify your domain** (recommended for production):
   - Go to **Settings** → **Sender Authentication** → **Authenticate Your Domain**
   - Follow the DNS setup instructions
   - This improves deliverability significantly

2. **Check email content**:
   - Avoid spam trigger words
   - Include proper unsubscribe links
   - Use proper HTML formatting

## 8. Debug Mode

To see detailed error messages, set `DEBUG=True` temporarily and check your server logs when sending emails.

## Quick Checklist

- [ ] Sender email is verified in SendGrid
- [ ] `SENDGRID_API_KEY` is set correctly in environment variables
- [ ] `DEFAULT_FROM_EMAIL` matches verified sender email
- [ ] `USE_CONSOLE_EMAIL=False` in production
- [ ] API key has "Mail Send" permissions
- [ ] Check SendGrid Activity dashboard for errors
- [ ] Check server logs for error messages

## Still Not Working?

1. Check Railway logs: Go to your Railway project → Deployments → View logs
2. Check SendGrid Activity dashboard for specific error messages
3. Try using SendGrid's test email feature in their dashboard
4. Verify your SendGrid account is not suspended or limited

## Alternative: Use SendGrid Web API (More Reliable)

If SMTP continues to have issues, you can use SendGrid's Web API instead. This requires installing `sendgrid-django` package, but it's more reliable than SMTP.

