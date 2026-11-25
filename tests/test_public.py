def test_health(client):
    r=client.get('/api/v1/health')
    assert r.status_code==200
    assert r.json()['status']=='ok'

def test_seed_event_and_brand(client):
    r=client.get('/api/v1/events')
    assert r.status_code==200
    events=r.json()
    assert len(events)==1
    assert events[0]['slug']=='reviver-edicao-01'
    assert events[0]['organization']['slug']=='batalha-do-reviver'
    assert events[0]['capacity']==16
    assert client.get('/assets/logo.webp').headers['content-type']=='image/webp'
    assert client.get('/assets/fenix.webp').headers['content-type']=='image/webp'
    assert client.get('/favicon.ico').status_code==200

def test_filters(client):
    assert len(client.get('/api/v1/events?organization=batalha-do-reviver').json())==1
    assert client.get('/api/v1/events?organization=nao-existe').json()==[]
    assert client.get('/api/v1/events?search=Reviver').status_code==200
    assert client.get('/api/v1/events?period=invalid').status_code==422

def test_profiles_are_not_fabricated(client):
    assert client.get('/api/v1/mcs').json()==[]
    assert client.get('/api/v1/mcs/nao-existe').status_code==404

def test_admin_locked_without_secret(client):
    assert client.get('/api/v1/auth/status').json()['configured'] is False
    assert client.post('/api/v1/admin/events',json={}).status_code==503
    assert client.post('/api/v1/auth/login',json={'password':'abc'}).status_code==401

def test_spa_routes(client):
    assert client.get('/').status_code==200
    assert client.get('/agenda').status_code==200
    assert client.get('/api/non-existent').status_code==404

def test_known_organizations_have_no_fabricated_events(client):
    organizations=client.get('/api/v1/organizations').json()
    assert len(organizations)>=7
    assert any(o['slug']=='batalha-do-qi' for o in organizations)
    assert client.get('/api/v1/events?organization=batalha-do-qi').json()==[]
