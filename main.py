"""
base.py

Arquivo principal do Sistema RDO Multiempresa
"""

# Importe a variável blindada lá no topo do seu base.py
from config import PASTA_ATIVOS

import flet as ft
import os
import shutil
from pathlib import Path
import flet as ft

def exportar_logos_para_galeria(page: ft.Page):
    try:
        # Busca a Galeria do Android de forma segura
        caminho_base = Path("/storage/emulated/0/Pictures")
        if not caminho_base.exists():
            caminho_base = Path("/storage/emulated/0/Download")
        
        pasta_destino = caminho_base / "Logos_RDO"
        pasta_destino.mkdir(parents=True, exist_ok=True)

        logos = [
            "logo1.png", "logo2.png", "logo3.png", "logo4.png", 
            "logo5.png", "logo6.png", "logo7.png", "logo8.png"
        ] 

        copiados = 0
        for nome_logo in logos:
            destino_arquivo = pasta_destino / nome_logo
            origem_arquivo = Path("assets") / nome_logo # Volta a usar o caminho simples e seguro
            
            if origem_arquivo.exists() and not destino_arquivo.exists():
                shutil.copy(origem_arquivo, destino_arquivo)
                copiados += 1
        
        # Só exibe aviso SE a página já estiver carregada e copiou algo
        if copiados > 0:
            page.snack_bar = ft.SnackBar(ft.Text(f"Sucesso! {copiados} logos na Galeria.", color=ft.colors.WHITE), bgcolor=ft.colors.GREEN_700)
            page.snack_bar.open = True
            page.update()

    except Exception as e:
        # Mostra o erro sem travar a tela
        page.snack_bar = ft.SnackBar(ft.Text(f"Erro Galeria: {e}", color=ft.colors.WHITE), bgcolor=ft.colors.RED_900, duration=5000)
        page.snack_bar.open = True
        page.update()


# ==========================================================
# 2. AQUI COMEÇA O CORAÇÃO DO SEU APLICATIVO
# ==========================================================
def main(page: ft.Page):
    page.title = "RDO Grupo"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # ... todo o código gigante do seu aplicativo que monta as telas ...
    # ... page.add(...) ...
    # ... page.update() ...

    # -----> A CHAMADA VEM AQUI, NO FINAL DE TUDO! <-----
    exportar_logos_para_galeria(page)

# ==========================================================
# SERVIÇOS
# ==========================================================

from servicos.empresa_service import (
    criar_tabela_empresa,
    listar_empresas,
    inserir_empresa,
)

from servicos.cliente_service import criar_tabela_clientes
from servicos.rdo_service import criar_tabela_rdo

# ==========================================================
# VIEWS
# ==========================================================

from visualizacoes.home_view import construir_home
from visualizacoes.rdo_view import construir_rdo
from visualizacoes.inicial_view import construir_tela_inicial


# ==========================================================
# FUNÇÃO PRINCIPAL
# ==========================================================

def main(page: ft.Page):
    # Pedir permissão de armazenamento em tempo de execução
        # O Flet gerencia isso através do FilePicker ou permissões de plataforma
        # Para garantir a escrita na Galeria, rodamos a exportação

    
    # ... resto do seu código ...

    # ======================================================
    # CONFIGURAÇÃO DA JANELA
    # ======================================================

    page.title = "Sistema RDO Multiempresa"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = 1100
    page.window.height = 800
    page.padding = 0

    # ======================================================
    # CRIAR TABELAS
    # ======================================================

    criar_tabela_empresa()
    criar_tabela_clientes()
    criar_tabela_rdo()

    # ======================================================
    # GARANTIR QUE EXISTE PELO MENOS UMA EMPRESA
    # ======================================================

    empresas = listar_empresas()

    if not empresas:
        inserir_empresa("Empresa Padrão")
        empresas = listar_empresas()

    # ======================================================
    # EMPRESA ATIVA (INICIA COMO NONE PARA FORÇAR TELA INICIAL)
    # ======================================================

    page.empresa_ativa_id = None

    # ======================================================
    # CONTROLE DE ROTAS
    # ======================================================

    def route_change(e):
        # 1. EXTERMINADOR DE TELA CINZA GLOBAL
        if page.dialog:
            page.dialog.open = False
            page.update()

        # 2. Ignora a rota de limpeza de cache
        if page.route == "/_limpar_tela":
            return

        page.views.clear()

        # ==================================================
        # ROTA HOME E TELA INICIAL
        # ==================================================
        if page.route == "/":
            # Escolhe qual função chamar
            if page.empresa_ativa_id is None:
                controle_da_tela = construir_tela_inicial(page)
            else:
                controle_da_tela = construir_home(page)
                
            # Verifica se a função retornou algo antes de adicionar
            if controle_da_tela is not None:
                page.views.append(
                    ft.View(
                        route="/",
                        controls=[controle_da_tela]
                    )
                )
            else:
                print("ERRO CRÍTICO: A função não retornou um controle Flet!")

        # ==================================================
        # ROTA RDO POR CLIENTE
        # ==================================================
        elif page.route.startswith("/rdo/"):
            cliente_id = int(page.route.split("/")[-1])
            
            controle_da_tela = construir_rdo(page, cliente_id)
            
            if controle_da_tela is not None:
                page.views.append(
                    ft.View(
                        route=page.route,
                        controls=[controle_da_tela]
                    )
                )

        page.update()

    # ======================================================
    # BOTÃO VOLTAR
    # ======================================================

    def view_pop(e):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    # ======================================================
    # REGISTRAR EVENTOS
    # ======================================================

    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # ======================================================
    # INICIAR NA HOME
    # ======================================================

    page.go("/")


# ==========================================================
# INICIAR APP
# ==========================================================

if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir=PASTA_ATIVOS # O Flet agora entende a pasta blindada!
    )
