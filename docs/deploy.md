# Publicação — checklist de produção

O projeto foi validado localmente, mas **não tem implantação pública concluída** enquanto um repositório GitHub com acesso à hospedagem e um PostgreSQL persistente não estiverem provisionados.

## 1. Repositório GitHub

1. Criar um repositório vazio chamado `batalha-do-reviver` na conta desejada.
2. Subir todo o conteúdo da pasta do projeto com branch `main`.
3. Conceder permissão ao app GitHub integrado, se usar implantação conectada.

Se o diretório já tiver um histórico git:

```bash
git remote add origin https://github.com/SEU_USUARIO/batalha-do-reviver.git
git push -u origin main
```

A autenticação do Git deve ser feita no GitHub, sem compartilhar tokens no chat ou em arquivos versionados.

## 2. Banco e serviço de API

1. Criar um projeto Railway isolado para o Reviver.
2. Adicionar PostgreSQL persistente (sem SQLite efêmero).
3. Criar serviço a partir do repositório GitHub e habilitar deploy da branch `main`.
4. Definir variáveis de produção `APP_ENV=production`, `DATABASE_URL` a partir da referência interna ao banco Railway, `ADMIN_PASSWORD_HASH` e `SESSION_SECRET` (segredos devem ser inseridos na área protegida da plataforma).
5. Verificar `/api/v1/health`, abrir `/` e `/agenda`, autenticar em `/admin`.
6. Configurar domínio, HTTPS, backups e monitoramento de erros, e testar navegação mobile.

## 3. Antes de divulgar

- Validar domínio final e HTTPS.
- Confirmar que o painel só funciona após login.
- Abrir todas as imagens oficiais no computador e celular.
- Validar nome, data e endereço da estreia.
- Só cadastrar eventos de terceiros depois de confirmação dos organizadores.
- Solicitar permissão para uso de fotos de MCs e de terceiros.
- Configurar backup e restauração do PostgreSQL.
- Documentar e aplicar migrações de banco antes de alterações futuras de schema.

## Vercel standalone preview

A standalone deploy can expose the public read-only website via the root-level
`app.py` ASGI entrypoint. With no `DATABASE_URL` Vercel stores the seeded snapshot
in `/tmp/reviver.db`, which is **ephemeral and unsuitable for administration**;
keep `ADMIN_PASSWORD_HASH` and `SESSION_SECRET` unset in this mode.
To enable persistent publishing, provision managed PostgreSQL and configure its
connection string in Vercel's protected environment variables, then redeploy.
Use managed migrations, backups and a sufficiently strong administrator secret.
