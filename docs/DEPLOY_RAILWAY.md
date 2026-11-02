# Deploy no Railway (passo a passo)

O repositório já contém `railway.json`, `Procfile`, `requirements.txt` e `.python-version`. O Railway detecta Python automaticamente.

## 1. Subir o código para o GitHub
```bash
git remote add origin https://github.com/SEU_USUARIO/labu.git
git push -u origin main
```

## 2. Criar o projeto no Railway
1. Acesse https://railway.com → **New Project** → **Deploy from GitHub repo** → escolha `labu`.
2. No mesmo projeto: **+ New** → **Database** → **Add MySQL**.

## 3. Variáveis de ambiente do serviço web (aba *Variables*)
| Variável | Valor |
|---|---|
| `SECRET_KEY` | resultado de `python -c "import secrets; print(secrets.token_hex(32))"` |
| `MYSQL_URL` | `${{MySQL.MYSQL_URL}}` (referência ao serviço MySQL; ajuste o nome do serviço se for diferente) |
| `ADMIN_EMAIL` | e-mail do superusuário |
| `ADMIN_PASSWORD` | senha forte do superusuário |
| `ADMIN_NOME` | (opcional) nome exibido |
| `GOOGLE_MAPS_API_KEY` | (opcional) chave do Google Maps — veja abaixo |
| `VLIBRAS_ENABLED` | `true` (padrão) ou `false` |

`RAILWAY_ENVIRONMENT` já é definida pelo Railway e ativa o modo produção (cookies seguros e exigência de `SECRET_KEY` + MySQL).

## 4. Gerar domínio público
Serviço web → **Settings → Networking → Generate Domain**.

## 5. O que acontece a cada deploy
1. **Pre-deploy** (`railway.json`): `flask --app wsgi init-db` cria as tabelas (se não existirem), as categorias e o superusuário (se `ADMIN_EMAIL`/`ADMIN_PASSWORD` estiverem definidos). É idempotente.
2. **Start**: `gunicorn wsgi:app`.
3. **Healthcheck**: `GET /health` (retorna 200 se o banco responde).

## 6. Google Maps (opcional)
1. No Google Cloud Console, ative **Maps JavaScript API** e **Geocoding API**.
2. Crie uma chave e restrinja por *HTTP referrers* ao seu domínio do Railway.
3. Cole em `GOOGLE_MAPS_API_KEY`. Sem a chave, o sistema continua funcionando (busca por GPS/texto e lista); apenas o mapa e a geocodificação por endereço ficam desativados.

## 7. Dados de demonstração (opcional)
No Railway CLI: `railway run flask --app wsgi seed-demo` (cria 7 prestadores fictícios, senha `Demo12345`). **Não use em produção real.**

## Problemas comuns
- **"Produção exige MySQL"**: `MYSQL_URL` não está definida no serviço web.
- **Erro de conexão**: use a URL interna (`mysql.railway.internal`), disponível apenas dentro do projeto Railway.
- **Cookie de sessão não persiste**: acesse via HTTPS (domínio do Railway).
