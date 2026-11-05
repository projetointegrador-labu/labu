# LABU — Conectando construtores e prestadores de serviços na construção civil via web

Projeto Integrador II — UNIVESP (2026). Plataforma web com banco de dados MySQL para divulgação e contratação de profissionais da construção civil (pedreiros, eletricistas, encanadores, pintores etc.) com **busca por localização**, **acessibilidade** e **hospedagem em nuvem (Railway)**.

## Funcionalidades
- **Feed de profissionais** (tema escuro com amarelo): filtros por cidade/função/habilidade, localização ("Usar minha localização"), disponibilidade, distância máxima, função (chips), diária máxima (slider) e avaliação mínima; ordenação por proximidade, avaliação ou menor diária.
- **Cartões** com habilidades, fotos de trabalhos, nota média, nº de serviços avaliados, diária e botões **Salvar** (favoritos) e **Chamar pelo site**.
- Cadastro/login de **contratantes** e **prestadores**; superusuário (admin).
- Perfil profissional com especialidade, experiência, disponibilidade, área de atuação e localização (GPS, CEP via ViaCEP ou Google Maps).
- Busca por especialidade, bairro, cidade, estado e **"perto de mim"** (raio em km, ordenada por distância).
- Solicitação de serviços, fluxo de status (solicitado → aceito → concluído), **histórico** e **avaliações**.
- Painel administrativo: usuários, **relatórios** (por categoria, cidade, status, mês) e exportação CSV.
- **Acessibilidade** (WCAG 2.1 AA): navegação por teclado, link "pular", alto contraste, ajuste de fonte, redução de animações, leitores de tela, **VLibras**.
- **LGPD**: consentimento, política de privacidade, exclusão de conta, contato visível só a logados.
- Segurança: hash de senha, CSRF, limite de tentativas de login, cookies seguros, SQL parametrizado.

## Stack
Python 3.12 · Flask · MySQL 8 (PyMySQL) · JavaScript (vanilla) · Google Maps API (opcional) · Gunicorn · Railway

## Estrutura
```
labu/
├── app/
│   ├── __init__.py          # fábrica da app + comandos CLI (init-db, create-superuser, seed-demo)
│   ├── config.py            # variáveis de ambiente (compatível com Railway)
│   ├── db.py · seed.py · demo.py
│   ├── security.py          # sessão, CSRF, perfis, anti-open-redirect
│   ├── busca.py · geo.py    # busca e geolocalização (Haversine)
│   ├── validators.py
│   ├── blueprints/          # main, auth, prestador, servicos, favoritos, admin, api
│   ├── templates/           # Jinja2 acessíveis
│   └── static/{css,js,img}/ # style.css, acessibilidade.js, busca.js, mapa.js, perfil.js, formularios.js
├── database/schema.sql      # esquema MySQL
├── tests/                   # pytest
├── docs/                    # DEPLOY_RAILWAY.md, ARQUITETURA.md
├── .github/workflows/ci.yml # testes + integração com MySQL
├── railway.json · Procfile · requirements*.txt · .python-version
├── .env.example · .gitignore · LICENSE
└── wsgi.py
```

## Rodando localmente
```bash
git clone https://github.com/SEU_USUARIO/labu.git && cd labu
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                   # edite os valores

flask --app wsgi init-db        # cria tabelas, categorias e superusuário (ADMIN_*)
flask --app wsgi seed-demo      # (opcional) prestadores fictícios com fotos/avaliações — senha Demo12345
                                # contratante de teste: contratante@demo.labu / Demo12345
flask --app wsgi run --debug    # http://127.0.0.1:5000
```
Sem `MYSQL_URL` e fora de produção, o app usa SQLite (`labu_dev.db`) para facilitar o desenvolvimento. Para usar MySQL local, defina `MYSQL_URL=mysql://usuario:senha@localhost:3306/labu` (crie antes o banco: `CREATE DATABASE labu CHARACTER SET utf8mb4;`).

## Testes
```bash
python -m pytest -q
```

## Deploy no Railway
Veja **[docs/DEPLOY_RAILWAY.md](docs/DEPLOY_RAILWAY.md)**. Resumo: conectar o repositório, adicionar o plugin MySQL, definir `SECRET_KEY`, `MYSQL_URL=${{MySQL.MYSQL_URL}}`, `ADMIN_EMAIL` e `ADMIN_PASSWORD`, e gerar o domínio.

## Equipe
Antonio Flaviano da Silva Nobre · Christian Ferreira de Oliveira · Diana Ribeiro da Silva · Diego Lopes do Amparo · Emerson Evandro de Melo · Jhonata Moreira da Costa · Luana Cardoso da Silva · Paulo Ricardo Ferreira Lima — Tutor: Lucas Fattori de Moraes.

Licença: MIT.
