# ==========================================================
# visualizacoes/home_view.py
# Tela Inicial do Sistema RDO - MULTIEMPRESA (COMPLETO E BLINDADO)
# ==========================================================

import flet as ft
import os
import shutil
import json
import time
import base64

from servicos.cliente_service import (
    inserir_cliente,
    listar_clientes,
    excluir_cliente,
    atualizar_cliente
)

from servicos.empresa_service import (
    obter_empresa_por_id,
    atualizar_logo,
    listar_empresas,
    inserir_empresa,
    excluir_empresa
)

# IMPORTANDO A PASTA SEGURA DO ARQUIVO DE CONFIGURAÇÃO
from config import PASTA_ATIVOS, DIRETORIO_RAIZ

# ==========================================================
# CONSTRUIR HOME
# ==========================================================

def construir_home(page: ft.Page):

    # GARANTIA MÁXIMA DA PASTA DE ATIVOS NO WINDOWS
    pasta_absoluta = os.path.abspath(PASTA_ATIVOS)
    if not os.path.exists(pasta_absoluta):
        os.makedirs(pasta_absoluta)
        
    estado = {"cliente_editando_id": None}

    # ==========================================================
    # FILE PICKERS BLINDADOS (ANTI-FANTASMAS)
    # ==========================================================
    # O SEGREDO: Só criamos os botões de galeria UMA ÚNICA VEZ na vida do App!
    if not hasattr(page, "picker_nova_logo"):
        page.picker_nova_logo = ft.FilePicker()
        page.picker_trocar_logo = ft.FilePicker()
        page.overlay.append(page.picker_nova_logo)
        page.overlay.append(page.picker_trocar_logo)
        page.update()

    # O sistema puxa os mesmos pickers oficiais da memória (evitando clones)
    picker_nova_logo = page.picker_nova_logo
    picker_trocar_logo = page.picker_trocar_logo

    # ==========================================================
    # LOGO DINÂMICA
    # ==========================================================
    logo_container = ft.Container(
        width=220,
        height=110,
    )

    def atualizar_logo_visual():
        empresa = obter_empresa_por_id(getattr(page, "empresa_ativa_id", None))
        logo_src = None

        if isinstance(empresa, dict):
            logo_src = empresa.get("logo")
        elif isinstance(empresa, (tuple, list)):
            for item in empresa:
                if isinstance(item, str) and item.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    logo_src = item
                    break
            if not logo_src and len(empresa) > 2 and empresa[2]:
                logo_src = str(empresa[2]).strip()

        if logo_src and logo_src.lower() not in ["none", "null", ""]:
            caminho_fisico = os.path.join(pasta_absoluta, logo_src)
            
            if os.path.exists(caminho_fisico):
                # A ARMA SECRETA: Lemos a imagem e convertemos para Base64
                try:
                    with open(caminho_fisico, "rb") as img_file:
                        b64_string = base64.b64encode(img_file.read()).decode('utf-8')
                    
                    logo_container.content = ft.Image(
                        src_base64=b64_string, 
                        width=220,
                        height=110,
                        fit=ft.ImageFit.CONTAIN
                    )
                except Exception as ex:
                    logo_container.content = ft.Text("ERRO AO LER IMAGEM", color=ft.colors.RED)
            else:
                logo_container.content = ft.Text(f"FOTO NÃO ACHADA:\n{caminho_fisico}", color=ft.colors.RED, size=10, weight="bold", text_align=ft.TextAlign.CENTER)
        else:
            logo_container.content = ft.Text("LOGO EMPRESA", size=20, weight="bold")
            
        page.update()

    atualizar_logo_visual()

    # ==========================================================
    # CAMPOS DE CADASTRO DE CLIENTE
    # ==========================================================
    campo_cliente = ft.TextField(
        label="Cliente (Obrigatório)", 
        expand=1
    )
    campo_os = ft.TextField(
        label="Ordem de Serviço (Obrigatório)", 
        expand=1, 
        hint_text="Ex: OS-1234/A"
    )
    
    campo_obra = ft.TextField(
        label="Obra", 
        expand=1
    )
    campo_cidade = ft.TextField(
        label="Cidade", 
        expand=1
    )
    
    campo_servico = ft.TextField(
        label="Serviço", 
        expand=1
    )
    campo_especificacao = ft.TextField(
        label="Especificação", 
        expand=1
    )

    def limpar_form():
        estado["cliente_editando_id"] = None
        campo_cliente.value = ""
        campo_os.value = ""
        campo_obra.value = ""
        campo_cidade.value = ""
        campo_servico.value = ""
        campo_especificacao.value = ""
        page.update()

    def salvar_cliente(e):
        if not campo_cliente.value.strip() or not campo_os.value.strip():
            page.snack_bar = ft.SnackBar(
                ft.Text(
                    "Erro: O Nome do Cliente e a Ordem de Serviço (OS) são obrigatórios!", 
                    color=ft.colors.WHITE, 
                    weight="bold"
                ), 
                bgcolor=ft.colors.RED_700
            )
            page.snack_bar.open = True
            page.update()
            return

        if estado["cliente_editando_id"]:
            atualizar_cliente(
                estado["cliente_editando_id"], 
                campo_cliente.value, 
                campo_obra.value, 
                campo_cidade.value, 
                campo_servico.value, 
                campo_os.value, 
                campo_especificacao.value
            )
            msg = "Cliente atualizado com sucesso!"
        else:
            inserir_cliente(
                page.empresa_ativa_id, 
                campo_cliente.value, 
                campo_obra.value, 
                campo_cidade.value, 
                campo_servico.value, 
                campo_os.value, 
                campo_especificacao.value
            )
            msg = "Novo cliente cadastrado com sucesso!"

        limpar_form()
        atualizar_lista()
        
        page.snack_bar = ft.SnackBar(
            ft.Text(msg, color=ft.colors.WHITE), 
            bgcolor=ft.colors.GREEN_700
        )
        page.snack_bar.open = True
        page.update()

    def fechar_dialog_seguro(dialog):
        dialog.open = False
        page.update()

    # ==========================================================
    # CONFIRMAÇÃO DE EDIÇÃO DO CLIENTE
    # ==========================================================
    def tentar_editar_cliente(cliente):
        def confirmar_edicao(e):
            dialog_edicao.open = False
            page.update()
            
            estado["cliente_editando_id"] = cliente[0]
            campo_cliente.value = str(cliente[1]) if cliente[1] else ""
            campo_obra.value = str(cliente[2]) if cliente[2] else ""
            campo_cidade.value = str(cliente[3]) if len(cliente) > 3 and cliente[3] else ""
            campo_servico.value = str(cliente[4]) if len(cliente) > 4 and cliente[4] else ""
            campo_os.value = str(cliente[5]) if len(cliente) > 5 and cliente[5] else ""
            campo_especificacao.value = str(cliente[6]) if len(cliente) > 6 and cliente[6] else ""
            
            page.snack_bar = ft.SnackBar(
                ft.Text(
                    "Modo de Edição Ativado! Altere os dados acima e clique em Salvar.", 
                    color=ft.colors.WHITE
                ), 
                bgcolor=ft.colors.ORANGE_800
            )
            page.snack_bar.open = True
            page.update()

        dialog_edicao = ft.AlertDialog(
            modal=True, 
            title=ft.Text("Confirmar Edição", color=ft.colors.ORANGE_800), 
            content=ft.Text(f"Deseja carregar os dados do cliente '{cliente[1]}' para edição?"),
            actions=[
                ft.TextButton(
                    "Cancelar", 
                    on_click=lambda e: fechar_dialog_seguro(dialog_edicao)
                ), 
                ft.ElevatedButton(
                    "Sim, Editar", 
                    bgcolor=ft.colors.ORANGE_800, 
                    color=ft.colors.WHITE, 
                    on_click=confirmar_edicao
                )
            ]
        )
        if dialog_edicao not in page.overlay:
            page.overlay.append(dialog_edicao)
        dialog_edicao.open = True
        page.update()

    # ==========================================================
    # LISTA DE CLIENTES
    # ==========================================================
    tabela_clientes = ft.Column(spacing=8)
    
    campo_pesquisa = ft.Container(
    margin=ft.margin.only(left=20), # <-- Isso cria o espaço exato entre o texto e a caixa
    expand=True,
    content=ft.TextField(
        hint_text="Pesquisar...", 
        prefix_icon=ft.icons.SEARCH, 
        on_change=lambda e: atualizar_lista(e.control.value)
    )
)

    def abrir_rdo(id_cliente):
        page.go(f"/rdo/{id_cliente}")
        if hasattr(page, "on_route_change") and callable(page.on_route_change):
            page.on_route_change(None)

    def atualizar_lista(filtro=""):
        tabela_clientes.controls.clear()
        clientes = listar_clientes(getattr(page, "empresa_ativa_id", None))

        for c in clientes:
            if filtro:
                if filtro.lower() not in c[1].lower() and (len(c) > 3 and c[3] and filtro.lower() not in c[3].lower()):
                    continue

            tabela_clientes.controls.append(
                ft.Container(
                    padding=10, 
                    bgcolor=ft.colors.GREY_100, 
                    border_radius=10,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                expand=3, 
                                controls=[
                                    ft.Text(
                                        f"{c[1]} (OS: {c[5] if len(c) > 5 and c[5] else '-'})", 
                                        weight="bold"
                                    ),
                                    ft.Text(
                                        f"{c[3] if len(c)>3 and c[3] else '-'} | {c[4] if len(c)>4 and c[4] else '-'}", 
                                        size=12
                                    )
                                ]
                            ),
                            ft.Row(
                                spacing=5, 
                                controls=[
                                    ft.IconButton(
                                        icon=ft.icons.DESCRIPTION if hasattr(ft, "icons") else ft.Icons.DESCRIPTION, 
                                        tooltip="Abrir RDO", 
                                        icon_color=ft.colors.BLUE if hasattr(ft, "colors") else ft.Colors.BLUE, 
                                        on_click=lambda e, id_cli=c[0]: abrir_rdo(id_cli) 
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.VISIBILITY if hasattr(ft, "icons") else ft.Icons.VISIBILITY, 
                                        tooltip="Ficha do Cliente", 
                                        icon_color=ft.colors.GREEN if hasattr(ft, "colors") else ft.Colors.GREEN, 
                                        on_click=lambda e, dados_cli=c: visualizar_cliente(dados_cli)
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.EDIT if hasattr(ft, "icons") else ft.Icons.EDIT, 
                                        tooltip="Editar Cadastro", 
                                        icon_color=ft.colors.ORANGE_800 if hasattr(ft, "colors") else ft.Colors.ORANGE_800, 
                                        on_click=lambda e, dados_cli=c: tentar_editar_cliente(dados_cli)
                                    ),
                                    ft.IconButton(
                                        icon=ft.icons.DELETE if hasattr(ft, "icons") else ft.Icons.DELETE, 
                                        tooltip="Excluir", 
                                        icon_color=ft.colors.RED if hasattr(ft, "colors") else ft.Colors.RED, 
                                        on_click=lambda e, dados_cli=c: tentar_excluir_cliente(dados_cli)
                                    ),
                                ]
                            )
                        ]
                    )
                )
            )
        page.update()

    def visualizar_cliente(cliente):
        def cel(label, valor):
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(
                            label, 
                            weight="bold", 
                            size=13, 
                            color=ft.colors.BLUE_GREY_700, 
                            width=130
                        ), 
                        ft.Text(
                            valor, 
                            size=13, 
                            color=ft.colors.BLACK, 
                            expand=True, 
                            weight="bold"
                        )
                    ]
                ),
                padding=ft.padding.symmetric(vertical=10, horizontal=20), 
                border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_200))
            )

        conteudo = ft.Container(
            width=500, 
            bgcolor=ft.colors.WHITE, 
            border_radius=8,
            content=ft.Column(
                spacing=0, 
                tight=True, 
                controls=[
                    ft.Container(
                        bgcolor=ft.colors.BLUE_900, 
                        padding=15, 
                        border_radius=ft.border_radius.only(top_left=8, top_right=8), 
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.BUSINESS_CENTER, color=ft.colors.WHITE), 
                                ft.Text("FICHA DO CLIENTE", weight="bold", size=16, color=ft.colors.WHITE)
                            ]
                        )
                    ),
                    cel("CLIENTE:", cliente[1]), 
                    cel("ORDEM DE SERVIÇO:", cliente[5] if len(cliente) > 5 and cliente[5] else "-"),
                    cel("OBRA:", cliente[2]), 
                    cel("CIDADE:", cliente[3] if len(cliente) > 3 and cliente[3] else "-"),
                    cel("SERVIÇO:", cliente[4] if len(cliente) > 4 and cliente[4] else "-"), 
                    cel("ESPECIFICAÇÃO:", cliente[6] if len(cliente) > 6 and cliente[6] else "-"),
                    ft.Container(height=10) 
                ]
            )
        )

        dialog = ft.AlertDialog(
            modal=True, 
            content_padding=0, 
            content=conteudo, 
            actions_padding=15, 
            actions=[
                ft.TextButton("Fechar Ficha", on_click=lambda e: fechar_dialog_seguro(dialog))
            ]
        )
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def tentar_excluir_cliente(cliente):
        cliente_id = cliente[0]
        nome_cliente = cliente[1]
        arquivo_rdos = os.path.join(DIRETORIO_RAIZ, "banco_rdos", f"cliente_{cliente_id}_rdos.json")
        tem_rdos = False
        
        if os.path.exists(arquivo_rdos):
            try:
                with open(arquivo_rdos, 'r', encoding='utf-8') as f:
                    if len(json.load(f)) > 0: 
                        tem_rdos = True
            except Exception: 
                pass
        
        if tem_rdos:
            page.snack_bar = ft.SnackBar(
                ft.Text(
                    f"AÇÃO BLOQUEADA: '{nome_cliente}' possui RDOs. Apague os RDOs primeiro.", 
                    color=ft.colors.WHITE, 
                    weight="bold"
                ), 
                bgcolor=ft.colors.RED_800, 
                duration=5000
            )
            page.snack_bar.open = True
            page.update()
        else:
            def confirmar_final(e):
                excluir_cliente(cliente_id)
                dialog_inicial.open = False
                page.update()
                atualizar_lista()
                page.snack_bar = ft.SnackBar(
                    ft.Text("Cliente excluído permanentemente!", color=ft.colors.WHITE), 
                    bgcolor=ft.colors.GREEN_700
                )
                page.snack_bar.open = True
                page.update()

            dialog_inicial = ft.AlertDialog(
                modal=True, 
                title=ft.Text("Confirmação de Exclusão", color=ft.colors.RED_700),
                content=ft.Text(f"Deseja realmente excluir o cliente '{nome_cliente}'?\nEsta ação não pode ser desfeita."),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: fechar_dialog_seguro(dialog_inicial)), 
                    ft.ElevatedButton("Sim, Excluir", bgcolor=ft.colors.RED_700, color=ft.colors.WHITE, on_click=confirmar_final)
                ]
            )
            if dialog_inicial not in page.overlay:
                page.overlay.append(dialog_inicial)
            dialog_inicial.open = True
            page.update()

    atualizar_lista()
    
    # ==========================================================
    # MENU CONFIGURAÇÃO EMPRESA (LAYOUT MOBILE OTIMIZADO)
    # ==========================================================
    def abrir_menu_empresa(e):
        empresas = listar_empresas()
        
        container_modal = ft.Container(width=400, padding=10) # Largura ajustada para celular

        dialog_principal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Gestão de Empresa", weight="bold", size=20),
            content=container_modal,
            actions=[ft.TextButton("Fechar Janela", on_click=lambda e: fechar_dialog_seguro(dialog_principal))]
        )

        def mudar_tela_modal(nova_tela):
            container_modal.content = nova_tela
            page.update()

        # --- PROTEÇÃO POR SENHA ---
        def acao_protegida(destino):
            if getattr(page, "autenticado", False):
                destino() if callable(destino) else mudar_tela_modal(destino)
            else:
                c_user = ft.TextField(label="Usuário", prefix_icon=ft.icons.PERSON)
                c_pass = ft.TextField(label="Senha", password=True, prefix_icon=ft.icons.LOCK)
                msg_log = ft.Text(color=ft.colors.RED, size=12, weight="bold")

                def validar(e):
                    if c_user.value == "acival" and c_pass.value == "acival":
                        page.autenticado = True
                        destino() if callable(destino) else mudar_tela_modal(destino)
                    else:
                        msg_log.value = "Usuário ou Senha incorretos!"
                        page.update()

                tela_login = ft.Column(tight=True, spacing=15, controls=[
                    ft.Text("Acesso de Supervisor", weight="bold", color=ft.colors.RED_800),
                    c_user, c_pass, msg_log,
                    ft.Row([
                        ft.TextButton("Cancelar", on_click=lambda _: mudar_tela_modal(tela_padrao), expand=True),
                        ft.ElevatedButton("Login", bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE, on_click=validar, expand=True)
                    ])
                ])
                mudar_tela_modal(tela_login)

        # --- CRIAR NOVA EMPRESA ---
        arquivo_nova_logo = {"selecionado": None}
        campo_nome_nova_empresa = ft.TextField(label="Nome da Nova Empresa")
        msg_erro_nova = ft.Text(color=ft.colors.RED, size=12)
        btn_anexar_logo = ft.ElevatedButton("Anexar Logo", icon=ft.icons.IMAGE)

        def processar_nova_logo(ev: ft.FilePickerResultEvent):
            if ev.files:
                arquivo_nova_logo["selecionado"] = ev.files[0]
                btn_anexar_logo.text = f"Logo Selecionada"
                btn_anexar_logo.icon_color = ft.colors.GREEN
                page.update()

        picker_nova_logo.on_result = processar_nova_logo
        def abrir_picker_nova_empresa(e):
            if picker_nova_logo not in page.overlay:
                page.overlay.append(picker_nova_logo)
                page.update()
            picker_nova_logo.pick_files(file_type=ft.FilePickerFileType.IMAGE)

        btn_anexar_logo.on_click = abrir_picker_nova_empresa

        def salvar_nova_empresa(ev):
            nome = campo_nome_nova_empresa.value.strip()
            if not nome:
                msg_erro_nova.value = "Digite um nome válido."; page.update(); return
            
            if nome.lower() in [emp[1].strip().lower() for emp in listar_empresas()]:
                msg_erro_nova.value = "Empresa já existe!"; page.update(); return
            
            inserir_empresa(nome)
            nova_id = next((e[0] for e in listar_empresas() if str(e[1]).lower() == nome.lower()), None)
            
            if nova_id and arquivo_nova_logo["selecionado"]:
                arquivo = arquivo_nova_logo["selecionado"]
                extensao = os.path.splitext(arquivo.name)[1]
                nome_foto = f"logo_empresa_{nova_id}_{int(time.time())}{extensao}"
                try:
                    shutil.copy2(arquivo.path, os.path.join(pasta_absoluta, nome_foto))
                    atualizar_logo(nova_id, nome_foto)
                except Exception as ex: print(f"Erro ao salvar logo: {ex}")
            
            dialog_principal.open = False
            page.empresa_ativa_id = nova_id; page.ultima_empresa_id = nova_id
            page.update(); atualizar_logo_visual(); atualizar_lista()
            arquivo_nova_logo["selecionado"] = None

        tela_criar_empresa = ft.Column(tight=True, spacing=15, controls=[
            ft.Text("Cadastrar Nova Empresa", weight="bold", size=16),
            campo_nome_nova_empresa, btn_anexar_logo, msg_erro_nova,
            ft.Row([
                ft.TextButton("Voltar", on_click=lambda e: mudar_tela_modal(tela_padrao), expand=True),
                ft.ElevatedButton("Salvar", bgcolor=ft.colors.BLUE_800, color=ft.colors.WHITE, on_click=salvar_nova_empresa, expand=True)
            ])
        ])

        # --- TROCAR LOGO EXISTENTE ---
        # --- TROCAR LOGO EXISTENTE ---
        def processar_logo_atualizada(ev: ft.FilePickerResultEvent):
            if not ev.files: 
                return 
            
            # BLINDAGEM MÁXIMA: Garante que o ID seja estritamente um NÚMERO INTEIRO da empresa certa
            emp_str = dropdown_empresas.value
            if not emp_str:
                emp_str = str(page.empresa_ativa_id)
                
            emp_id_inteiro = int(emp_str) # Força o Python a tratar como número, não como texto!

            try:
                arquivo = ev.files[0]
                
                # Faxina: Apaga só as fotos antigas DESTA empresa
                for f in os.listdir(pasta_absoluta):
                    if f.startswith(f"logo_empresa_{emp_id_inteiro}_"):
                        try: os.remove(os.path.join(pasta_absoluta, f))
                        except: pass 
                        
                extensao = os.path.splitext(arquivo.name)[1]
                nome_novo = f"logo_empresa_{emp_id_inteiro}_{int(time.time())}{extensao}" 
                shutil.copy2(arquivo.path, os.path.join(pasta_absoluta, nome_novo))
                
                # Grava no banco usando o número inteiro isolado
                atualizar_logo(emp_id_inteiro, nome_novo)
                
                dialog_principal.open = False
                
                # Atualiza a tela APENAS se a empresa alterada for a que está ativa no fundo
                if emp_id_inteiro == int(page.empresa_ativa_id): 
                    atualizar_logo_visual()
                    
                # AVISO VERDE NA TELA CONFIRMANDO O ID EXATO
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"SISTEMA: Logo da Empresa ID [{emp_id_inteiro}] salva isoladamente!", color=ft.colors.WHITE, weight="bold"), 
                    bgcolor=ft.colors.GREEN_700
                )
                page.snack_bar.open = True
                page.update()
                
            except Exception as ex: 
                print(f"Erro fatal: {ex}")

        picker_trocar_logo.on_result = processar_logo_atualizada

        # --- EXCLUIR EMPRESA ---
        def executar_exclusao_final(e):
            emp_id = int(dropdown_empresas.value)
            try:
                for arquivo in os.listdir(pasta_absoluta):
                    if arquivo.startswith(f"logo_empresa_{emp_id}_"): os.remove(os.path.join(pasta_absoluta, arquivo))
            except: pass
            excluir_empresa(emp_id)
            dialog_principal.open = False
            page.empresa_ativa_id = None; page.route = "/"
            page.update()
            if hasattr(page, "on_route_change") and callable(page.on_route_change): page.on_route_change(None)

        tela_excluir_final = ft.Column(tight=True, spacing=15, controls=[
            ft.Text("CONFIRMAÇÃO FINAL", color=ft.colors.RED, weight="bold", size=16),
            ft.Text("Esta ação apagará a empresa do banco para sempre.\nTem certeza?"),
            ft.Row([
                ft.TextButton("Cancelar", on_click=lambda e: mudar_tela_modal(tela_padrao), expand=True),
                ft.ElevatedButton("Apagar", bgcolor=ft.colors.RED_800, color=ft.colors.WHITE, on_click=executar_exclusao_final, expand=True)
            ])
        ])

        def tentar_abrir_exclusao(e):
            if dropdown_empresas.value:
                clientes_vinculados = listar_clientes(int(dropdown_empresas.value))
                if len(clientes_vinculados) > 0:
                    page.snack_bar = ft.SnackBar(ft.Text("Erro: Apague os clientes antes de excluir a empresa!", color=ft.colors.WHITE), bgcolor=ft.colors.RED_800)
                    page.snack_bar.open = True; page.update()
                else: acao_protegida(lambda: mudar_tela_modal(tela_excluir_final))

       # --- TELA PADRÃO (AQUI FOI CORRIGIDO PARA O MOBILE) ---
        dropdown_empresas = ft.Dropdown(
            label="Selecione a Empresa",
            value=str(page.empresa_ativa_id) if page.empresa_ativa_id else None,
            options=[ft.dropdown.Option(str(emp[0]), emp[1]) for emp in empresas],
        )

        def confirmar_troca(ev):
            if dropdown_empresas.value:
                page.empresa_ativa_id = int(dropdown_empresas.value)
                page.ultima_empresa_id = page.empresa_ativa_id
                dialog_principal.open = False
                page.update(); atualizar_logo_visual(); atualizar_lista()

        # --- FUNÇÃO NOVA PARA DESCONGELAR A TELA ---
        
        def acao_abrir_picker():
            mudar_tela_modal(tela_padrao) # Primeiro tira a tela de senha da frente!
            
            # GARANTIA: Adiciona o FilePicker à página se ele não estiver lá
            if picker_trocar_logo not in page.overlay:
                page.overlay.append(picker_trocar_logo)
                page.update()
                
            picker_trocar_logo.pick_files(file_type=ft.FilePickerFileType.IMAGE) # Depois abre a galeria

        tela_padrao = ft.Column(tight=True, spacing=15, controls=[
            dropdown_empresas, 
            ft.ElevatedButton("Ativar Empresa", icon=ft.icons.CHECK_CIRCLE, icon_color=ft.colors.GREEN, on_click=confirmar_troca, width=400),
            ft.Row([
                # O botão de Logo agora chama a função "acao_abrir_picker" que criamos ali em cima!
                ft.ElevatedButton("Logo", icon=ft.icons.IMAGE, on_click=lambda e: acao_protegida(acao_abrir_picker), expand=True),
                ft.ElevatedButton("Excluir", icon=ft.icons.DELETE, icon_color=ft.colors.RED, on_click=tentar_abrir_exclusao, expand=True),
            ]),
            ft.Divider(),
            ft.ElevatedButton("➕ Criar Nova Empresa", bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE, on_click=lambda e: acao_protegida(lambda: mudar_tela_modal(tela_criar_empresa)), width=400)
        ])

        mudar_tela_modal(tela_padrao)
        if dialog_principal not in page.overlay: page.overlay.append(dialog_principal)
        dialog_principal.open = True
        page.update()
    
    # ==========================================================
    # LAYOUT PRINCIPAL (SEM FILEPICKER AQUI DENTRO!!!)
    # ==========================================================
    return ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            controls=[
                ft.Container(
                    bgcolor="#D1FDFF",
                    padding=15,
                    border_radius=10,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            logo_container,
                            ft.IconButton(
                                icon=ft.icons.SETTINGS,
                                tooltip="Configurações da Empresa",
                                on_click=abrir_menu_empresa 
                            )
                        ]
                    )
                ),
                ft.Text(
                    "Cadastro de Cliente", 
                    size=22, 
                    weight="bold"
                ),
                ft.Row(
                    controls=[
                        campo_cliente, 
                        campo_os
                    ]
                ),
                ft.Row(
                    controls=[
                        campo_obra, 
                        campo_cidade
                    ]
                ),
                ft.Row(
                    controls=[
                        campo_servico, 
                        campo_especificacao
                    ]
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.ElevatedButton(
                            "Limpar Formulário", 
                            icon=ft.icons.CLEANING_SERVICES, 
                            on_click=lambda e: limpar_form(), 
                            color=ft.colors.RED_700, 
                            bgcolor=ft.colors.RED_50
                        ),
                        ft.ElevatedButton(
                            "Salvar Cliente", 
                            icon=ft.icons.SAVE, 
                            on_click=salvar_cliente, 
                            bgcolor=ft.colors.GREEN_700, 
                            color=ft.colors.WHITE
                        )
                    ]
                ),
                ft.Divider(),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(
                            "Lista de Clientes", 
                            size=22, 
                            weight="bold"
                        ),
                        campo_pesquisa
                    ]
                ),
                tabela_clientes
            ]
        )
    )