# ==========================================================
# visualizacoes/rdo_view.py
# Tela de Histórico e Formulário de RDO
# ==========================================================

import flet as ft
import os
import shutil
import json
import time
from datetime import datetime

from servicos.empresa_service import obter_empresa_por_id
from servicos.cliente_service import listar_clientes
from servicos.pdf_service import gerar_pdf_oficial
from servicos.visao_profissional import exibir_visao_profissional

from config import PASTA_ATIVOS, PASTA_BANCO, DIRETORIO_RAIZ

def construir_rdo(page: ft.Page, cliente_id: int):
    # Configura o idioma da página para Português
    page.locale = "pt-BR"

    # --- FUNÇÃO BLINDADA PARA AVISOS ---
    def exibir_aviso(msg, cor):
        snack = ft.SnackBar(ft.Text(msg, color=ft.colors.WHITE), bgcolor=cor)
        if hasattr(page, "open"):
            page.open(snack)
        else:
            page.snack_bar = snack
            snack.open = True
            page.update()

    # ==========================================================
    # 1. DADOS INICIAIS E ESTADO DO APP E PASTAS
    # ==========================================================
    empresa = obter_empresa_por_id(page.empresa_ativa_id)
    logo_src = empresa.get("logo") if isinstance(empresa, dict) else (empresa[2] if isinstance(empresa, (tuple, list)) and len(empresa) > 2 else None)

    clientes = listar_clientes(page.empresa_ativa_id)
    cliente_dados = next((c for c in clientes if c[0] == cliente_id), None)

    nome_cliente = cliente_dados[1] if cliente_dados else "Cliente não encontrado"
    obra_cliente = cliente_dados[2] if cliente_dados else "-"
    cidade_cliente = cliente_dados[3] if cliente_dados and len(cliente_dados) > 3 else "-"
    servico_cliente = cliente_dados[4] if cliente_dados and len(cliente_dados) > 4 else "-"
    os_cliente = cliente_dados[5] if cliente_dados and len(cliente_dados) > 5 else "" 
    especificacao_cliente = cliente_dados[6] if cliente_dados and len(cliente_dados) > 6 else ""
    
    data_atual = datetime.now().strftime("%d/%m/%Y")
    
    # Controle da assinatura no estado do app (Texto, Desenho ou Imagem)
    estado_app = {"rdo_editando_id": None, "ass": {"tipo": None, "valor": None}}

    # BLINDAGEM DE PASTAS
    arquivo_bd_rdos = os.path.join(PASTA_BANCO, f"cliente_{cliente_id}_rdos.json")
    PASTA_FOTOS_RDO = os.path.join(DIRETORIO_RAIZ, "fotos_rdo")
    PASTA_ASSINATURAS = os.path.join(DIRETORIO_RAIZ, "assinaturas") 
    
    if not os.path.exists(PASTA_FOTOS_RDO):
        os.makedirs(PASTA_FOTOS_RDO)
    if not os.path.exists(PASTA_ASSINATURAS):
        os.makedirs(PASTA_ASSINATURAS)

    # CONTEXTO QUE SERÁ ENVIADO PARA OS ARQUIVOS EXTERNOS
    contexto_pdf = {
        "nome_cliente": nome_cliente,
        "obra_cliente": obra_cliente,
        "cidade_cliente": cidade_cliente,
        "servico_cliente": servico_cliente,
        "os_cliente": os_cliente,
        "especificacao_cliente": especificacao_cliente,
        "empresa": empresa,
        "logo_src": logo_src,
        "diretorio_raiz": DIRETORIO_RAIZ,
        "pasta_ativos": PASTA_ATIVOS
    }

    # FUNÇÕES DE BANCO DE DADOS (JSON)
    def carregar_dados_rdos():
        if os.path.exists(arquivo_bd_rdos):
            try:
                with open(arquivo_bd_rdos, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def salvar_dados_rdos():
        with open(arquivo_bd_rdos, 'w', encoding='utf-8') as f:
            json.dump(rdos_dados, f, ensure_ascii=False, indent=4)

    rdos_dados = carregar_dados_rdos()

    def atualizar_numeracao():
        total = len(rdos_dados)
        for i, rdo in enumerate(rdos_dados):
            rdo['num'] = f"{(total - i):03d}"
        salvar_dados_rdos() 

    # ==========================================================
    # 2. SISTEMAS DE SUPORTE (POP-UPS E CALENDÁRIO)
    # ==========================================================
    
    # --- SISTEMA DE ÁREA INOPERANTE ---
    input_dialog_just = ft.TextField(label="Descreva o motivo da área inoperante", multiline=True, min_lines=3)
    campo_just_inoperante = ft.TextField(
    label="Justificativa da Área", 
    visible=False, 
    # expand=True, <-- APAGUE ISSO! Ele é o causador do bug.
    read_only=True, 
    bgcolor=ft.colors.RED_50
)

    def fechar_dialog_inop(e):
        dialog_inop.open = False
        page.update()

    def salvar_just_inop(e):
        if not input_dialog_just.value.strip():
            input_dialog_just.error_text = "Preencha a justificativa!"
            page.update()
            return
        
        input_dialog_just.error_text = None
        campo_just_inoperante.value = input_dialog_just.value
        campo_just_inoperante.visible = True
        dialog_inop.open = False
        page.update()

    def cancelar_just_inop(e):
        dd_condicao_area.value = "Operável"
        campo_just_inoperante.visible = False
        campo_just_inoperante.value = ""
        dialog_inop.open = False
        page.update()

    dialog_inop = ft.AlertDialog(
        modal=True,
        title=ft.Text("Justificativa Obrigatória", color=ft.colors.RED_700),
        content=input_dialog_just,
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar_just_inop),
            ft.ElevatedButton("Salvar Justificativa", on_click=salvar_just_inop, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE)
        ]
    )
    page.overlay.append(dialog_inop)

    def mudar_condicao_area(e):
        if e.control.value in ["Inop. Parc.", "Inop. Total"]:
            input_dialog_just.value = campo_just_inoperante.value 
            # Use page.open se estiver no Flet 0.21+, ou mantenha o .open = True 
            # mas garanta que o diálogo já esteja no overlay ou instanciado corretamente.
            dialog_inop.open = True
            page.update()
        else:
            campo_just_inoperante.visible = False
            campo_just_inoperante.value = ""
            page.update()

    # --- SISTEMA DE CALENDÁRIO ---
    def selecionar_data(e):
        if e.control.value:
            campo_data.value = e.control.value.strftime("%d/%m/%Y")
            page.update()

    datepicker = ft.DatePicker(
        on_change=selecionar_data, 
        help_text="Selecione a data do RDO", 
        cancel_text="Cancelar", 
        confirm_text="OK"
    )
    page.overlay.append(datepicker)

    # --- SISTEMA DE ASSINATURA (ACROBAT STYLE) ---
    texto_feedback_assinatura = ft.Text("Nenhuma assinatura anexada", color=ft.colors.RED_700, italic=True)

    input_ass_texto = ft.TextField(label="Digite seu nome completo", text_style=ft.TextStyle(italic=True, size=20, color=ft.colors.BLUE_900), expand=True)
    aba_texto = ft.Tab(
        text="Digitar", 
        icon=ft.icons.KEYBOARD, 
        content=ft.Container(
            padding=20, 
            content=ft.Column([
                ft.Text("A assinatura será gerada em formato cursivo no PDF.", color=ft.colors.GREY_600), 
                input_ass_texto
            ])
        )
    )

    aba_desenho = ft.Tab(
        text="Desenhar", 
        icon=ft.icons.DRAW, 
        content=ft.Container(
            padding=20, 
            content=ft.Column([
                ft.Text("Desenhe sua assinatura abaixo:", color=ft.colors.GREY_600), 
                ft.Container(
                    height=120, expand=True, bgcolor=ft.colors.GREY_100, border=ft.border.all(1, ft.colors.GREY_400), 
                    content=ft.Text("Área de desenho livre\n(Disponível em breve)", text_align=ft.TextAlign.CENTER, color=ft.colors.GREY_400), 
                    alignment=ft.alignment.center
                )
            ])
        )
    )

    ass_imagem_caminho = [""]
    img_ass_preview = ft.Image(height=80, fit=ft.ImageFit.CONTAIN, visible=False)
    
    def on_ass_img_picked(e: ft.FilePickerResultEvent):
        if e.files:
            ass_imagem_caminho[0] = e.files[0].path
            img_ass_preview.src = e.files[0].path
            img_ass_preview.visible = True
            page.update()
            
    picker_ass = ft.FilePicker(on_result=on_ass_img_picked)
    page.overlay.append(picker_ass)
    
    aba_imagem = ft.Tab(
        text="Galeria", 
        icon=ft.icons.IMAGE, 
        content=ft.Container(
            padding=20, 
            content=ft.Column([
                ft.Text("Selecione uma imagem (.PNG transparente).", color=ft.colors.GREY_600), 
                ft.ElevatedButton("Escolher Imagem", on_click=lambda _: picker_ass.pick_files(file_type=ft.FilePickerFileType.IMAGE)), 
                img_ass_preview
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    )

    abas_assinatura = ft.Tabs(selected_index=0, animation_duration=300, tabs=[aba_texto, aba_desenho, aba_imagem], height=250)

    def confirmar_assinatura_modal(e):
        idx = abas_assinatura.selected_index
        if idx == 0: 
            if input_ass_texto.value.strip():
                estado_app["ass"]["tipo"] = "texto"
                estado_app["ass"]["valor"] = input_ass_texto.value.strip()
                texto_feedback_assinatura.value = f"Assinado por: {estado_app['ass']['valor']}"
                texto_feedback_assinatura.color = ft.colors.GREEN_700
                texto_feedback_assinatura.margin = ft.margin.only(top=-10)
        elif idx == 1: 
            pass 
        elif idx == 2: 
            if ass_imagem_caminho[0]:
                estado_app["ass"]["tipo"] = "imagem"
                estado_app["ass"]["valor"] = ass_imagem_caminho[0]
                texto_feedback_assinatura.value = "Imagem anexada com sucesso."
                texto_feedback_assinatura.color = ft.colors.GREEN_700
                texto_feedback_assinatura.margin = ft.margin.only(top=-10)
        dialog_assinatura.open = False
        page.update()

    def cancelar_assinatura_modal(e):
        dialog_assinatura.open = False
        page.update()

    dialog_assinatura = ft.AlertDialog(
        modal=True, 
        title=ft.Text("Assinatura do Responsável", weight="bold"), 
        content=ft.Container(width=400, content=abas_assinatura), 
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar_assinatura_modal), 
            ft.ElevatedButton("Confirmar Assinatura", bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE, on_click=confirmar_assinatura_modal)
        ]
    )
    
    def abrir_modal_assinatura(e):
        page.dialog = dialog_assinatura
        dialog_assinatura.open = True
        page.update()

    def limpar_assinatura():
        estado_app["ass"]["tipo"] = None
        estado_app["ass"]["valor"] = None
        input_ass_texto.value = ""
        ass_imagem_caminho[0] = ""
        img_ass_preview.visible = False
        texto_feedback_assinatura.value = "Nenhuma assinatura anexada"
        texto_feedback_assinatura.color = ft.colors.RED_700
        page.update()

    # ==========================================================
    # 3. CAMPOS DO FORMULÁRIO (ARQUITETURA MOBILE CORRIGIDA)
    # ==========================================================
    def titulo_secao(texto):
        return ft.Row([
            ft.Container(height=1, bgcolor=ft.colors.BLUE_GREY_200, expand=True), 
            ft.Text(texto, size=12, color=ft.colors.BLUE_GREY_500, weight="bold"), 
            ft.Container(height=1, bgcolor=ft.colors.BLUE_GREY_200, expand=True)
        ])

    cabecalho_cliente_ui = ft.Container(
        padding=10,
        content=ft.Column(spacing=5, controls=[
            titulo_secao("Dados do Cliente"),
            ft.Row([
                ft.Text(f"Cliente: {nome_cliente}", weight="bold", expand=True, color=ft.colors.BLUE_900), 
                ft.Text(f"OS: {os_cliente}", weight="bold", expand=True, text_align=ft.TextAlign.RIGHT, color=ft.colors.BLUE_900)
            ]),
            ft.Row([
                ft.Text(f"Obra: {obra_cliente}", expand=True), 
                ft.Text(f"{cidade_cliente}", expand=True, text_align=ft.TextAlign.RIGHT)
            ]),
            ft.Row([
                ft.Text(f"Serviço: {servico_cliente}", expand=True), 
                ft.Text(f"{especificacao_cliente}", expand=True, text_align=ft.TextAlign.RIGHT)
            ]),
            ft.Divider(height=1, color=ft.colors.BLUE_GREY_200)
        ])
    )

    # --- CONDIÇÕES ---
    campo_data = ft.TextField(
        label="Data", value=data_atual, expand=1, read_only=True, 
        suffix=ft.IconButton(icon=ft.icons.CALENDAR_MONTH, on_click=lambda _: datepicker.pick_date())
    )
    campo_hora_inicio = ft.TextField(label="Início", hint_text="00:00", expand=1)
    campo_hora_fim = ft.TextField(label="Fim", hint_text="00:00", expand=1)
    dd_clima = ft.Dropdown(
        label="Clima", expand=1, 
        options=[ft.dropdown.Option(x) for x in ["Bom", "Chuva Leve", "Chuva Forte", "Vento"]]
    )
    dd_condicao_area = ft.Dropdown(
        label="Área", expand=1, on_change=mudar_condicao_area, 
        options=[ft.dropdown.Option(x) for x in ["Operável", "Inop. Parc.", "Inop. Total"]]
    )

    secao_condicoes_ui = ft.Container(
        padding=10, content=ft.Column(spacing=10, controls=[
            titulo_secao("Condições"),
            ft.Row([campo_data, campo_hora_inicio, campo_hora_fim], spacing=5), 
            ft.Row([dd_clima, dd_condicao_area], spacing=5), 
            campo_just_inoperante, 
            ft.Divider(height=1, color=ft.colors.BLUE_GREY_200)
        ])
    )

    # --- HISTOGRAMA (MÃO DE OBRA E EQUIPAMENTOS) ---
    func_labels = ["Engenheiro", "Analista de doc.", "Gerente téc.", "Supervisor téc.", "Téc. em imperm.", "Aux. téc. imperm.", "Aux. serv. gerais"]
    campos_funcionarios = [ft.TextField(label=f, value="", keyboard_type=ft.KeyboardType.NUMBER) for f in func_labels]
    
    equip_labels = ["Máquina cunha", "Extrusora", "Soprador", "Esmerilhadeira", "Gerador", "Teste de ar", "Holiday detector", "Tensiômetro", "Guilhotina", "Vácuo teste"]
    campos_equipamentos = [ft.TextField(label=e, value="", keyboard_type=ft.KeyboardType.NUMBER) for e in equip_labels]

    tubo_labels = ["Termofusão", "Eletrofusão", "Extrusora", "Alinhador"]
    campos_tubo = [ft.TextField(label=t, value="", keyboard_type=ft.KeyboardType.NUMBER) for t in tubo_labels]

    # --- PRODUÇÃO E ATIVIDADES ---
    campo_qtd_m2 = ft.TextField(label="Qtd. (m²)", dense=True, expand=1)
    campo_painel_larg = ft.TextField(label="Largura Bobina", dense=True, expand=1)
    campo_painel_comp = ft.TextField(label="Compr. Bobina", dense=True, expand=1)
    campo_manchao = ft.TextField(label="Manchão (Unid)", dense=True, expand=1)
    
    campo_canopla = ft.TextField(label="Canopla (Unid)", dense=True)
    campo_atividades = ft.TextField(label="Atividades Executadas", multiline=True, min_lines=5)

    # --- EVENTUALIDADES ---
    # --- SISTEMA DE DIÁRIA TÉCNICA (MODAL) ---
    input_dialog_just_diaria = ft.TextField(label="Justificativa (Obrigatório)", multiline=True, min_lines=3)
    input_dialog_obs_diaria = ft.TextField(label="Observação (Opcional)", multiline=True, min_lines=2)

    campo_just_diaria = ft.TextField(label="Justificativa da Diária", visible=False, expand=True, read_only=True, bgcolor=ft.colors.GREEN_50)
    campo_obs_diaria = ft.TextField(label="Observação da Diária", visible=False, expand=True, read_only=True, bgcolor=ft.colors.GREEN_50)

    def cancelar_diaria(e):
        chk_diaria_tecnica.value = False
        campo_just_diaria.visible = False
        campo_obs_diaria.visible = False
        campo_just_diaria.value = ""
        campo_obs_diaria.value = ""
        dialog_diaria.open = False
        btn_editar_diaria.visible = False
        page.update()

    def salvar_diaria(e):
        if not input_dialog_just_diaria.value.strip():
            input_dialog_just_diaria.error_text = "Preencha a justificativa!"
            page.update()
            return
        input_dialog_just_diaria.error_text = None
        campo_just_diaria.value = input_dialog_just_diaria.value
        campo_obs_diaria.value = input_dialog_obs_diaria.value
        campo_just_diaria.visible = True
        campo_obs_diaria.visible = True
        dialog_diaria.open = False
        btn_editar_diaria.visible = True
        page.update()

    dialog_diaria = ft.AlertDialog(
        modal=True,
        title=ft.Text("Detalhes da Diária Técnica", color=ft.colors.GREEN_700),
        content=ft.Column([input_dialog_just_diaria, input_dialog_obs_diaria], tight=True, spacing=10),
        actions=[
            ft.TextButton("Cancelar", on_click=cancelar_diaria),
            ft.ElevatedButton("Salvar Diária", on_click=salvar_diaria, bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE)
        ]
    )

    def abrir_modal_diaria(e=None):
        input_dialog_just_diaria.value = campo_just_diaria.value
        input_dialog_obs_diaria.value = campo_obs_diaria.value
        page.dialog = dialog_diaria
        dialog_diaria.open = True
        page.update()

    def mudar_diaria_tecnica(e):
        if e.control.value:
            abrir_modal_diaria()
        else:
            campo_just_diaria.visible = False
            campo_obs_diaria.visible = False
            campo_just_diaria.value = ""
            campo_obs_diaria.value = ""
            btn_editar_diaria.visible = False
            page.update()

    chk_diaria_tecnica = ft.Checkbox(label="Houve Diária Técnica?", on_change=mudar_diaria_tecnica)
    btn_editar_diaria = ft.IconButton(icon=ft.icons.EDIT, icon_color=ft.colors.BLUE_700, visible=False, tooltip="Editar Diária", on_click=abrir_modal_diaria)

    # --- FOTOS ---
    grid_fotos = ft.Row(wrap=True, spacing=10)
    arquivos_fotos_paths = []

    def fotos_selecionadas(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                if len(arquivos_fotos_paths) < 6:
                    arquivos_fotos_paths.append(f.path)
                    grid_fotos.controls.append(
                        ft.Container(
                            width=100, height=100, border_radius=5, 
                            border=ft.border.all(1, ft.colors.BLUE_GREY_200), 
                            image_src=f.path, image_fit=ft.ImageFit.COVER
                        )
                    )
            page.update()

    picker_fotos = ft.FilePicker(on_result=fotos_selecionadas)
    if picker_fotos not in page.overlay:
        page.overlay.append(picker_fotos)

   
    # ==========================================================
    # 4. CHAMADAS PARA SERVIÇOS EXTERNOS (PDF E VISÃO)
    # ==========================================================
    def gerar_pdf(rdo):
        gerar_pdf_oficial(rdo, contexto_pdf, page)

    def chamar_visao_profissional(rdo):
        exibir_visao_profissional(rdo, contexto_pdf, page, gerar_pdf)


    # ==========================================================
    # 5. LÓGICA DE AÇÃO (SALVAR, EDITAR, EXCLUIR, LIMPAR)
    # ==========================================================
    tabela_rdos = ft.Column(spacing=8)

    def renderizar_tabela():
        tabela_rdos.controls.clear()
        for rdo in rdos_dados:
            
            # 1. Pega o número e verifica a diária técnica (DT)
            num_rdo = f"RDO Nº {rdo.get('num', '000')}"
            mostra_dt = bool(rdo.get('diaria')) # Retorna True ou False
            
            # 2. Pega a data e a hora para a linha de baixo
            data_rdo = rdo.get('data', '')
            h_ini = rdo.get('h_ini', '')
            h_fim = rdo.get('h_fim', '')
            
            # Monta a string de horário (Ex: 08:00 - 17:00)
            str_horario = f"  |  {h_ini} ás {h_fim}" if h_ini or h_fim else ""
            subtitulo_rdo = f"{data_rdo}{str_horario}"

            tabela_rdos.controls.append(
                ft.Container(
                    padding=15, bgcolor=ft.colors.WHITE, border=ft.border.all(1, ft.colors.BLUE_GREY_100), border_radius=8,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column([
                                # Linha de cima (Agora separada para pintar o DT de vermelho)
                                ft.Row([
                                    ft.Text(num_rdo, weight="bold", size=16, color=ft.colors.BLUE_900),
                                    ft.Text("(DT)", weight="bold", size=16, color=ft.colors.RED_700, visible=mostra_dt),
                                ], spacing=5),
                                
                                # Linha de baixo (Menor, cinza, apenas Data e Horário)
                                ft.Text(subtitulo_rdo, color=ft.colors.GREY_600, size=13),
                            ], expand=True),
                            ft.Row(
                                spacing=5,
                                controls=[
                                    ft.IconButton(icon=ft.icons.VISIBILITY, tooltip="Visão Profissional", icon_color=ft.colors.BLUE, on_click=lambda e, r=rdo: chamar_visao_profissional(r)),
                                    ft.IconButton(icon=ft.icons.PICTURE_AS_PDF, tooltip="Gerar PDF", icon_color=ft.colors.RED_700, on_click=lambda e, r=rdo: gerar_pdf(r)),
                                    ft.IconButton(icon=ft.icons.EDIT, tooltip="Editar RDO", icon_color=ft.colors.ORANGE, on_click=lambda e, r=rdo: editar_rdo(r)),
                                    ft.IconButton(icon=ft.icons.DELETE, tooltip="Excluir RDO", icon_color=ft.colors.RED, on_click=lambda e, id=rdo['id']: confirmar_exclusao_rdo(id)),
                                ]
                            )
                        ]
                    )
                )
            )
        page.update()

    def voltar_para_historico(e):
        area_conteudo.content = layout_historico
        page.update()

    def limpar_formulario():
        campo_data.value = data_atual
        campo_hora_inicio.value = ""
        campo_hora_fim.value = ""
        
        dd_clima.value = None
        dd_condicao_area.value = None
        
        campo_just_inoperante.value = ""
        campo_just_inoperante.visible = False
        
        for f in campos_funcionarios: f.value = ""
        for e in campos_equipamentos: e.value = ""
        for t in campos_tubo: t.value = ""
        
        campo_qtd_m2.value = ""
        campo_painel_larg.value = ""
        campo_painel_comp.value = ""
        campo_manchao.value = ""
        campo_canopla.value = ""
        campo_atividades.value = ""
        
        chk_diaria_tecnica.value = False
        campo_just_diaria.value = ""
        campo_obs_diaria.value = ""
        campo_just_diaria.visible = False
        campo_obs_diaria.visible = False
        btn_editar_diaria.visible = False
        
        arquivos_fotos_paths.clear()
        grid_fotos.controls.clear()
        limpar_assinatura()

    def abrir_formulario_novo(e):
        estado_app["rdo_editando_id"] = None
        limpar_formulario()
        area_conteudo.content = layout_formulario
        page.update()

    def editar_rdo(rdo):
        estado_app["rdo_editando_id"] = rdo["id"]
        limpar_formulario()
        
        campo_data.value = rdo.get('data', '')
        campo_hora_inicio.value = rdo.get('h_ini', '')
        campo_hora_fim.value = rdo.get('h_fim', '')
        
        dd_clima.value = rdo.get('clima', None)
        dd_condicao_area.value = rdo.get('cond', None)
        
        campo_just_inoperante.value = rdo.get('just_inop', '')
        campo_just_inoperante.visible = (dd_condicao_area.value in ["Inop. Parc.", "Inop. Total"])
        
        funcs = rdo.get('func', [""]*len(func_labels))
        for i, f in enumerate(campos_funcionarios): f.value = funcs[i] if i < len(funcs) else ""
            
        equips = rdo.get('equip', [""]*len(equip_labels))
        for i, eq in enumerate(campos_equipamentos): eq.value = equips[i] if i < len(equips) else ""

        tubos = rdo.get('tubo', [""]*len(tubo_labels))
        for i, tb in enumerate(campos_tubo): tb.value = tubos[i] if i < len(tubos) else ""
            
        campo_qtd_m2.value = rdo.get('qtd', '')
        campo_painel_larg.value = rdo.get('p_larg', '')
        campo_painel_comp.value = rdo.get('p_comp', '')
        campo_manchao.value = rdo.get('manchao', '')
        campo_canopla.value = rdo.get('canopla', '')
        campo_atividades.value = rdo.get('atv', '')
        
        chk_diaria_tecnica.value = rdo.get('diaria', False)
        campo_just_diaria.value = rdo.get('just_d', '')
        campo_obs_diaria.value = rdo.get('obs_d', '')
        campo_just_diaria.visible = chk_diaria_tecnica.value
        campo_obs_diaria.visible = chk_diaria_tecnica.value
        btn_editar_diaria.visible = chk_diaria_tecnica.value

        for caminho in rdo.get('fotos', []):
            if os.path.exists(caminho):
                arquivos_fotos_paths.append(caminho)
                grid_fotos.controls.append(
                    ft.Container(
                        width=100, height=100, border_radius=5, 
                        border=ft.border.all(1, ft.colors.BLUE_GREY_200), 
                        image_src=caminho, image_fit=ft.ImageFit.COVER
                    )
                )

        ass_data = rdo.get('assinatura', {})
        if ass_data and isinstance(ass_data, dict):
            estado_app["ass"]["tipo"] = ass_data.get("tipo")
            estado_app["ass"]["valor"] = ass_data.get("valor")
            if estado_app["ass"]["tipo"] == "texto":
                input_ass_texto.value = estado_app["ass"]["valor"]
                texto_feedback_assinatura.value = f"Assinado por: {input_ass_texto.value}"
                texto_feedback_assinatura.color = ft.colors.GREEN_700
                abas_assinatura.selected_index = 0
            elif estado_app["ass"]["tipo"] == "imagem" and os.path.exists(estado_app["ass"]["valor"]):
                ass_imagem_caminho[0] = estado_app["ass"]["valor"]
                img_ass_preview.src = estado_app["ass"]["valor"]
                img_ass_preview.visible = True
                texto_feedback_assinatura.value = "Imagem anexada com sucesso."
                texto_feedback_assinatura.color = ft.colors.GREEN_700
                abas_assinatura.selected_index = 2

        area_conteudo.content = layout_formulario
        page.update()

    def salvar_rdo_banco(e):
        if chk_diaria_tecnica.value and not campo_just_diaria.value.strip():
            exibir_aviso("Preencha a Justificativa da Diária Técnica.", ft.colors.RED)
            return

        if dd_condicao_area.value in ["Inop. Parc.", "Inop. Total"] and not campo_just_inoperante.value.strip():
            exibir_aviso("Atenção: Área inoperante requer justificativa obrigatória!", ft.colors.RED_700)
            return
        
        # BLINDAGEM DE FOTOS
        fotos_salvas_definitivas = []
        for caminho_original in arquivos_fotos_paths:
            if caminho_original.startswith(PASTA_FOTOS_RDO):
                fotos_salvas_definitivas.append(caminho_original)
            else:
                if os.path.exists(caminho_original):
                    ext = os.path.splitext(caminho_original)[1]
                    novo_nome = f"foto_rdo_cli{cliente_id}_{int(time.time()*1000)}_{len(fotos_salvas_definitivas)}{ext}"
                    caminho_destino = os.path.join(PASTA_FOTOS_RDO, novo_nome)
                    shutil.copy(caminho_original, caminho_destino)
                    fotos_salvas_definitivas.append(caminho_destino)

        # BLINDAGEM DE ASSINATURA
        assinatura_final = {"tipo": None, "valor": None}
        if estado_app["ass"]["tipo"] == "texto":
            assinatura_final = {"tipo": "texto", "valor": estado_app["ass"]["valor"]}
        elif estado_app["ass"]["tipo"] == "imagem" and estado_app["ass"]["valor"]:
            caminho_original = estado_app["ass"]["valor"]
            if caminho_original.startswith(PASTA_ASSINATURAS):
                assinatura_final = {"tipo": "imagem", "valor": caminho_original}
            else:
                if os.path.exists(caminho_original):
                    ext = os.path.splitext(caminho_original)[1]
                    novo_nome = f"ass_cli{cliente_id}_{int(time.time()*1000)}{ext}"
                    caminho_destino = os.path.join(PASTA_ASSINATURAS, novo_nome)
                    shutil.copy(caminho_original, caminho_destino)
                    assinatura_final = {"tipo": "imagem", "valor": caminho_destino}

        dados_salvar = {
            "os": os_cliente, "cidade": cidade_cliente, "espec": especificacao_cliente,
            "data": campo_data.value, "h_ini": campo_hora_inicio.value, "h_fim": campo_hora_fim.value,
            "clima": dd_clima.value, "cond": dd_condicao_area.value, "just_inop": campo_just_inoperante.value,
            "func": [f.value for f in campos_funcionarios], 
            "equip": [eq.value for eq in campos_equipamentos], 
            "tubo": [tb.value for tb in campos_tubo],
            "qtd": campo_qtd_m2.value, "p_larg": campo_painel_larg.value, "p_comp": campo_painel_comp.value,
            "manchao": campo_manchao.value, "canopla": campo_canopla.value, "atv": campo_atividades.value,
            "diaria": chk_diaria_tecnica.value, "just_d": campo_just_diaria.value, "obs_d": campo_obs_diaria.value,
            "fotos": fotos_salvas_definitivas,
            "assinatura": assinatura_final
        }

        if estado_app["rdo_editando_id"] is not None:
            for rdo in rdos_dados:
                if rdo["id"] == estado_app["rdo_editando_id"]:
                    rdo.update(dados_salvar)
                    break
            msg_aviso = "RDO Editado com sucesso!"
            cor_aviso = ft.colors.ORANGE_800
        else:
            dados_salvar["id"] = int(datetime.now().timestamp())
            rdos_dados.insert(0, dados_salvar)
            msg_aviso = "RDO Criado com sucesso!"
            cor_aviso = ft.colors.GREEN_700
            
        atualizar_numeracao() 
        renderizar_tabela()
        
        # VOLTA PARA A TELA INICIAL PRIMEIRO
        voltar_para_historico(e)
        
        # DEPOIS MOSTRA O AVISO
        exibir_aviso(msg_aviso, cor_aviso)

    def confirmar_exclusao_rdo(id_rdo):
        def fechar_dialog_inicial(e):
            dialog_inicial.open = False
            page.update()

        def fechar_dialog_final(e):
            dialog_final.open = False
            page.update()

        def abrir_confirmacao_final(e):
            dialog_inicial.open = False 
            if dialog_final not in page.overlay:
                page.overlay.append(dialog_final)
            dialog_final.open = True 
            page.update()

        def executar_exclusao_final(e):
            dialog_final.open = False
            page.update()

            for i, rdo in enumerate(rdos_dados):
                if rdo["id"] == id_rdo:
                    # Deletar fotos
                    for foto in rdo.get("fotos", []):
                        if os.path.exists(foto):
                            try: os.remove(foto)
                            except: pass
                    
                    # Deletar assinatura se for imagem
                    ass = rdo.get("assinatura", {})
                    if ass and ass.get("tipo") == "imagem" and ass.get("valor"):
                        if os.path.exists(ass["valor"]):
                            try: os.remove(ass["valor"])
                            except: pass
                    
                    del rdos_dados[i]
                    break
            
            atualizar_numeracao()
            renderizar_tabela()
            exibir_aviso("RDO e anexos excluídos permanentemente!", ft.colors.GREEN_700)

        # Janela Final (Vermelha)
        dialog_final = ft.AlertDialog(
            modal=True, 
            title=ft.Text("Confirmação Final", color=ft.colors.RED_700),
            content=ft.Text("O RDO será apagado juntamente com as fotos e assinatura.\nEsta ação é irreversível. Deseja Realmente excluir?"),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dialog_final), 
                ft.ElevatedButton("Sim, Excluir", bgcolor=ft.colors.RED_700, color=ft.colors.WHITE, on_click=executar_exclusao_final)
            ]
        )

        # Janela Inicial (Laranja)
        dialog_inicial = ft.AlertDialog(
            modal=True, 
            title=ft.Text("Atenção", color=ft.colors.ORANGE_800),
            content=ft.Text("Deseja iniciar a exclusão deste RDO?"),
            actions=[
                ft.TextButton("Cancelar", on_click=fechar_dialog_inicial), 
                ft.ElevatedButton("Sim, Continuar", bgcolor=ft.colors.ORANGE_800, color=ft.colors.WHITE, on_click=abrir_confirmacao_final)
            ]
        )
        
        if dialog_inicial not in page.overlay:
            page.overlay.append(dialog_inicial)
        dialog_inicial.open = True
        page.update()


    # ==========================================================
    # 6. MONTAGEM DAS TELAS E NAVEGAÇÃO (ARQUITETURA FINAL MOBILE)
    # ==========================================================
    
    layout_formulario = ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            expand=True,
            scroll=ft.ScrollMode.AUTO, spacing=20,
            controls=[
                # Botão Voltar
                ft.Row([
                    ft.Text("Novo (RDO)", size=22, weight="bold", color=ft.colors.BLUE_900),
                    ft.ElevatedButton("Voltar", icon=ft.icons.ARROW_BACK, on_click=voltar_para_historico, color=ft.colors.BLUE_GREY_700)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                
                cabecalho_cliente_ui,
                secao_condicoes_ui,
                
                # MÃO DE OBRA E EQUIPAMENTOS
                ft.Container(
                    padding=15, border=ft.border.all(1, ft.colors.GREY_300), border_radius=8,
                    content=ft.Column(spacing=15, controls=[
                        titulo_secao("Mão de Obra"),
                        ft.Column(campos_funcionarios),
                        
                        titulo_secao("Equipamento Solda Geomembrana"),
                        ft.Column(campos_equipamentos),
                        
                        titulo_secao("Equipamento Solda Tubo"),
                        ft.Column(campos_tubo)
                    ])
                ),
                
                # DESCRIÇÃO TÉCNICA E PRODUÇÃO
                ft.Container(
                    padding=15, border=ft.border.all(1, ft.colors.GREY_300), border_radius=8, 
                    content=ft.Column(spacing=15, controls=[
                        titulo_secao("Produção e Descrição Técnica"),
                        ft.Row([campo_qtd_m2, campo_painel_larg]),
                        ft.Row([campo_painel_comp, campo_manchao]),
                        campo_canopla,
                        campo_atividades
                    ])
                ),
                
                # EVENTUALIDADES E DIÁRIA
                ft.Container(padding=15, border=ft.border.all(1, ft.colors.GREY_300), border_radius=8, content=ft.Column(spacing=15, controls=[titulo_secao("Diária e Eventualidades"), ft.Row([chk_diaria_tecnica, btn_editar_diaria]), ft.Row([campo_just_diaria, campo_obs_diaria])])),
                
                # ASSINATURA
                ft.Container(
                    padding=15, border=ft.border.all(1, ft.colors.GREY_300), border_radius=8, 
                    content=ft.Column(spacing=15, controls=[
                        titulo_secao("Assinatura do Responsável"), 
                        ft.Row([
                            ft.ElevatedButton("Assinar Documento", icon=ft.icons.DRAW, on_click=abrir_modal_assinatura, bgcolor=ft.colors.BLUE_800, color=ft.colors.WHITE),
                            ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED, tooltip="Remover Assinatura", on_click=lambda _: limpar_assinatura())
                        ]),
                        texto_feedback_assinatura
                    ])
                ),

                # REGISTRO FOTOGRÁFICO
                ft.Container(
                    padding=15, border=ft.border.all(1, ft.colors.GREY_300), border_radius=8, 
                    content=ft.Column(spacing=15, controls=[
                        titulo_secao("Registro Fotográfico (Máx. 6)"), 
                        ft.ElevatedButton("Anexar Fotos", icon=ft.icons.ADD_A_PHOTO, on_click=lambda _: picker_fotos.pick_files(allow_multiple=True, file_type=ft.FilePickerFileType.IMAGE)), 
                        grid_fotos
                    ])
                ),
                
                # BOTÕES DE SALVAR
                ft.Row([
                    ft.ElevatedButton("Cancelar", icon=ft.icons.CANCEL, on_click=voltar_para_historico, color=ft.colors.RED), 
                    ft.ElevatedButton("Salvar RDO", icon=ft.icons.SAVE, on_click=salvar_rdo_banco, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]
        )
    )

    layout_historico = ft.Container(
        padding=20,
        content=ft.Column([
            ft.Row([
                ft.ElevatedButton("Novo RDO", icon=ft.icons.ADD, bgcolor=ft.colors.BLUE_800, color=ft.colors.WHITE, on_click=abrir_formulario_novo)
            ], alignment=ft.MainAxisAlignment.END),
            
            ft.Row([
                ft.Text("Histórico de RDOs", size=22, weight="bold", width=200), 
                ft.Container(content=ft.TextField(hint_text="Pesquisar...", prefix_icon=ft.icons.SEARCH, height=45), expand=True, padding=ft.padding.symmetric(horizontal=20))
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Divider(),
            
            ft.Container(padding=10, bgcolor=ft.colors.BLUE_GREY_50, border_radius=10, content=tabela_rdos)
        ])
    )
    
    area_conteudo = ft.Container(content=layout_historico, expand=True)
    renderizar_tabela()

    return ft.Container(
        expand=True,
        padding=ft.padding.only(top=40),
        content=ft.Column(expand=True, controls=[
            ft.Container(
                bgcolor=ft.colors.BLUE_GREY_800, 
                padding=15, 
                content=ft.Row([
                    ft.IconButton(icon=ft.icons.HOME, icon_color=ft.colors.WHITE, tooltip="Voltar para Início", on_click=lambda e: page.go("/")),
                    ft.Text(f"RDO - {nome_cliente}", size=18, weight="bold", color=ft.colors.WHITE)
                ])
            ),
            area_conteudo
        ])
    )