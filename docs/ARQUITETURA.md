# Arquitetura

```
Navegador (HTML + CSS + JavaScript)
   │  geolocalização (GPS), ViaCEP, Google Maps JS, VLibras
   ▼
Flask (Python) ── blueprints: main · auth · prestador · servicos · admin · api
   │  SQL parametrizado (PyMySQL)
   ▼
MySQL 8 (Railway)
```

## Mapeamento com o relatório do Projeto Integrador II
| Item do relatório | Onde está |
|---|---|
| Cadastro de prestadores e contratantes (CRUD) | `app/blueprints/auth.py`, `prestador.py` |
| Autenticação por superusuário | perfil `admin` (`flask create-superuser` / `init-db` com `ADMIN_*`) |
| Histórico dos serviços prestados | `app/blueprints/servicos.py`, tabela `servicos` |
| Geração de relatórios / análise de dados | `app/blueprints/admin.py` (`/admin/relatorios`, exportação CSV) |
| Busca por bairro, cidade, estado e proximidade | `app/busca.py`, `app/geo.py` (Haversine + caixa delimitadora) |
| Geolocalização (Google Maps API) | `static/js/mapa.js`, `static/js/perfil.js`, `static/js/busca.js` |
| Acessibilidade | `static/js/acessibilidade.js`, `static/css/style.css`, `templates/_campos.html`, VLibras |
| LGPD | consentimento no cadastro, `templates/privacidade.html`, exclusão de conta, contato só para logados |
| Hospedagem em nuvem | `railway.json`, `Procfile`, `docs/DEPLOY_RAILWAY.md` |
| Controle de versão no GitHub + testes | `.github/workflows/ci.yml`, `tests/` |

## Modelo de dados
`usuarios` (perfil: contratante | prestador | admin) · `categorias` · `prestadores` (1:1 com usuário prestador; localização lat/lng) · `servicos` (prestador × contratante, status e avaliação). Script completo em `database/schema.sql`.

## Fora do escopo (conforme delimitação do relatório)
Pagamentos dentro da plataforma e aplicativos móveis nativos.
