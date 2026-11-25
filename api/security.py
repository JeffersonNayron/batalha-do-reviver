import hmac, hashlib, base64, json, time
from fastapi import HTTPException, Request
from argon2 import PasswordHasher, exceptions
from api.config import get_settings
from api.database import SessionLocal
from api.models import RootAdmin
from api.database import engine

hasher = PasswordHasher()
COOKIE = 'reviver_session'

def enabled():
    s = get_settings()
    return len(s.session_secret) >= 32 and (not s.production or engine.dialect.name == 'postgresql')

def verify_password(admin: RootAdmin, username: str, password: str):
    if not enabled() or admin is None or username.strip().casefold() != admin.username.casefold():
        return False
    try:
        return hasher.verify(admin.password_hash, password)
    except (exceptions.VerificationError, exceptions.InvalidHashError):
        return False

def _sign(payload):
    secret = get_settings().session_secret.encode()
    return hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()

def issue_token(version: int):
    body = base64.urlsafe_b64encode(json.dumps({'role':'admin','version':version,'exp':int(time.time())+8*3600}).encode()).decode().rstrip('=')
    return f'{body}.{_sign(body)}'

def admin_guard(request: Request):
    if not enabled(): raise HTTPException(503, 'Painel indisponível até configurar autenticação')
    token = request.cookies.get(COOKIE, '')
    try:
        body, sig = token.split('.', 1)
        if not hmac.compare_digest(sig, _sign(body)): raise ValueError()
        claims = json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
        if claims.get('role') != 'admin' or claims.get('exp',0) < int(time.time()): raise ValueError()
        with SessionLocal() as db:
            admin=db.get(RootAdmin,1)
            if not admin or claims.get("version") != admin.session_version: raise ValueError()
        return True
    except (ValueError, TypeError, KeyError): raise HTTPException(401, 'Autenticação necessária')
