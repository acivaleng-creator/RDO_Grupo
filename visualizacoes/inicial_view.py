# ==========================================================
# visualizacoes/inicial_view.py
# Tela Inicial com Login Global e Módulo Empresa (BLINDADO)
# ==========================================================

import flet as ft
import os
import shutil
import time
from servicos.empresa_service import listar_empresas, inserir_empresa, atualizar_logo

# IMPORTANDO A PASTA SEGURA
from config import PASTA_ATIVOS

def construir_tela_inicial(page: ft.Page):
    # --- ESTADO INICIAL ---
    empresas = listar_empresas()
    ultima_empresa_id = page.client_storage.get("ultima_empresa_id")
    estado_local = {"arquivo_logo": None}

    # --- COMPONENTES DE MENSAGEM ---
    msg_erro = ft.Text(color=ft.colors.RED, size=13, weight="bold")

    # ==========================================================
    # LAYOUT 1: TELA DE LOGIN (CADEADO GLOBAL)
    # ==========================================================
    
    # 1. PRIMEIRO: Definimos o que o Enter ou o Clique devem fazer
    def realizar_login(e):
        if campo_login.value == "acival" and campo_senha.value == "acival":
            page.session.set("autenticado", True)
            msg_erro.value = ""
            mostrar_layout_selecao()
        else:
            msg_erro.value = "Usuário ou senha incorretos!"
            page.update()

    # 2. SEGUNDO: Criamos os campos já "nascendo" com o Enter (on_submit) conectado!
    campo_login = ft.TextField(
        label="Usuário", 
        width=350, 
        prefix_icon=ft.icons.PERSON,
        on_submit=realizar_login
    )
    
    campo_senha = ft.TextField(
        label="Senha", 
        password=True, 
        can_reveal_password=True, 
        width=350, 
        prefix_icon=ft.icons.LOCK,
        on_submit=realizar_login
    )

    # 3. TERCEIRO: Montamos a tela
    layout_login = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15,
        controls=[
            ft.Icon(ft.icons.LOCK_PERSON, size=60, color=ft.colors.BLUE_900),
            ft.Text("Acesso Restrito", size=24, weight="bold", color=ft.colors.BLUE_900),
            ft.Text("Por favor, faça login para acessar o sistema.", size=14, color=ft.colors.GREY_600),
            campo_login,
            campo_senha,
            msg_erro,
            ft.ElevatedButton("Entrar no Sistema", width=350, height=50, bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE, on_click=realizar_login)
        ]
    )

    # ==========================================================
    # LAYOUT 2: SELEÇÃO / CRIAÇÃO DE EMPRESA
    # ==========================================================
    
    # CORREÇÃO DO CABO DE GUERRA: Funções separadas para Dropdown e Texto!
    def ao_selecionar_empresa(e):
        if dropdown_empresas.value: 
            campo_nova_empresa.value = ""
        page.update()

    def ao_digitar_nova_empresa(e):
        if campo_nova_empresa.value: 
            dropdown_empresas.value = None
        page.update()

    dropdown_empresas = ft.Dropdown(
        label="Empresas Cadastradas", 
        options=[ft.dropdown.Option(str(emp[0]), emp[1]) for emp in empresas],
        value=str(ultima_empresa_id) if ultima_empresa_id and any(str(emp[0])==str(ultima_empresa_id) for emp in empresas) else None,
        width=350, 
        on_change=ao_selecionar_empresa # Chama a função exclusiva do Dropdown
    )
    
    campo_nova_empresa = ft.TextField(
        label="Nome da Nova Empresa", 
        width=350, 
        on_change=ao_digitar_nova_empresa # Chama a função exclusiva do Texto
    )
    
    botao_logo = ft.ElevatedButton("Anexar Logo", icon=ft.icons.IMAGE, width=350)

    def logo_selecionada(e: ft.FilePickerResultEvent):
        if e.files:
            estado_local["arquivo_logo"] = e.files[0]
            botao_logo.text = f"Logo: {e.files[0].name}"
            botao_logo.icon_color = ft.colors.GREEN
            page.update()

    file_picker = ft.FilePicker(on_result=logo_selecionada)
    if file_picker not in page.overlay: page.overlay.append(file_picker)
    botao_logo.on_click = lambda _: file_picker.pick_files(file_type=ft.FilePickerFileType.IMAGE)

    def salvar_imagem(emp_id):
        if estado_local["arquivo_logo"]:
            arquivo = estado_local["arquivo_logo"]
            ext = os.path.splitext(arquivo.name)[1]
            nome_foto = f"logo_empresa_{emp_id}_{int(time.time())}{ext}"
            destino = os.path.join(PASTA_ATIVOS, nome_foto)
            shutil.copy(arquivo.path, destino)
            atualizar_logo(emp_id, nome_foto)

    def entrar_no_sistema(emp_id):
        page.empresa_ativa_id = emp_id
        page.client_storage.set("ultima_empresa_id", emp_id)
        if page.dialog:
            page.dialog.open = False
            page.update()
        page.go("/_limpar_tela")
        page.go("/")

    def validar_e_acessar(e):
        msg_erro.value = ""
        nome_nova = campo_nova_empresa.value.strip()

        if nome_nova:
            if nome_nova.lower() in [x[1].lower() for x in listar_empresas()]:
                msg_erro.value = "Esta empresa já existe!"; page.update(); return
            
            inserir_empresa(nome_nova)
            emp_id = next((x[0] for x in listar_empresas() if x[1].lower() == nome_nova.lower()), None)
            salvar_imagem(emp_id)
            entrar_no_sistema(emp_id)
        elif dropdown_empresas.value:
            emp_id = int(dropdown_empresas.value)
            if estado_local["arquivo_logo"]:
                salvar_imagem(emp_id)
            entrar_no_sistema(emp_id)
        else:
            msg_erro.value = "Selecione uma empresa ou digite o nome de uma nova."
            page.update()

    layout_selecao = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15,
        controls=[
            ft.Icon(ft.icons.BUSINESS, size=60, color=ft.colors.BLUE_900),
            ft.Text("Módulo Empresa", size=24, weight="bold", color=ft.colors.BLUE_900),
            dropdown_empresas,
            ft.Text("OU CRIAR NOVA", weight="bold", color=ft.colors.GREY_400),
            campo_nova_empresa,
            botao_logo,
            msg_erro,
            ft.Divider(height=10, color=ft.colors.TRANSPARENT),
            ft.ElevatedButton("Acessar Painel", icon=ft.icons.PLAY_ARROW, width=350, height=50, bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE, on_click=validar_e_acessar)
        ]
    )

    # ==========================================================
    # GESTÃO DA TELA E RETORNO
    # ==========================================================
    card_principal = ft.Card(
        elevation=10,
        content=ft.Container(
            padding=40, bgcolor=ft.colors.WHITE, border_radius=10, width=450,
            content=layout_selecao if page.session.get("autenticado") else layout_login
        )
    )

    def mostrar_layout_selecao():
        card_principal.content.content = layout_selecao
        page.update()

    return ft.Container(
        expand=True, 
        bgcolor=ft.colors.BLUE_GREY_50, 
        alignment=ft.alignment.center, 
        content=card_principal
    )