from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select
from sqlalchemy.orm import Session
from api.models import Organization, Event

# Organizações verificadas no mapa do Duelo Nacional e em perfis públicos.
# Cadastro de uma organização NÃO implica que exista edição confirmada.
KNOWN_ORGANIZATIONS = (
    ('batalha-do-reviver','Batalha do Reviver','', 'Movimento de cultura, arte e freestyle no Centro Histórico de São Luís.'),
    ('batalha-do-qi','Batalha do QI','batalhado_qi', 'Batalha de rima de São Luís.'),
    ('batalha-da-cohab','Batalha da Cohab','batalhadacohab_', 'Batalha de rima de São Luís.'),
    ('batalha-na-praca','Batalha na Praça','batalhanapraca', 'Batalha de rima de São Luís.'),
    ('batalha-do-participa','Batalha do Participa','batalha_do_participa_', 'Batalha de rima de São Luís.'),
    ('batalha-da-liberdade','Batalha da Liberdade','batalhadalb', 'Batalha de rima de São Luís.'),
    ('batalha-da-vp','Batalha da VP','batalhada.vp', 'Batalha de rima de São Luís.'),
)

def seed(db: Session):
    existing = {o.slug:o for o in db.scalars(select(Organization).where(Organization.slug.in_([o[0] for o in KNOWN_ORGANIZATIONS])))}
    for slug,name,instagram,description in KNOWN_ORGANIZATIONS:
        if slug not in existing:
            org=Organization(slug=slug,name=name,instagram=instagram,description=description)
            db.add(org);db.flush();existing[slug]=org
    if not db.scalar(select(Event).where(Event.slug == 'reviver-edicao-01')):
        db.add(Event(slug='reviver-edicao-01', organization_id=existing['batalha-do-reviver'].id,
                     title='Batalha do Reviver — 1ª edição',
                     start_at=datetime(2026,12,2,19,0,tzinfo=ZoneInfo('America/Fortaleza')),
                     venue='Praça Odylo Costa Filho — Centro Histórico', city='São Luís', state='MA',
                     description='Estreia da Batalha do Reviver: 16 vagas para MCs, inscrições no local, entrada gratuita.',
                     capacity=16, champion_prize=100, runner_up_prize=50, registration='Inscrições no local',
                     free=True, published=True, cover_url='/assets/hero.jpg'))
    db.commit()
