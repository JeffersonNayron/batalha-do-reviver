from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from api.database import Base, engine, SessionLocal
from api.seed import seed
from api.accounts import seed_admin
from api.routes import router
from api.config import ROOT, get_settings
import api.models  # registers model metadata

@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.begin() as connection:
        if connection.dialect.name == 'postgresql':
            connection.execute(text('SELECT pg_advisory_xact_lock(827641907)'))
        elif connection.dialect.name == 'sqlite':
            connection.exec_driver_sql('BEGIN IMMEDIATE')
        Base.metadata.create_all(connection)
        with SessionLocal(bind=connection) as db:
            seed(db)
            seed_admin(db)
    yield

app = FastAPI(title='Batalha do Reviver — API',version='1.0.0',lifespan=lifespan, docs_url='/api/docs', redoc_url=None)
if get_settings().allowed_origin:
    app.add_middleware(CORSMiddleware,allow_origins=[get_settings().allowed_origin], allow_credentials=True, allow_methods=['GET','POST','PUT'],allow_headers=['Content-Type'])
@app.middleware('http')
async def security_headers(request: Request, call_next):
    settings = get_settings()
    if request.method in ('POST','PUT','PATCH','DELETE'):
        origin = request.headers.get('origin', '')
        allowed = {str(request.base_url).rstrip('/'), settings.public_base_url,
                   settings.allowed_origin}
        if origin and origin not in allowed:
            return JSONResponse({'detail': 'Origem não autorizada'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    is_admin = request.url.path == '/admin' or request.url.path.startswith(('/api/v1/auth/', '/api/v1/admin/'))
    response.headers['Referrer-Policy'] = 'no-referrer' if is_admin else 'strict-origin-when-cross-origin'
    if is_admin:
        response.headers['Cache-Control'] = 'no-store'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response

app.include_router(router)
web = ROOT/'web'
app.mount('/assets', StaticFiles(directory=str(web/'assets')), name='assets')

@app.get('/favicon.ico',include_in_schema=False)
def favicon():return FileResponse(web/'favicon.svg')

@app.get('/{path:path}',include_in_schema=False)
def spa(path: str):
    if path.startswith('api/'):
        from fastapi import HTTPException
        raise HTTPException(404,'Rota não encontrada')
    if path in ('styles.css','app.js','api-client.js','ui.js','admin.js','favicon.svg'):
        return FileResponse(web/path)
    return FileResponse(web/'index.html')
