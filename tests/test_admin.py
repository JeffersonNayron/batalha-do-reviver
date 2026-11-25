import json
from io import BytesIO
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import update

from api.accounts import deliver_reset
from api.config import get_settings
from api.database import SessionLocal
from api.models import RootAdmin
from api.security import hasher


def test_resend_delivers_the_reset_message(monkeypatch):
    monkeypatch.setenv('RESEND_API_KEY', 'test-key')
    monkeypatch.setenv('RESEND_FROM', 'Reviver <reviver@example.test>')
    with patch('api.accounts.urlopen', return_value=BytesIO(b'{"id":"email-id"}')) as send:
        deliver_reset('admin@example.test', 'link de recuperação')

    request = send.call_args.args[0]
    assert request.full_url == 'https://api.resend.com/emails'
    assert request.get_method() == 'POST'
    assert request.get_header('Authorization') == 'Bearer test-key'
    assert json.loads(request.data) == {
        'from': 'Reviver <reviver@example.test>',
        'to': ['admin@example.test'],
        'subject': 'Reviver | Redefinição de senha',
        'text': 'link de recuperação',
    }


def test_admin_can_save_and_recover_access(client, monkeypatch):
    settings = get_settings()
    password = 'initial-test-password'
    new_password = 'new-test-password'
    monkeypatch.setattr(settings, 'session_secret', 'test-secret-for-local-tests-only!!')
    monkeypatch.setattr(settings, 'public_base_url', 'https://example.test')
    monkeypatch.setattr(settings, 'admin_email', 'admin@example.test')
    monkeypatch.delenv('RESEND_API_KEY', raising=False)
    for key in ('SMTP_HOST', 'SMTP_FROM', 'SMTP_USER', 'SMTP_PASSWORD'):
        monkeypatch.setenv(key, 'smtp@example.test')

    with SessionLocal() as db:
        db.execute(update(RootAdmin).where(RootAdmin.id == 1).values(password_hash=hasher.hash(password)))
        db.commit()

    assert client.get('/api/v1/auth/status').json()['recovery'] is True
    login = '/api/v1/auth/login'
    event = '/api/v1/admin/events'
    assert client.get(event).status_code == 401
    assert client.post(login, json={'username': settings.admin_username, 'password': password}).status_code == 200
    existing = client.get(event).json()[0]
    draft = {**existing, 'slug': 'admin-test-draft', 'published': False}
    created = client.post(event, json=draft)
    assert created.status_code == 201
    assert client.get('/api/v1/events/admin-test-draft').status_code == 404
    assert client.put(f'{event}/{created.json()["id"]}', json={**draft, 'published': True}).status_code == 200
    assert client.get('/api/v1/events/admin-test-draft').status_code == 200
    client.put(f'{event}/{created.json()["id"]}', json=draft).raise_for_status()

    with patch('api.accounts.smtplib.SMTP') as smtp:
        request = '/api/v1/auth/reset-request'
        payload = {'username': settings.admin_username}
        assert client.post(request, json=payload).status_code == 200
        assert client.post(request, json=payload).status_code == 200
        send = smtp.return_value.__enter__.return_value.send_message
        send.assert_called_once()
        link = send.call_args.args[0].get_content().splitlines()[1]
        token = parse_qs(urlsplit(link).query)['reset'][0]

    old_session = client.cookies.get('reviver_session')
    confirm = '/api/v1/auth/reset-confirm'
    payload = {'token': token, 'password': new_password}
    assert client.post(confirm, json=payload).status_code == 200
    assert client.post(confirm, json=payload).status_code == 400
    assert client.get(event, headers={'Cookie': f'reviver_session={old_session}'}).status_code == 401
    assert client.post(login, json={'username': settings.admin_username, 'password': password}).status_code == 401
    assert client.post(login, json={'username': settings.admin_username, 'password': new_password}).status_code == 200
    client.cookies.clear()
