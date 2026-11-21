# Arquitetura — Batalha do Reviver

## Organização

```text
batalha-do-reviver/
├─ api/
│  ├─ main.py       # app ASGI, ciclo de vida, roteamento SPA e arquivos
│  ├─ routes.py     # rotas versionadas, públicas e administrativas
│  ├─ models.py     # entidades persistidas e relacionamentos
│  ├─ schemas.py    # contratos de entrada/saída, sanitização de campos
│  ├─ database.py   # engine e conexão SQLAlchemy
│  ├─ seed.py       # primeira edição confirmada, idempotente
│  ├─ config.py     # configuração e ambiente
│  └─ security.py   # senha Argon2, sessão HTTP-only, verificação
├─ web/
│  ├─ index.html    # documento semântico e navegação
│  ├─ styles.css    # design system escuro + layout responsivo
│  ├─ app.js        # SPA, páginas, navegação e ações
│  ├─ api-client.js # único client de requests HTTP
│  ├─ ui.js         # componentes e escape de HTML
│  ├─ admin.js      # UI administrativa
│  ├─ favicon.png   # fênix isolada oficial
│  └─ assets/       # logo oficial e imagens ilustrativas
├─ tests/           # testes de comportamento da API
├─ scripts/         # ferramentas administrativas locais
├─ .github/workflows/ci.yml
├─ Dockerfile
├─ railway.json
└─ requirements.txt
```

## Fluxo de dados

```text
Navegador (páginas e formulário)
       │  GET/POST/PUT JSON sobre HTTPS
       ▼
FastAPI /api/v1
       │  validação Pydantic + autenticação para escrita
       ▼
SQLAlchemy ──→ PostgreSQL em produção / SQLite local
```

Os arquivos estáticos são atendidos pela própria aplicação FastAPI no ambiente de demonstração e no Docker, evitando CORS na configuração padrão. Se o frontend for hospedado em outro domínio, habilitar CORS estritamente para a origem específica, revisar cookie cross-site e CSRF; não usar `*` com credenciais.

## Regras editoriais

- Evento, MC ou resultado não são considerados publicados por estarem cadastrados: campo `published` controla a exibição pública.
- Apenas a estreia de 02/12/2026 é pré-cadastrada por haver informação confirmada.
- Organizações de outras batalhas podem ser registradas; datas externas são incluídas pela administração após validação.
- Imagens de referências visuais não podem ser tratadas como fotografias documentais de uma edição que ainda não aconteceu.
- Ranking e resultados não são calculados a partir de dados inventados.

## Segurança

- Autenticação administrativa desabilitada até configuração explícita de senha Argon2 e chave de sessão, sem credenciais padrão.
- Sessões HMAC com prazo de 8 horas, cookie HTTP-only, `SameSite=Strict` e `Secure` em produção.
- Escrita administrativa é condicionada à autenticação; login tem limite simples de tentativas por IP (para produção distribuída, mover a contagem para armazenamento compartilhado).
- Strings do banco são escapadas no HTML. URLs de imagem são limitadas a HTTPS ou ao diretório local de assets.
- `DATABASE_URL`, senha e chave de sessão devem ficar em variáveis protegidas da plataforma, nunca em Git.

## Crescimento

Versão seguinte com migrações Alembic versionadas, armazenamento de mídia autorizado, gravações/vídeos e tabelas de confrontos e resultados validados; índices e filtros adicionais conforme volume real de agenda. Para múltiplas organizações independentes, implantar RBAC, revisão de submissões e trilha de auditoria.
