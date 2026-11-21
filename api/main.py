from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from api.database import Base, engine, SessionLocal
from api.seed import seed
from api.routes import router
from api.config import ROOT, get_settings
import api.models  # registers model metadata

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield

app = FastAPI(title='Batalha do Reviver — API',version='1.0.0',lifespan=lifespan, docs_url='/api/docs', redoc_url=None)
if get_settings().allowed_origin:
    app.add_middleware(CORSMiddleware,allow_origins=[get_settings().allowed_origin], allow_credentials=True, allow_methods=['GET','POST','PUT'],allow_headers=['Content-Type'])
@app.middleware('http')
async def security_headers(request: Request, call_next):
    if request.method in ('POST','PUT','PATCH','DELETE'):
        origin = request.headers.get('origin', '')
        expected = str(request.base_url).rstrip('/')
        if origin and origin != expected:
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail': 'Origem não autorizada'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response

app.include_router(router)
web = ROOT/'web'
app.mount('/assets', StaticFiles(directory=str(web/'assets')), name='assets')

@app.get('/favicon.ico',include_in_schema=False)
def favicon():return FileResponse(web/'favicon.png')

@app.get('/{path:path}',include_in_schema=False)
def spa(path: str):
    if path.startswith('api/'):
        from fastapi import HTTPException
        raise HTTPException(404,'Rota não encontrada')
    if path in ('styles.css','app.js','api-client.js','ui.js','admin.js','favicon.png'):
        return FileResponse(web/path)
    return FileResponse(web/'index.html')
