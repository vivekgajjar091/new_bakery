# Email Configuration Fix for Bakehouse

## Problem
The automatic email sending after order placement is failing with the error:
```
(535, b'5.7.8 Username and Password not accepted. For more information, go to\n5.7.8  https://support.google.com/mail/?p=BadCredentials')
```

## Root Cause
The Gmail SMTP authentication is failing because:
1. The password in `.env` file is incorrect/placeholder
2. Gmail requires an App Password for SMTP access (not regular password)

## Solution Steps

### Step 1: Enable 2-Factor Authentication on Gmail Account
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already enabled
3. Follow the setup process

### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" from the app dropdown
3. Select "Other (Custom name)" and enter "Bakehouse Django App"
4. Click "Generate"
5. Copy the 16-character password (format: xxxx xxxx xxxx xxxx)

### Step 3: Update Environment Variables
Edit the `.env` file and replace the password:

```env
EMAIL_HOST_USER=bakehous023@gmail.com
EMAIL_HOST_PASSWORD=xxxx-xxxx-xxxx-xxxx  # Replace with your actual 16-char app password
```

### Step 4: Test the Configuration
Run the test script to verify:
```bash
cd d:\bakery\bakehouse
python test_email.py
```

### Step 5: Restart the Application
After updating the `.env` file, restart your Django application for the changes to take effect.

## Alternative Solutions

### Option A: Use a Different Email Service
If Gmail continues to have issues, consider using:
- SendGrid (recommended for production)
- Mailgun
- Amazon SES

### Option B: Use Environment-Specific Configuration
For development, you could use Django's console email backend:
```python
# In settings.py (for development only)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Security Notes
- Never commit actual passwords to version control
- Use different credentials for development and production
- Consider using a dedicated email service for production apps

## Current Configuration Status
- Email Host: smtp.gmail.com ✅
- Email Port: 587 ✅  
- Use TLS: True ✅
- Email User: bakehous023@gmail.com ✅
- Email Password: ❌ (needs to be updated with valid App Password)
