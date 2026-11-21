import hmac, hashlib, base64, json, time
from fastapi import HTTPException, Request
from argon2 import PasswordHasher, exceptions
from api.config import get_settings

hasher = PasswordHasher()
COOKIE = 'reviver_session'

def enabled():
    s = get_settings()
    return bool(s.admin_password_hash and s.session_secret and len(s.session_secret) >= 32)

def verify_password(password: str):
    s = get_settings()
    if not enabled(): return False
    try: return hasher.verify(s.admin_password_hash, password)
    except (exceptions.VerificationError, exceptions.InvalidHashError): return False

def _sign(payload):
    secret = get_settings().session_secret.encode()
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

def issue_token():
    body = base64.urlsafe_b64encode(json.dumps({'role':'admin','exp':int(time.time())+8*3600}).encode()).decode().rstrip('=')
    return f'{body}.{_sign(body)}'

def admin_guard(request: Request):
    if not enabled(): raise HTTPException(503, 'Painel indisponível até configurar autenticação')
    token = request.cookies.get(COOKIE, '')
    try:
        body, sig = token.split('.', 1)
        if not hmac.compare_digest(sig, _sign(body)): raise ValueError()
        claims = json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
        if claims.get('role') != 'admin' or claims.get('exp',0) < int(time.time()): raise ValueError()
        return True
    except (ValueError, TypeError, KeyError): raise HTTPException(401, 'Autenticação necessária')
