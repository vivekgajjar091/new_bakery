#!/usr/bin/env python
import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bakehouse.settings')
django.setup()

def test_email_configuration():
    """Test email configuration by sending a test email"""
    try:
        print("Testing email configuration...")
        print(f"Email Host: {settings.EMAIL_HOST}")
        print(f"Email Port: {settings.EMAIL_PORT}")
        print(f"Email User: {settings.EMAIL_HOST_USER}")
        print(f"Use TLS: {settings.EMAIL_USE_TLS}")
        
        # Send test email
        send_mail(
            subject='Test Email - Bakehouse Configuration',
            message='This is a test email to verify the SMTP configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to self for testing
            fail_silently=False,
        )
        
        print("SUCCESS: Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"ERROR: Email failed to send: {e}")
        return False

if __name__ == "__main__":
    test_email_configuration()
