import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session, selectinload
from api.database import session_scope
from api.accounts import consume_reset, recovery_enabled, send_reset
from api.models import Event, Organization, MC, RootAdmin
from api.schemas import EventIn, EventOut, OrgIn, OrgOut, MCIn, MCOut, Login, ResetConfirm, ResetRequest
from api.security import COOKIE, admin_guard, enabled, verify_password, issue_token
from api.config import get_settings

router = APIRouter(prefix='/api/v1')
_login_attempts = {}

@router.get('/health')
def health(): return {'status': 'ok', 'service': 'reviver-api', 'version': '1.0.0'}

@router.get('/organizations', response_model=list[OrgOut])
def organizations(db: Session = Depends(session_scope)):
    return db.scalars(select(Organization).order_by(Organization.name)).all()

@router.get('/events', response_model=list[EventOut])
def events(organization: str | None = None, search: str = '', period: str = Query('all', pattern='^(all|upcoming|past)$'), db: Session = Depends(session_scope)):
    stmt = select(Event).options(selectinload(Event.organization)).join(Organization).where(Event.published.is_(True))
    if organization: stmt = stmt.where(Organization.slug == organization)
    if search: stmt = stmt.where(or_(Event.title.ilike(f'%{search[:80]}%'), Event.venue.ilike(f'%{search[:80]}%'), Organization.name.ilike(f'%{search[:80]}%')))
    now = datetime.now(ZoneInfo('America/Fortaleza'))
    if period == 'upcoming': stmt = stmt.where(Event.start_at >= now)
    if period == 'past': stmt = stmt.where(Event.start_at < now)
    return db.scalars(stmt.order_by(Event.start_at).limit(200)).all()

@router.get('/events/{slug}', response_model=EventOut)
def event_detail(slug: str, db: Session = Depends(session_scope)):
    event = db.scalar(select(Event).options(selectinload(Event.organization)).where(Event.slug==slug, Event.published.is_(True)))
    if not event: raise HTTPException(404, 'Evento não encontrado')
    return event

@router.get('/mcs', response_model=list[MCOut])
def mcs(search: str = '', db: Session = Depends(session_scope)):
    stmt = select(MC).where(MC.published.is_(True))
    if search: stmt = stmt.where(MC.stage_name.ilike(f'%{search[:80]}%'))
    return db.scalars(stmt.order_by(MC.stage_name).limit(200)).all()

@router.get('/mcs/{slug}', response_model=MCOut)
def mc_detail(slug: str, db: Session = Depends(session_scope)):
    mc = db.scalar(select(MC).where(MC.slug==slug, MC.published.is_(True)))
    if not mc: raise HTTPException(404, 'MC não encontrado')
    return mc

@router.get('/auth/status')
def status(request: Request):
    try: admin_guard(request); ok=True
    except HTTPException: ok=False
    return {'configured': enabled(), 'authenticated': ok, 'recovery': enabled() and recovery_enabled()}

@router.post('/auth/login')
def login(credentials: Login, request: Request, response: Response, db: Session = Depends(session_scope)):
    key = request.client.host if request.client else 'unknown'
    now = time.monotonic()
    history = [t for t in _login_attempts.get(key, []) if now-t<900]
    if len(history)>=8: raise HTTPException(429, 'Muitas tentativas; tente novamente mais tarde')
    admin = db.get(RootAdmin, 1)
    if not verify_password(admin, credentials.username, credentials.password):
        history.append(now)
        _login_attempts[key]=history
        raise HTTPException(401, 'Credenciais inválidas')
    _login_attempts.pop(key,None)
    response.set_cookie(COOKIE, issue_token(admin.session_version), httponly=True, secure=get_settings().production, samesite='strict', max_age=8*3600, path='/')
    return {'ok': True}

@router.post('/auth/logout')
def logout(response: Response):
    response.delete_cookie(COOKIE, path='/')
    return {'ok':True}

@router.get('/admin/events', dependencies=[Depends(admin_guard)], response_model=list[EventOut])
def admin_events(db: Session = Depends(session_scope)):
    return db.scalars(select(Event).options(selectinload(Event.organization)).order_by(Event.start_at)).all()

