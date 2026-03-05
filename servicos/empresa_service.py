"""
empresa_service.py
Serviços de Empresa (Multiempresa)
"""

import sqlite3
import os
# IMPORTANDO A BLINDAGEM DO NOSSO ARQUIVO DE CONFIGURAÇÃO
from config import DIRETORIO_RAIZ

# ==========================================================
# CONEXÃO
# ==========================================================

def conectar():
    # Centralizamos a conexão aqui. 
    # AGORA BLINDADO: O banco de dados será criado e lido na pasta segura do usuário!
    caminho_banco = os.path.join(DIRETORIO_RAIZ, "database.db")
    return sqlite3.connect(caminho_banco)


# ==========================================================
# CRIAR TABELA
# ==========================================================

def criar_tabela_empresa():

    conn = conectar()
    cursor = conn.cursor()

    # Adicionado "UNIQUE" na coluna "nome" para evitar duplicidade direto no banco
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            logo TEXT
        )
    """)

    conn.commit()
    conn.close()


# ==========================================================
# INSERIR EMPRESA
# ==========================================================

def inserir_empresa(nome):

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO empresas (nome)
            VALUES (?)
        """, (nome,))
        conn.commit()
    except sqlite3.IntegrityError:
        # Se por algum motivo o sistema tentar inserir um nome repetido,
        # o banco de dados vai bloquear silenciosamente, sem quebrar o app.
        pass
    finally:
        conn.close()


# ==========================================================
# LISTAR EMPRESAS
# ==========================================================

def listar_empresas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, logo
        FROM empresas
        ORDER BY nome
    """)

    dados = cursor.fetchall()

    conn.close()
    return dados


# ==========================================================
# OBTER EMPRESA POR ID
# ==========================================================

def obter_empresa_por_id(id_empresa):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, nome, logo FROM empresas WHERE id = ?",
        (id_empresa,)
    )

    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        return {
            "id": resultado[0],
            "nome": resultado[1],
            "logo": resultado[2]
        }

    return None


# ==========================================================
# ATUALIZAR LOGO
# ==========================================================

def atualizar_logo(empresa_id, nome_logo):
    conn = conectar() # ou como estiver a sua conexão
    cursor = conn.cursor()
    
    # A CORREÇÃO MÁGICA ESTÁ AQUI NO FINAL DA LINHA (WHERE id = ?):
    cursor.execute("UPDATE empresas SET logo = ? WHERE id = ?", (nome_logo, empresa_id))
    
    conn.commit()
    conn.close()


# ==========================================================
# EXCLUIR EMPRESA
# ==========================================================

def excluir_empresa(empresa_id):
    # Agora usa a função conectar() padrão. Nada de importar sqlite3 de novo!
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM empresas WHERE id = ?", (empresa_id,))
    
    conn.commit()
    conn.close()