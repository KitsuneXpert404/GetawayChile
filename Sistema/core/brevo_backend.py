import os
import json
import urllib.request
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)

class BrevoAPIBackend(BaseEmailBackend):
    """
    Custom Django Email Backend to send emails via Brevo HTTP API (Port 443)
    This bypasses Render's firewall block on SMTP port 587.
    """
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        api_key = os.environ.get('BREVO_API_KEY')
        if not api_key:
            logger.error("BREVO_API_KEY no está configurado en el entorno.")
            if not self.fail_silently:
                raise ValueError("BREVO_API_KEY es obligatorio para enviar correos.")
            return 0

        num_sent = 0
        for message in email_messages:
            if self._send(message, api_key):
                num_sent += 1
        return num_sent

    def _send(self, email_message, api_key):
        url = "https://api.brevo.com/v3/smtp/email"
        
        # Parse Sender
        from_email = email_message.from_email or settings.DEFAULT_FROM_EMAIL
        if "<" in from_email and ">" in from_email:
            name, email = from_email.split("<")
            sender = {"name": name.strip(), "email": email.strip(">").strip()}
        else:
            sender = {"name": "Getaway Chile", "email": from_email.strip()}
            
        # Parse Recipients
        to_list = [{"email": addr.strip()} for addr in email_message.to]
        if not to_list:
            return False

        payload = {
            "sender": sender,
            "to": to_list,
            "subject": email_message.subject,
        }
        
        # Add content body (HTML or Plain)
        if hasattr(email_message, 'alternatives') and email_message.alternatives:
            for alt_content, alt_mimetype in email_message.alternatives:
                if alt_mimetype == 'text/html':
                    payload["htmlContent"] = alt_content
                    break
        else:
            payload["textContent"] = email_message.body
            
        data = json.dumps(payload).encode('utf-8')
        
        try:
            req = urllib.request.Request(url, data=data)
            req.add_header('accept', 'application/json')
            req.add_header('api-key', api_key)
            req.add_header('content-type', 'application/json')
            
            # 10s timeout to prevent Server 502 Bad Gateway
            response = urllib.request.urlopen(req, timeout=10)
            if response.getcode() in (200, 201, 202):
                return True
            else:
                logger.error(f"Brevo API error: HTTP {response.getcode()}")
                return False
        except Exception as e:
            logger.error(f"Brevo API request failed: {e}")
            if not self.fail_silently:
                raise
            return False