@router.get('/admin/mcs', dependencies=[Depends(admin_guard)], response_model=list[MCOut])
def admin_mcs(db: Session = Depends(session_scope)):
    return db.scalars(select(MC).order_by(MC.stage_name)).all()

@router.post('/admin/organizations', dependencies=[Depends(admin_guard)], response_model=OrgOut, status_code=201)
def create_org(payload: OrgIn, db: Session = Depends(session_scope)):
    if db.scalar(select(Organization).where(Organization.slug==payload.slug)): raise HTTPException(409, 'Organização já existe')
    item = Organization(**payload.model_dump());db.add(item);db.commit();db.refresh(item);return item

@router.post('/admin/events', dependencies=[Depends(admin_guard)], response_model=EventOut, status_code=201)
def create_event(payload: EventIn, db: Session = Depends(session_scope)):
    if db.scalar(select(Event).where(Event.slug==payload.slug)): raise HTTPException(409, 'Evento já existe')
    if not db.get(Organization,payload.organization_id): raise HTTPException(422,'Organização não encontrada')
    item=Event(**payload.model_dump());db.add(item);db.commit()
    return db.scalar(select(Event).options(selectinload(Event.organization)).where(Event.id==item.id))

@router.put('/admin/events/{event_id}', dependencies=[Depends(admin_guard)], response_model=EventOut)
def update_event(event_id: int,payload: EventIn, db: Session = Depends(session_scope)):
    item=db.get(Event,event_id)
    if not item: raise HTTPException(404,'Evento não encontrado')
    if not db.get(Organization,payload.organization_id): raise HTTPException(422,'Organização não encontrada')
    conflict=db.scalar(select(Event).where(Event.slug==payload.slug, Event.id!=event_id))
    if conflict: raise HTTPException(409,'Slug já utilizado')
    for key,val in payload.model_dump().items():setattr(item,key,val)
    db.commit()
    return db.scalar(select(Event).options(selectinload(Event.organization)).where(Event.id==event_id))

@router.post('/admin/mcs', dependencies=[Depends(admin_guard)],response_model=MCOut,status_code=201)
def create_mc(payload: MCIn,db: Session = Depends(session_scope)):
    if db.scalar(select(MC).where(MC.slug==payload.slug)):raise HTTPException(409,'MC já existe')
    item=MC(**payload.model_dump());db.add(item);db.commit();db.refresh(item);return item

@router.put('/admin/mcs/{mc_id}', dependencies=[Depends(admin_guard)],response_model=MCOut)
def update_mc(mc_id:int,payload:MCIn,db:Session=Depends(session_scope)):
    item=db.get(MC,mc_id)
    if not item:raise HTTPException(404,'MC não encontrado')
    other=db.scalar(select(MC).where(MC.slug==payload.slug,MC.id!=mc_id))
    if other:raise HTTPException(409,'Slug já utilizado')
    for key,val in payload.model_dump().items():setattr(item,key,val)
    db.commit();db.refresh(item);return item


@router.post('/auth/reset-request')
def reset_request(payload: ResetRequest, db: Session = Depends(session_scope)):
    if not enabled() or not recovery_enabled():
        raise HTTPException(503, 'Recuperação por e-mail indisponível.')
    admin = db.get(RootAdmin, 1)
    if admin and payload.username.strip().casefold() in (admin.username.casefold(), get_settings().admin_email.casefold()):
        try:
            send_reset(db, admin)
        except (OSError, ValueError):
            logging.getLogger(__name__).warning('Falha no envio de recuperação')
    return {'ok': True}

@router.post('/auth/reset-confirm')
def reset_confirm(payload: ResetConfirm, response: Response, db: Session = Depends(session_scope)):
    if not enabled(): raise HTTPException(503,'Serviço temporariamente indisponível.')
    if not consume_reset(db,payload.token,payload.password): raise HTTPException(400,'Link inválido ou expirado. Solicite outro.')
    response.delete_cookie(COOKIE, path='/')
    return {'ok':True}
