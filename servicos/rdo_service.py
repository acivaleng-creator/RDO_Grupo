"""
servicos/rdo_service.py

RDO vinculado ao cliente.
Número gerado automaticamente por cliente.
"""

from core.database import conectar


def criar_tabela_rdo():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rdos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            data TEXT,
            descricao TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    conn.commit()
    conn.close()


# ==========================================================
# GERAR PRÓXIMO NÚMERO
# ==========================================================

def gerar_proximo_numero(cliente_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(numero) FROM rdos
        WHERE cliente_id = ?
    """, (cliente_id,))

    resultado = cursor.fetchone()[0]
    conn.close()

    return 1 if resultado is None else resultado + 1


# ==========================================================
# INSERIR RDO
# ==========================================================

def inserir_rdo(cliente_id, data, descricao):
    numero = gerar_proximo_numero(cliente_id)

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO rdos (cliente_id, numero, data, descricao)
        VALUES (?, ?, ?, ?)
    """, (cliente_id, numero, data, descricao))

    conn.commit()
    conn.close()