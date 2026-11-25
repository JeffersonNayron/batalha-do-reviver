import hashlib
import json
import os
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from sqlalchemy import select, update
from api.models import RootAdmin
from api.config import get_settings
from api.security import hasher

def seed_admin(db):
    settings = get_settings()
    admin = db.get(RootAdmin, 1)
    if admin is None:
        admin = RootAdmin(id=1, name='', phone='', username=settings.admin_username,
                          email=settings.admin_email, password_hash=settings.admin_password_hash)
        db.add(admin)
    elif not admin.password_hash and settings.admin_password_hash:
        admin.password_hash = settings.admin_password_hash
    db.commit()


def recovery_enabled():
    settings = get_settings()
    resend = os.getenv('RESEND_API_KEY') and os.getenv('RESEND_FROM')
    smtp = all(os.getenv(key) for key in ('SMTP_HOST', 'SMTP_FROM', 'SMTP_USER', 'SMTP_PASSWORD'))
    return bool(settings.admin_email and settings.public_base_url.startswith('https://') and (resend or smtp))


def deliver_reset(recipient, body):
    subject = 'Reviver | Redefinição de senha'
    api_key = os.getenv('RESEND_API_KEY')
    sender = os.getenv('RESEND_FROM')
    if api_key and sender:
        payload = json.dumps({'from': sender, 'to': [recipient], 'subject': subject, 'text': body})
        request = Request('https://api.resend.com/emails', data=payload.encode(), headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Batalha-do-Reviver/1.0',
        }, method='POST')
        with urlopen(request, timeout=10) as response:
            if not json.load(response).get('id'):
                raise ValueError('Resend não confirmou o envio')
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = os.environ['SMTP_FROM']
    msg['To'] = recipient
    msg.set_content(body)
    with smtplib.SMTP(os.environ['SMTP_HOST'], int(os.getenv('SMTP_PORT', '587')), timeout=10) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        smtp.send_message(msg)

def send_reset(db, admin):
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode()).hexdigest()
    now = int(time.time())
    result = db.execute(update(RootAdmin).where(
        RootAdmin.id == admin.id, RootAdmin.reset_until <= now + 1740,
    ).values(reset_digest=digest, reset_until=now + 1800))
    db.commit()
    if not result.rowcount:
        return

    settings = get_settings()
    link = settings.public_base_url + '/admin?' + urlencode({'reset': token})
    try:
        deliver_reset(settings.admin_email, f'Para definir sua senha, acesse o link válido por 30 minutos:\n{link}\n'
                      'Se não solicitou, ignore esta mensagem.')
    except (OSError, ValueError):
        db.execute(update(RootAdmin).where(RootAdmin.id == admin.id, RootAdmin.reset_digest == digest)
                   .values(reset_digest='', reset_until=0))
        db.commit()
        raise

def consume_reset(db, token, password):
    digest = hashlib.sha256(token.encode()).hexdigest()
    match = (RootAdmin.id == 1, RootAdmin.reset_digest == digest)
    if db.scalar(select(RootAdmin.id).where(*match, RootAdmin.reset_until >= int(time.time()))) is None:
        return False
    password_hash = hasher.hash(password)
    result = db.execute(update(RootAdmin).where(*match, RootAdmin.reset_until >= int(time.time())).values(
        password_hash=password_hash, reset_digest='', reset_until=0,
        session_version=RootAdmin.session_version + 1,
    ))
    db.commit()
    return result.rowcount == 1
