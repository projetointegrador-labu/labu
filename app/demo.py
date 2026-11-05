"""Dados fictícios para demonstração (não use em produção real).

As imagens são ilustrações locais (static/img/demo) apenas para visualizar o layout.
"""
from werkzeug.security import generate_password_hash

IMG = "/static/img/demo/"

# nome, categoria, bairro, lat, lng, anos, disponibilidade, diária, habilidades, descrição, fotos
DEMO = [
    ("Edson Lima", "Eletricista", "Jardim Ângela", -23.7840, -46.7790, 12, "imediata", 180,
     ["Quadro de distribuição", "Tomadas", "Iluminação", "Chuveiro"],
     "Instalação de quadros de luz, tomadas, fiação e iluminação. Laudo técnico e certificado de instalação.",
     ["eletrica.svg", "ladrilho.svg"]),
    ("Edilson Ribeiro", "Pedreiro", "Capão Redondo", -23.6720, -46.7690, 15, "semana", 150,
     ["Alvenaria", "Reboco", "Contrapiso", "Piso e azulejo", "Laje"],
     "Levanto paredes, faço reboco e contrapiso. Trabalho com reformas de casas e sobrados, sempre com prazo e nível.",
     ["tijolos.svg", "pintura.svg"]),
    ("Carlos Almeida", "Encanador", "Grajaú", -23.7627, -46.6973, 9, "imediata", 170,
     ["Vazamentos", "Caixa d'água", "Esgoto", "Aquecedor"],
     "Reparo de vazamentos, troca de tubulação e instalação de louças e metais.",
     ["ladrilho.svg", "eletrica.svg"]),
    ("Paulo Nascimento", "Pintor", "Guarapiranga", -23.7203, -46.7351, 6, "imediata", 140,
     ["Pintura interna", "Textura", "Massa corrida"],
     "Pintura residencial e comercial com acabamento fino. Orçamento sem compromisso.",
     ["pintura.svg", "tijolos.svg"]),
    ("Ana Lima", "Azulejista / Ladrilheiro", "Casa Blanca", -23.7712, -46.7110, 9, "mes", 200,
     ["Porcelanato", "Revestimento", "Rejunte"],
     "Assentamento de pisos e revestimentos em cozinhas e banheiros.",
     ["ladrilho.svg", "pintura.svg"]),
    ("Rafael Costa", "Carpinteiro", "Vila Atlântica", -23.7890, -46.7220, 11, "imediata", 190,
     ["Telhados", "Forro", "Portas", "Deck"],
     "Estruturas de madeira, portas, janelas e decks.",
     ["tijolos.svg", "ladrilho.svg"]),
    ("Edson Barros", "Mestre de obras", "Tiquatira", -23.5290, -46.5430, 20, "semana", 320,
     ["Gestão de obra", "Orçamento", "Fundação"],
     "Coordeno equipes e prazos em construções e grandes reformas.",
     ["tijolos.svg", "eletrica.svg"]),
]
NOTAS = [5, 5, 5, 4, 5, 4, 5, 5, 4, 5]


def popular_demo(db) -> int:
    cats = {c["nome"]: c["id"] for c in db.consultar("SELECT id, nome FROM categorias")}
    senha = generate_password_hash("Demo12345")

    cont = db.um("SELECT id FROM usuarios WHERE email = %s", ("contratante@demo.labu",))
    cont_id = cont["id"] if cont else db.executar(
        """INSERT INTO usuarios (nome, email, senha_hash, perfil, consentimento_lgpd, consentimento_em)
           VALUES ('Rodolfo Demo', 'contratante@demo.labu', %s, 'contratante', 1, CURRENT_TIMESTAMP)""",
        (senha,))

    criados = 0
    for i, (nome, cat, bairro, lat, lng, anos, disp, diaria, habs, desc, fotos) in enumerate(DEMO, start=1):
        email = f"demo{i}@demo.labu"
        if db.um("SELECT id FROM usuarios WHERE email = %s", (email,)):
            continue
        uid = db.executar(
            """INSERT INTO usuarios (nome, email, senha_hash, telefone, perfil,
                                     consentimento_lgpd, consentimento_em)
               VALUES (%s, %s, %s, %s, 'prestador', 1, CURRENT_TIMESTAMP)""",
            (nome, email, senha, "11999990000"),
        )
        db.executar(
            """INSERT INTO prestadores (usuario_id, categoria_id, descricao, anos_experiencia,
                   disponibilidade, whatsapp, bairro, cidade, estado, latitude, longitude, raio_km, valor_diaria)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'São Paulo', 'SP', %s, %s, 15, %s)""",
            (uid, cats[cat], desc, anos, disp, "11999990000", bairro, lat, lng, diaria),
        )
        for pos, h in enumerate(habs):
            db.executar("INSERT INTO prestador_habilidades (usuario_id, habilidade, posicao) VALUES (%s, %s, %s)",
                        (uid, h, pos))
        for f in fotos:
            db.executar("INSERT INTO prestador_fotos (usuario_id, url) VALUES (%s, %s)", (uid, IMG + f))
        for k in range(3 + i % 4):  # avaliações fictícias para exibir nota
            db.executar(
                """INSERT INTO servicos (prestador_id, contratante_id, categoria_id, descricao, status,
                                         avaliacao, concluido_em)
                   VALUES (%s, %s, %s, 'Serviço fictício de demonstração', 'concluido', %s, CURRENT_TIMESTAMP)""",
                (uid, cont_id, cats[cat], NOTAS[(i + k) % len(NOTAS)]),
            )
        criados += 1
    return criados
