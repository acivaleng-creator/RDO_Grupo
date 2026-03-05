"""
core/database.py
Gerenciador Central de Conexão com o Banco de Dados
"""

import sqlite3
import os
# IMPORTANDO A BLINDAGEM DO NOSSO ARQUIVO DE CONFIGURAÇÃO
from config import DIRETORIO_RAIZ

def conectar():
    """
    Cria ou conecta ao banco de dados na pasta segura do usuário.
    Garante que o Executável e o Celular tenham permissão de gravação.
    """
    caminho_banco = os.path.join(DIRETORIO_RAIZ, "database.db")
    return sqlite3.connect(caminho_banco)