# Batalha do Reviver — Portal Cultural

Site e sistema de gestão da **Batalha do Reviver**, em São Luís/MA.

## Tecnologias e arquitetura

- **Frontend:** HTML5, CSS responsivo e JavaScript ES modules (SPA), separados em `app.js` (roteamento/views), `api-client.js` (acesso HTTP), `ui.js` (componentes) e `admin.js` (painel).
- **Backend:** FastAPI com rotas versionadas, Pydantic, SQLAlchemy, autenticação Argon2 + cookie HTTP-only.
- **Banco:** SQLite local para desenvolvimento; PostgreSQL recomendado em produção por `DATABASE_URL`.
- **Hospedagem:** API e site sob o mesmo domínio em Railway ou contêiner compatível; `Dockerfile` e `railway.json` incluídos.
- **Testes:** pytest e GitHub Actions.
- **Identidade:** logo e fênix extraídas do kit de marca oficial, **não geradas novamente por IA**.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn api.main:app --reload --port 8000 --env-file .env
```

Copie `.env.example` para `.env` para configurar o ambiente local. No VS Code, selecione **Tasks: Run Task → Reviver: iniciar portal** para usar o Python de `.venv`. Abra `http://localhost:8000`. API em `/api/docs` e verificação em `/api/v1/health`.

### Configurar o painel

Use `scripts/hash_password.py` para gerar o hash da senha inicial (mínimo 12 caracteres). Defina `ADMIN_PASSWORD_HASH`, `ADMIN_USERNAME` e `SESSION_SECRET` no `.env` local ou nas variáveis protegidas da hospedagem. A chave da sessão precisa de no mínimo 32 caracteres. Em produção, configure também `APP_ENV=production` e PostgreSQL via `DATABASE_URL` (ou `POSTGRES_URL` na Vercel). O hash inicial é usado uma vez. A recuperação de senha atualiza o banco. Para ativar a recuperação por e-mail, configure no serviço da API `PUBLIC_BASE_URL` com o domínio HTTPS oficial, `ADMIN_EMAIL`, `RESEND_API_KEY` e `RESEND_FROM` com um remetente verificado. As variáveis `SMTP_*` de `.env.example` permanecem disponíveis para instalações com SMTP.

```bash
python scripts/hash_password.py
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Painel: `/admin`. A edição dos registros exige login e salva no banco. Somente conteúdo `published=true` aparece para o público. Não há senha inicial ou cadastro automático inseguro. Para maior proteção em escala, use rate limit compartilhado por Redis/proxy e CSRF token dedicado em implantação com múltiplos domínios.

## Conteúdo inicial

Apenas **Batalha do Reviver — Edição 01**, confirmada para **02/12/2026 às 19h na Praça Odylo Costa Filho, São Luís/MA**, com **16 vagas**, **entrada gratuita**, **R$ 100** para campeão e **R$ 50** para vice. Nenhum MC, resultado, ranking ou edição externa fictícios são criados.

## Deploy

Em produção, a Vercel serve as páginas públicas e encaminha `/api/v1/` ao serviço `reviver-api` no Railway. O projeto Railway da Batalha do Reviver contém o PostgreSQL e as variáveis da API. Cadastros e acessos administrativos ficam nesse banco.

Railway: conectar o repositório, definir `DATABASE_URL` apontando para PostgreSQL permanente e `APP_ENV=production`; adicionar `ADMIN_PASSWORD_HASH` e `SESSION_SECRET` na área de variáveis do serviço; o `Dockerfile` está disponível. Não usar SQLite em disco efêmero em produção. Rodar migrações controladas antes de deploys que modifiquem o esquema; o setup atual `create_all` é apenas bootstrap inicial e não migra esquema existente.

## Rotas API

`GET /api/v1/health`, `/organizations`, `/events`, `/events/{slug}`, `/mcs`, `/mcs/{slug}`. Autenticação: `GET /auth/status`, `POST /auth/login`, `POST /auth/logout`. Gestão: `POST /admin/organizations`, `GET/POST/PUT /admin/events`, `GET/POST/PUT /admin/mcs` (prefixo `/api/v1`).

## Cuidados editoriais

Use apenas fotos de pessoas com autorização e direitos de uso. Fotos de batalha nas capas do primeiro layout são imagens ilustrativas da proposta visual, não documentação da primeira edição. Toda programação de terceiros deve ser confirmada antes de publicação.
