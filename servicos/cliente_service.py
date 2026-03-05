"""
cliente_service.py
Serviços de Cliente (Multiempresa)
"""

# Importamos a conexão central blindada, não precisamos mais do sqlite3 aqui!
from core.database import conectar

# ==========================================================
# CRIAR TABELA
# ==========================================================

def criar_tabela_clientes():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            obra TEXT,
            cidade TEXT,
            servico TEXT,
            os TEXT,               
            especificacao TEXT,    
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        )
    """)

    conn.commit()
    conn.close()


# ==========================================================
# INSERIR CLIENTE
# ==========================================================

def inserir_cliente(empresa_id, nome, obra, cidade, servico, os, especificacao):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO clientes (empresa_id, nome, obra, cidade, servico, os, especificacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (empresa_id, nome, obra, cidade, servico, os, especificacao))

    conn.commit()
    conn.close()


# ==========================================================
# ATUALIZAR (EDITAR) CLIENTE
# ==========================================================

def atualizar_cliente(cliente_id, nome, obra, cidade, servico, os, especificacao):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE clientes
        SET nome = ?, obra = ?, cidade = ?, servico = ?, os = ?, especificacao = ?
        WHERE id = ?
    """, (nome, obra, cidade, servico, os, especificacao, cliente_id))

    conn.commit()
    conn.close()


# ==========================================================
# LISTAR CLIENTES DA EMPRESA ATIVA (DECRESCENTE)
# ==========================================================

def listar_clientes(empresa_id):
    conn = conectar()
    cursor = conn.cursor()

    # ORDER BY id DESC para mostrar o mais recente primeiro
    cursor.execute("""
        SELECT id, nome, obra, cidade, servico, os, especificacao
        FROM clientes
        WHERE empresa_id = ?
        ORDER BY id DESC
    """, (empresa_id,))

    dados = cursor.fetchall()

    conn.close()
    return dados


# ==========================================================
# BUSCAR CLIENTES (NOME OU CIDADE) (DECRESCENTE)
# ==========================================================

def buscar_clientes(empresa_id, filtro):
    conn = conectar()
    cursor = conn.cursor()

    # ORDER BY id DESC para manter a ordem decrescente mesmo ao pesquisar
    cursor.execute("""
        SELECT id, nome, obra, cidade, servico, os, especificacao
        FROM clientes
        WHERE empresa_id = ?
        AND (nome LIKE ? OR cidade LIKE ?)
        ORDER BY id DESC
    """, (empresa_id, f"%{filtro}%", f"%{filtro}%"))

    dados = cursor.fetchall()

    conn.close()
    return dados


# ==========================================================
# EXCLUIR CLIENTE
# ==========================================================

def excluir_cliente(cliente_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM clientes
        WHERE id = ?
    """, (cliente_id,))

    conn.commit()
    conn.close()