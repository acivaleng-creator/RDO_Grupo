import flet as ft
import os

def exibir_visao_profissional(rdo, contexto, page: ft.Page, callback_gerar_pdf):
    cor_verde = "#D4FCBB"
    cor_azul = "#CDE3F7"
    cor_amarela = "#F9F989"

    # LOGO DO CLIENTE/EMPRESA
    caminho_logo = os.path.abspath(os.path.join(contexto['pasta_ativos'], contexto['logo_src'])) if contexto['logo_src'] else ""
    if os.path.exists(caminho_logo):
        elemento_logo = ft.Image(src=caminho_logo, width=120, height=45, fit=ft.ImageFit.CONTAIN)
    else:
        elemento_logo = ft.Icon(ft.icons.BUSINESS, size=45, color=ft.colors.BLUE_900)

    # FUNÇÃO DE CÉLULA GRADEADA
    def cel(texto, flex=1, bold=False, bg=None, center=False, tamanho=8.5, border_bottom=True, border_right=True, border_top=True, border_left=True):
        b_top = ft.border.BorderSide(1, ft.colors.BLACK) if border_top else ft.border.BorderSide(0, ft.colors.TRANSPARENT)
        b_right = ft.border.BorderSide(1, ft.colors.BLACK) if border_right else ft.border.BorderSide(0, ft.colors.TRANSPARENT)
        b_bottom = ft.border.BorderSide(1, ft.colors.BLACK) if border_bottom else ft.border.BorderSide(0, ft.colors.TRANSPARENT)
        b_left = ft.border.BorderSide(1, ft.colors.BLACK) if border_left else ft.border.BorderSide(0, ft.colors.TRANSPARENT)
        
        return ft.Container(
            content=ft.Text(texto, weight="bold" if bold else "normal", size=tamanho, color=ft.colors.BLACK, text_align="center" if center else "left"),
            expand=flex, bgcolor=bg, padding=ft.padding.all(4),
            border=ft.border.Border(top=b_top, right=b_right, bottom=b_bottom, left=b_left),
            alignment=ft.alignment.center if center else ft.alignment.center_left
        )

    h_ini = rdo.get('h_ini','')
    h_fim = rdo.get('h_fim','')
    horario = f"{h_ini} ÁS {h_fim}" if h_ini else ""

    # BLOCO 1 - CABEÇALHO
    b1_esq = ft.Column(spacing=0, expand=6, controls=[
        ft.Row(spacing=0, controls=[cel("CLIENTE:", 2, True), cel(contexto['nome_cliente'], 8)]),
        ft.Row(spacing=0, controls=[cel("OBRA:", 2, True), cel(contexto['obra_cliente'], 8)]),
        ft.Row(spacing=0, controls=[cel("CIDADE:", 2, True), cel(rdo.get('cidade', contexto['cidade_cliente']), 8)]),
        ft.Row(spacing=0, controls=[cel("SERVIÇO:", 2, True), cel(f"{contexto['servico_cliente']} | Espec: {rdo.get('espec', contexto['especificacao_cliente'])}", 8)]),
    ])
    b1_dir = ft.Column(spacing=0, expand=4, controls=[
        ft.Row(spacing=0, controls=[cel("RDO Nº:", 4, True), cel(rdo.get('num', '000'), 6, center=True)]),
        ft.Row(spacing=0, controls=[cel("ORDEM DE SERVIÇO:", 4, True), cel(rdo.get('os', contexto['os_cliente']), 6, center=True)]),
        ft.Row(spacing=0, controls=[cel("Data:", 4, True), cel(rdo.get('data', ''), 6, center=True)]),
        ft.Row(spacing=0, controls=[cel("Hora:", 4, True), cel(horario, 6, center=True)]),
    ])
    b1 = ft.Row(spacing=10, controls=[b1_esq, b1_dir])

    # BLOCO 2 - CONDIÇÕES CLIMÁTICAS E ÁREA
    clima = rdo.get('clima', '')
    cond = rdo.get('cond', '')
    x_bom = 'X' if clima == 'Bom' else ''
    x_chuva_l = 'X' if clima == 'Chuva Leve' else ''
    x_chuva_f = 'X' if clima == 'Chuva Forte' else ''
    x_vento = 'X' if clima == 'Vento' else ''
    x_op = 'X' if cond == 'Operável' else ''
    x_parc = 'X' if cond == 'Inop. Parc.' else ''
    x_inop = 'X' if cond == 'Inop. Total' else ''

    b2_tempo = ft.Column(spacing=0, expand=4, controls=[
        ft.Row(spacing=0, controls=[cel("CONDIÇÕES DO TEMPO", 1, True, cor_verde, True)]),
        ft.Row(spacing=0, controls=[cel("BOM", 1, center=True, tamanho=7), cel("CHUVA LEVE", 1, center=True, tamanho=7), cel("CHUVA FORTE", 1, center=True, tamanho=7), cel("VENTO", 1, center=True, tamanho=7)]),
        ft.Row(spacing=0, controls=[cel(x_bom, 1, center=True), cel(x_chuva_l, 1, center=True), cel(x_chuva_f, 1, center=True), cel(x_vento, 1, center=True)]),
    ])
    b2_area = ft.Column(spacing=0, expand=5, controls=[
        ft.Row(spacing=0, controls=[cel("CONDIÇÕES DA ÁREA", 1, True, cor_verde, True)]),
        ft.Row(spacing=0, controls=[cel("OPERÁVEL", 2, center=True, tamanho=7), cel("INOP. PARC.", 2, center=True, tamanho=7), cel("INOP. TOTAL", 2, center=True, tamanho=7), cel("JUSTIFICATIVA", 3, center=True, tamanho=7)]),
        ft.Row(spacing=0, controls=[cel(x_op, 2, center=True), cel(x_parc, 2, center=True), cel(x_inop, 2, center=True), cel(rdo.get('just_inop',''), 3, center=False)]),
    ])
    b2 = ft.Row(spacing=10, controls=[b2_tempo, b2_area])

    # BLOCO 3 - HISTOGRAMA (MÃO DE OBRA E EQUIPAMENTOS)
    funcs_salvas = rdo.get('func', [""]*10)
    equips_salvos = rdo.get('equip', [""]*10)
    tubos_salvos = rdo.get('tubo', [""]*10)

    func_labels = ["Engenheiro", "Analista de doc.", "Gerente téc.", "Supervisor téc.", "Téc. em imperm.", "Aux. téc. imperm.", "Aux. serv. gerais"]
    equip_labels = ["Máquina cunha", "Extrusora", "Soprador", "Esmerilhadeira", "Gerador", "Teste de ar", "Holiday detector", "Tensiômetro", "Guilhotina", "Vácuo teste"]
    tubo_labels = ["Termofusão", "Eletrofusão", "Extrusora", "Alinhador"]

    def make_hist_col(titulo, labels, vals):
        rows = [ft.Row(spacing=0, controls=[cel(titulo, 1, True, cor_azul, True)])]
        for i in range(10):
            l = labels[i] if i < len(labels) else ""
            v = vals[i] if i < len(vals) else ""
            rows.append(ft.Row(spacing=0, controls=[cel(l, 4, tamanho=7.5), cel(v, 1, center=True, tamanho=7.5)]))
        return ft.Column(spacing=0, expand=1, controls=rows)

    b3 = ft.Row(spacing=10, controls=[
        make_hist_col("MÃO DE OBRA", func_labels, funcs_salvas),
        make_hist_col("EQUIP. SOLDA GEO.", equip_labels, equips_salvos),
        make_hist_col("EQUIP. SOLDA TUBO", tubo_labels, tubos_salvos)
    ])

    # BLOCO 4 - PRODUÇÃO E ATIVIDADES
    larg = rdo.get('p_larg','')
    comp = rdo.get('p_comp','')
    bobina = f"{larg} x {comp}" if larg and comp else ""
    
    b4_app = ft.Column(spacing=0, expand=4, controls=[
        ft.Row(spacing=0, controls=[cel("APLICAÇÃO", 1, True, cor_amarela, True)]),
        ft.Row(spacing=0, controls=[cel("TOTAL APLICADO:", 2, True), cel(f"{rdo.get('qtd','')} m²", 2, center=True)]),
        ft.Row(spacing=0, controls=[cel("BOBINA (L x C):", 2, True), cel(bobina, 2, center=True)]),
        ft.Row(spacing=0, controls=[cel("MANCHÃO (UNID):", 2, True), cel(rdo.get('manchao',''), 2, center=True)]),
        ft.Row(spacing=0, controls=[cel("CANOPLA (UNID):", 2, True), cel(rdo.get('canopla',''), 2, center=True)]),
    ])
    
    texto_atv = rdo.get('atv','')
    b4_atv = ft.Column(spacing=0, expand=6, controls=[
        ft.Row(spacing=0, controls=[cel("DESCRIÇÃO DAS ATIVIDADES", 1, True, cor_amarela, True)]),
        cel(texto_atv, 1)
    ])
    b4 = ft.Row(spacing=10, height=130, controls=[b4_app, b4_atv]) 

    # BLOCO 5 - EVENTUALIDADES E DIÁRIA TÉCNICA
    chk = '[ X ]' if rdo.get('diaria') else '[   ]'
    just_text = rdo.get('just_d', '').strip()
    obs_text = rdo.get('obs_d', '').strip()

    b5 = ft.Container(
        border=ft.border.all(1, ft.colors.BLACK),
        content=ft.Column(spacing=0, controls=[
            ft.Container(bgcolor=cor_verde, border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.BLACK)), padding=4, width=float('inf'), alignment=ft.alignment.center, content=ft.Text("EVENTUALIDADES / CONSIDERAÇÕES TÉCNICAS", weight="bold", size=9, color=ft.colors.BLACK)),
            ft.Container(bgcolor=ft.colors.WHITE, padding=10, content=ft.Column(spacing=0, controls=[
                ft.Row(controls=[
                    ft.Text(f"DIÁRIA TÉCNICA: {chk}", size=9, color=ft.colors.BLACK, weight="bold"), 
                    ft.Row(spacing=5, controls=[ft.Text("JUSTIFICATIVA:", size=9, color=ft.colors.BLACK, weight="bold"), ft.Text(just_text, size=9, color=ft.colors.BLACK)])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=15, color=ft.colors.GREY_500),
                ft.Row(spacing=5, controls=[ft.Text("OBSERVAÇÃO:", size=9, color=ft.colors.BLACK, weight="bold"), ft.Text(obs_text, size=9, color=ft.colors.BLACK)]),
                ft.Divider(height=15, color=ft.colors.GREY_500),
                ft.Container(height=20, border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_400))),
                ft.Container(height=20, border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_400))),
                ft.Container(height=20, border=ft.border.only(bottom=ft.border.BorderSide(1, ft.colors.GREY_400))),
            ]))
        ])
    )

    # BLOCO 6 - ASSINATURAS (ATUALIZADO COM LÓGICA DE ASSINATURA)
    nome_empresa_str = "EMPRESA"
    if contexto['empresa']:
        if isinstance(contexto['empresa'], dict) and "nome" in contexto['empresa']:
            nome_empresa_str = contexto['empresa']["nome"].upper()
        elif isinstance(contexto['empresa'], (tuple, list)) and len(contexto['empresa']) > 1:
            nome_empresa_str = str(contexto['empresa'][1]).upper()

    # --- LÓGICA DE EXIBIÇÃO DA ASSINATURA ---
    ass_data = rdo.get('assinatura', {})
    elemento_assinatura = ft.Container(height=40) # Espaço em branco padrão
    
    if ass_data and isinstance(ass_data, dict):
        if ass_data.get("tipo") == "texto":
            # Pega o nome limpo e formata como itálico azul
            texto_limpo = ass_data.get("valor", "")
            elemento_assinatura = ft.Text(texto_limpo, italic=True, size=18, color=ft.colors.BLUE_900)
        elif ass_data.get("tipo") == "imagem" and os.path.exists(ass_data.get("valor", "")):
            # Puxa a imagem do arquivo
            elemento_assinatura = ft.Image(src=ass_data.get("valor"), height=40, fit=ft.ImageFit.CONTAIN)

    b6_esq = ft.Column(expand=1, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
        elemento_assinatura, # A assinatura entra aqui, flutuando sobre a linha
        ft.Text("____________________________________________", color=ft.colors.BLACK, weight="bold"),
        ft.Text(f"RESPONSÁVEL / {nome_empresa_str}", color=ft.colors.BLACK, size=10, weight="bold"),
        ft.Text(f"Data: {rdo.get('data', '')}", color=ft.colors.BLACK, size=10)
    ])

    b6_dir = ft.Column(expand=1, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
        ft.Container(height=40), # Espaço vazio do lado do cliente
        ft.Text("____________________________________________", color=ft.colors.BLACK, weight="bold"),
        ft.Text("CLIENTE", color=ft.colors.BLACK, size=10, weight="bold"),
        ft.Text("Data: _____ / _____ / _______", color=ft.colors.BLACK, size=10)
    ])
    b6 = ft.Row(spacing=20, controls=[b6_esq, b6_dir], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # BLOCO 7 - FOTOS
    grade_fotos_ui = ft.Row(wrap=True, spacing=10, alignment=ft.MainAxisAlignment.CENTER)
    for foto in rdo.get("fotos", [])[:6]:
        if os.path.exists(foto):
            grade_fotos_ui.controls.append(ft.Image(src=foto, width=200, height=150, fit=ft.ImageFit.COVER, border_radius=8))

    # CONSTRUÇÃO DO MODAL A4
    conteudo_a4 = ft.Container(
        width=900, height=800, padding=20, bgcolor=ft.colors.WHITE, border=ft.border.all(1, ft.colors.GREY_400), border_radius=8,
        content=ft.Column(
            scroll=ft.ScrollMode.AUTO, spacing=12,
            controls=[
                ft.Row([elemento_logo, ft.Text("RELATÓRIO DIÁRIO DE OBRA - RDO", weight="bold", size=18, color=ft.colors.BLACK)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(color=ft.colors.BLACK, thickness=2, height=1),
                b1, b2, b3, b4, b5, 
                ft.Container(height=30),
                b6,
                ft.Divider(color=ft.colors.BLACK, thickness=2, height=30) if grade_fotos_ui.controls else ft.Container(),
                ft.Text("REGISTRO FOTOGRÁFICO", weight="bold", size=14, color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER) if grade_fotos_ui.controls else ft.Container(),
                grade_fotos_ui
            ]
        )
    )
    
    def fechar_visao_e_dialog(e):
        dialog_visao.open = False
        page.update()
        
    dialog_visao = ft.AlertDialog(
        modal=True, 
        title=ft.Text("Visão Profissional (Simulação de Impressão)", weight="bold"), 
        content=conteudo_a4, 
        actions_padding=15, 
        actions=[
            ft.OutlinedButton("Voltar", on_click=fechar_visao_e_dialog), 
            ft.ElevatedButton("Gerar PDF Oficial", icon=ft.icons.PICTURE_AS_PDF, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE, on_click=lambda e: callback_gerar_pdf(rdo))
        ]
    )
    
    page.dialog = dialog_visao
    dialog_visao.open = True
    page.update()