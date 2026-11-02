"""Dados ficticios"""
from werkzeug.security import generate_password_hash

DEMO = [
    ("Carlos Almeida", "Pedreiro", "Grajaú", -23.7627, -46.6973, 12, "imediata"),
    ("Marcos Souza", "Eletricista", "Interlagos", -23.6812, -46.6783, 8, "semana"),
    ("José Ribeiro", "Encanador", "Parque São Carlos", -23.7421, -46.7502, 15, "imediata"),
    ("Paulo Nascimento", "Pintor", "Guarapiranga", -23.7203, -46.7351, 6, "imediata"),
    ("Ana Lima", "Azulejista / Ladrilheiro", "Casa Blanca", -23.7712, -46.7110, 9, "mes"),
    ("Rafael Costa", "Carpinteiro", "Vila Atlântica", -23.7890, -46.7220, 11, "imediata"),
    ("Edson Barros", "Mestre de obras", "Tiquatira", -23.5290, -46.5430, 20, "semana"),
]


def popular_demo(db) -> int:
    cats = {c["nome"]: c["id"] for c in db.consultar("SELECT id, nome FROM categorias")}
    criados = 0
    senha = generate_password_hash("Demo12345")
    for i, (nome, cat, bairro, lat, lng, anos, disp) in enumerate(DEMO, start=1):
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
                   disponibilidade, whatsapp, bairro, cidade, estado, latitude, longitude, raio_km)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'São Paulo', 'SP', %s, %s, 15)""",
            (uid, cats[cat], f"Profissional com {anos} anos de experiência. Perfil fictício de demonstração.",
             anos, disp, "11999990000", bairro, lat, lng),
        )
        criados += 1
    return criados
