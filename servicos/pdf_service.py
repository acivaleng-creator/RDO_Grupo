import sys
import os
import flet as ft
from datetime import datetime

def gerar_pdf_oficial(rdo, contexto, page: ft.Page):
    """
    Gera o PDF do RDO.
    O 'contexto' é um dicionário com os dados externos (cliente, empresa, pastas).
    """
    try:
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Image,
            Table, TableStyle, PageBreak
        )
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus.flowables import HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    except ImportError:
        page.snack_bar = ft.SnackBar(ft.Text("Instale: pip install reportlab", color=ft.colors.WHITE), bgcolor=ft.colors.RED)
        page.snack_bar.open = True
        page.update()
        return

    # DEFINIÇÃO DAS CORES
    cor_verde_claro = colors.HexColor("#D4FCBB") 
    cor_azul_claro = colors.HexColor("#CDE3F7") 
    cor_amarelo = colors.HexColor("#F9F989")   
    cor_borda = colors.black

    nomes_mao_de_obra = ["Engenheiro", "Analista de doc.", "Gerente téc.", "Supervisor téc.", "Téc. em imperm.", "Aux. téc. imperm.", "Aux. serv. gerais"]
    nomes_equip_geo = ["Máquina cunha", "Extrusora", "Soprador", "Esmerilhadeira", "Gerador", "Teste de ar", "Holiday detector", "Tensiômetro", "Guilhotina", "Vácuo teste"]
    nomes_equip_tubo = ["Termofusão", "Eletrofusão", "Extrusora", "Alinhador",]

    # BLINDAGEM DA PASTA DO PDF
    pasta_pdfs = os.path.join(contexto['diretorio_raiz'], "pdfs")
    if not os.path.exists(pasta_pdfs):
        os.makedirs(pasta_pdfs)

    data_bruta = rdo.get('data', '00/00/0000')
    try:
        data_formatada = datetime.strptime(data_bruta, "%d/%m/%Y").strftime("%d-%m-%y")
    except ValueError:
        data_formatada = data_bruta.replace('/', '-')

    numero_rdo = rdo.get('num', '000')
    nome_arquivo = f"RDO_{numero_rdo}_{data_formatada}_{contexto['nome_cliente']}.pdf"
    caminho_completo = os.path.join(pasta_pdfs, nome_arquivo)

    doc = SimpleDocTemplate(
        caminho_completo,
        pagesize=A4, 
        topMargin=15*mm, leftMargin=17.5*mm, rightMargin=15*mm, bottomMargin=12.5*mm
    )

    elementos = []
    estilos = getSampleStyleSheet()

    style_title = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=12, alignment=TA_RIGHT)
    style_label = ParagraphStyle('Label', fontName='Helvetica-Bold', fontSize=8, textColor=colors.black)
    style_val = ParagraphStyle('Val', fontName='Helvetica', fontSize=8, textColor=colors.black)
    
    style_center_mini_bold = ParagraphStyle('CenterMiniBold', fontName='Helvetica-Bold', fontSize=6.5, alignment=TA_CENTER)
    style_center_bold = ParagraphStyle('CenterBold', fontName='Helvetica-Bold', fontSize=8, alignment=TA_CENTER)
    style_center_val = ParagraphStyle('CenterVal', fontName='Helvetica', fontSize=8, alignment=TA_CENTER)
    
    # BLINDAGEM DA LOGO NO PDF
    caminho_logo = os.path.abspath(os.path.join(contexto['pasta_ativos'], contexto['logo_src'])) if contexto['logo_src'] else ""
    logo_flowable = ""
    if os.path.exists(caminho_logo):
        try: 
            logo_flowable = Image(caminho_logo, width=45*mm, height=15*mm)
            logo_flowable.hAlign = 'LEFT'
        except: pass
        
    t_header = Table([[logo_flowable, Paragraph("RELATÓRIO DIÁRIO DE OBRA - RDO", style_title)]], colWidths=[50*mm, 127.5*mm])
    t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    elementos.append(t_header)
    elementos.append(HRFlowable(width=177.5*mm, thickness=1.5, color=colors.black, spaceBefore=3, spaceAfter=4))

    # TABELA DA ESQUERDA
    t_info_esq_data = [
        [Paragraph("CLIENTE:", style_label), Paragraph(contexto['nome_cliente'], style_val)],
        [Paragraph("OBRA:", style_label), Paragraph(contexto['obra_cliente'], style_val)],
        [Paragraph("CIDADE:", style_label), Paragraph(rdo.get('cidade', contexto['cidade_cliente']), style_val)],
        [Paragraph("SERVIÇO:", style_label), Paragraph(f"{contexto['servico_cliente']} | Espec: {rdo.get('espec', contexto['especificacao_cliente'])}", style_val)]
    ]
    t_info_esq = Table(t_info_esq_data, colWidths=[20*mm, 90*mm])
    t_info_esq.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, cor_borda), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))

    # DADOS DA HORA
    h_ini = rdo.get('h_ini','')
    h_fim = rdo.get('h_fim','')
    horario = f"{h_ini} ÁS {h_fim}" if h_ini else ""
    
    # TABELA DA DIREITA
    t_info_dir_data = [
        [Paragraph("RDO Nº:", style_label), Paragraph(numero_rdo, style_center_val)],
        [Paragraph("ORDEM DE SERVIÇO:", style_label), Paragraph(rdo.get('os', contexto['os_cliente']), style_center_val)],
        [Paragraph("Data:", style_label), Paragraph(data_bruta, style_center_val)],
        [Paragraph("Hora:", style_label), Paragraph(horario, style_center_val)]
    ]
    t_info_dir = Table(t_info_dir_data, colWidths=[35*mm, 25*mm])
    t_info_dir.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, cor_borda), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))

    # BLOCO 1
    t_block_1 = Table([[t_info_esq, '', t_info_dir]], colWidths=[110*mm, 7.5*mm, 60*mm])
    t_block_1.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'), 
        ('LEFTPADDING', (0,0), (-1,-1), 0), 
        ('RIGHTPADDING', (0,0), (-1,-1), 0)
    ]))
    elementos.append(t_block_1)
    elementos.append(Spacer(1, 4))

    clima = rdo.get('clima', '')
    cond = rdo.get('cond', '')
    
    x_bom = 'X' if clima == 'Bom' else ''
    x_chuva_l = 'X' if clima == 'Chuva Leve' else ''
    x_chuva_f = 'X' if clima == 'Chuva Forte' else ''
    x_vento = 'X' if clima == 'Vento' else ''
    
    x_op = 'X' if cond == 'Operável' else ''
    x_parc = 'X' if cond == 'Inop. Parc.' else ''
    x_inop = 'X' if cond == 'Inop. Total' else ''

    t_tempo_data = [
        [Paragraph("CONDIÇÕES DO TEMPO", style_center_bold), '', '', ''],
        [Paragraph("BOM", style_center_val), Paragraph("CHUVA LEVE", style_center_val), Paragraph("CHUVA FORTE", style_center_val), Paragraph("VENTO", style_center_val)],
        [Paragraph(x_bom, style_center_val), Paragraph(x_chuva_l, style_center_val), Paragraph(x_chuva_f, style_center_val), Paragraph(x_vento, style_center_val)]
    ]
    t_tempo = Table(t_tempo_data, colWidths=[16*mm, 23*mm, 25*mm, 16*mm], rowHeights=[6*mm, 6*mm, 6*mm])
    t_tempo.setStyle(TableStyle([('SPAN', (0,0), (3,0)), ('BACKGROUND', (0,0), (3,0), cor_verde_claro), ('GRID', (0,0), (-1,-1), 1, cor_borda), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))

    t_area_data = [
        [Paragraph("CONDIÇÕES DA ÁREA", style_center_bold), '', '', ''],
        [Paragraph("OPERÁVEL", style_center_mini_bold), Paragraph("INOP. PARC.", style_center_mini_bold), Paragraph("INOP. TOTAL", style_center_mini_bold), Paragraph("JUSTIFICATIVA", style_center_mini_bold)],
        [Paragraph(x_op, style_center_val), Paragraph(x_parc, style_center_val), Paragraph(x_inop, style_center_val), Paragraph(rdo.get('just_inop',''), style_val)]
    ]
    t_area = Table(t_area_data, colWidths=[18*mm, 20*mm, 21*mm, 31*mm], rowHeights=[6*mm, 6*mm, 6*mm])
    t_area.setStyle(TableStyle([('SPAN', (0,0), (3,0)), ('BACKGROUND', (0,0), (3,0), cor_verde_claro), ('GRID', (0,0), (-1,-1), 1, cor_borda), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))

    t_block_2 = Table([[t_tempo, '', t_area]], colWidths=[80*mm, 7.5*mm, 90*mm])
    t_block_2.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    elementos.append(t_block_2)
    elementos.append(Spacer(1, 4))

    funcs_salvas = rdo.get('func', [""]*10)
    equips_salvos = rdo.get('equip', [""]*10)
    tubos_salvos = rdo.get('tubo', [""]*10)
    
    def criar_tabela_hist(titulo, labels, valores):
        dados = [[Paragraph(titulo, style_center_bold), '']]
        for i in range(10): 
            label = labels[i] if i < len(labels) else ""
            val = valores[i] if i < len(valores) else ""
            dados.append([Paragraph(label, style_val) if label else "", Paragraph(val, style_center_val) if val else ""])
        tab = Table(dados, colWidths=[45*mm, 12*mm], rowHeights=[5*mm]*11)
        tab.setStyle(TableStyle([
            ('SPAN', (0,0), (1,0)), ('BACKGROUND', (0,0), (1,0), cor_azul_claro),
            ('GRID', (0,0), (-1,-1), 1, cor_borda), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        return tab

    t_mo = criar_tabela_hist("MÃO DE OBRA", nomes_mao_de_obra, funcs_salvas)
    t_eq_geo = criar_tabela_hist("EQUIP. SOLDA GEO.", nomes_equip_geo, equips_salvos)
    t_eq_tubo = criar_tabela_hist("EQUIP. SOLDA TUBO", nomes_equip_tubo, tubos_salvos)

    t_block_3 = Table([[t_mo, '', t_eq_geo, '', t_eq_tubo]], colWidths=[57*mm, 3.25*mm, 57*mm, 3.25*mm, 57*mm])
    t_block_3.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    elementos.append(t_block_3)
    elementos.append(Spacer(1, 4))

    larg = rdo.get('p_larg','')
    comp = rdo.get('p_comp','')
    bobina = f"{larg} x {comp}" if larg and comp else ""

    t_app_data = [
        [Paragraph("APLICAÇÃO", style_center_bold), ''],
        [Paragraph("TOTAL APLICADO:", style_label), Paragraph(f"{rdo.get('qtd','')} m²", style_center_val)],
        [Paragraph("BOBINA (L x C):", style_label), Paragraph(bobina, style_center_val)],
        [Paragraph("MANCHÃO (UNID):", style_label), Paragraph(rdo.get('manchao',''), style_center_val)],
        [Paragraph("CANOPLA (UNID):", style_label), Paragraph(rdo.get('canopla',''), style_center_val)]
    ]
    t_app = Table(t_app_data, colWidths=[40*mm, 30*mm], rowHeights=[6*mm]*5)
    t_app.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)), ('BACKGROUND', (0,0), (1,0), cor_amarelo),
        ('GRID', (0,0), (-1,-1), 1, cor_borda), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))

    texto_atv = rdo.get('atv','').replace('\n', '<br/>')
    t_atv_data = [
        [Paragraph("DESCRIÇÃO DAS ATIVIDADES", style_center_bold)],
        [Paragraph(texto_atv, style_val)]
    ]
    t_atv = Table(t_atv_data, colWidths=[100*mm], rowHeights=[6*mm, 24*mm])
    t_atv.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), cor_amarelo),
        ('GRID', (0,0), (-1,-1), 1, cor_borda), ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))

    t_block_4 = Table([[t_app, '', t_atv]], colWidths=[70*mm, 7.5*mm, 100*mm])
    t_block_4.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    elementos.append(t_block_4)
    elementos.append(Spacer(1, 4))

    chk = '[ X ]' if rdo.get('diaria') else '[   ]'
    just_text = rdo.get('just_d', '').strip()
    obs_text = rdo.get('obs_d', '').strip()

    t_just = Table([
        [Paragraph(f"<b>DIÁRIA TÉCNICA:</b> {chk}", style_val), Paragraph("<b>JUSTIFICATIVA:</b>", style_val), Paragraph(just_text, style_val)]
    ], colWidths=[35*mm, 25*mm, 107.5*mm], rowHeights=[9*mm])
    t_just.setStyle(TableStyle([
        ('LINEBELOW', (2,0), (2,0), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    t_obs = Table([
        [Paragraph("<b>OBSERVAÇÃO:</b>", style_val), Paragraph(obs_text, style_val)]
    ], colWidths=[23*mm, 144.5*mm], rowHeights=[9*mm])
    t_obs.setStyle(TableStyle([
        ('LINEBELOW', (1,0), (1,0), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))

    t_evt_data = [
        [Paragraph("EVENTUALIDADES / CONSIDERAÇÕES TÉCNICAS", style_center_bold), '', ''],
        ['', t_just, ''],
        ['', t_obs, ''],
        ['', '', ''],
        ['', '', ''],
        ['', '', '']
    ]
    t_evt = Table(t_evt_data, colWidths=[5*mm, 167.5*mm, 5*mm], rowHeights=[6*mm, 9*mm, 9*mm, 8*mm, 8*mm, 8*mm])
    t_evt.setStyle(TableStyle([
        ('SPAN', (0,0), (2,0)), ('BOX', (0,0), (-1,-1), 1, cor_borda), ('BACKGROUND', (0,0), (2,0), cor_verde_claro),
        ('LINEBELOW', (0,0), (2,0), 1, cor_borda),
        ('LINEBELOW', (1,3), (1,3), 0.5, colors.grey), ('LINEBELOW', (1,4), (1,4), 0.5, colors.grey), ('LINEBELOW', (1,5), (1,5), 0.5, colors.grey),
        ('VALIGN', (0,0), (2,0), 'MIDDLE'), ('VALIGN', (0,1), (-1,-1), 'BOTTOM'), 
    ]))
    elementos.append(t_evt)
    elementos.append(Spacer(1, 6))

    nome_empresa_str = "EMPRESA"
    if contexto['empresa']:
        if isinstance(contexto['empresa'], dict) and "nome" in contexto['empresa']:
            nome_empresa_str = contexto['empresa']["nome"].upper()
        elif isinstance(contexto['empresa'], (tuple, list)) and len(contexto['empresa']) > 1:
            nome_empresa_str = str(contexto['empresa'][1]).upper()

   # ==========================================================
    # LÓGICA DE INSERÇÃO DA ASSINATURA NO PDF (LINHA REAL)
    # ==========================================================
    ass_data = rdo.get('assinatura', {})
    ass_flowable = ""
    
    if ass_data and isinstance(ass_data, dict):
        if ass_data.get("tipo") == "texto":
            style_ass = ParagraphStyle('Ass', fontName='Times-Italic', fontSize=14, alignment=TA_CENTER, textColor=colors.darkblue)
            texto_formatado = ass_data.get("valor", "").replace('\n', '<br/>')
            ass_flowable = Paragraph(texto_formatado, style_ass)
        elif ass_data.get("tipo") == "imagem":
            caminho_ass = ass_data.get("valor", "")
            if os.path.exists(caminho_ass):
                try: 
                    # Altura ajustada para 12mm
                    ass_flowable = Image(caminho_ass, width=40*mm, height=12*mm)
                except: pass

    # Usamos 3 colunas agora: [Empresa, Espaço Vazio no Meio, Cliente]
    # Removemos a linha cheia de "____" escrita.
    dados_ass = [
        [ass_flowable, "", ""],
        [f"RESPONSÁVEL / {nome_empresa_str}", "", "CLIENTE"],
        [f"Data: {data_bruta}", "", "Data: _____ / _____ / _______"] 
    ]
    
    # 80mm de linha pra empresa, 17.5mm de espaço vazio, 80mm de linha pro cliente
    tabela_ass = Table(dados_ass, colWidths=[80*mm, 17.5*mm, 80*mm], rowHeights=[14*mm, 5*mm, 5*mm])
    tabela_ass.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'), 
        ('VALIGN', (0,0), (-1,0), 'BOTTOM'), # Cola a imagem na base da célula
        ('VALIGN', (0,1), (-1,-1), 'TOP'),
        
        # --- A MÁGICA DEFINITIVA ---
        # Desenha uma linha real embaixo da célula da assinatura
        ('LINEBELOW', (0,0), (0,0), 1, colors.black), # Linha do Responsável
        ('LINEBELOW', (2,0), (2,0), 1, colors.black), # Linha do Cliente
        ('BOTTOMPADDING', (0,0), (-1,0), 1), # Dá só 1 pixel de respiro pra não cortar a foto
        # ---------------------------
        
        ('FONTNAME', (0,1), (-1,2), 'Helvetica-Bold'), 
        ('FONTSIZE', (0,1), (-1,2), 9)
    ]))
    elementos.append(tabela_ass)

    # ==========================================================
    
    fotos = rdo.get("fotos", [])[:6]
    if fotos:
        elementos.append(PageBreak())
        if os.path.exists(caminho_logo):
            try: 
                img_logo2 = Image(caminho_logo, width=40*mm, height=15*mm)
                img_logo2.hAlign = 'LEFT'
                elementos.append(img_logo2)
                elementos.append(HRFlowable(width=177.5*mm, thickness=1.5, color=colors.black, spaceBefore=3, spaceAfter=8))
            except: pass
            
        elementos.append(Paragraph("REGISTRO FOTOGRÁFICO", ParagraphStyle('TitFoto', parent=style_title, alignment=TA_CENTER)))
        elementos.append(Spacer(1, 10))

        linhas_de_fotos = []
        linha_atual = []
        for foto in fotos:
            if os.path.exists(foto):
                linha_atual.append(Image(foto, width=85*mm, height=65*mm))
                if len(linha_atual) == 2:
                    linhas_de_fotos.append(linha_atual)
                    linha_atual = []
        if linha_atual: 
            linha_atual.append("") 
            linhas_de_fotos.append(linha_atual)

        if linhas_de_fotos:
            tabela_fotos = Table(linhas_de_fotos, colWidths=[88*mm, 88*mm], rowHeights=[70*mm]*len(linhas_de_fotos))
            tabela_fotos.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            elementos.append(tabela_fotos)

    try:
        doc.build(elementos)
        caminho_abs = os.path.abspath(caminho_completo)
        
        # Verifica em qual sistema o app está rodando
        if sys.platform == "win32":
            # Se for Windows (seu PC), usa o startfile normal
            os.startfile(caminho_abs)
        else:
            # Se for Android/Linux/Mac, usa o lançador nativo do Flet
            page.launch_url(f"file://{caminho_abs}")
            
    except PermissionError:
        page.snack_bar = ft.SnackBar(ft.Text(f"Atenção: Feche o arquivo '{nome_arquivo}' no Leitor de PDF para salvar a nova versão!", color=ft.colors.WHITE), bgcolor=ft.colors.RED)
        page.snack_bar.open = True
        page.update()
        return
    except Exception as e:
        print(f"Erro ao gerar PDF: {e}")

    if getattr(page, "dialog", None) and getattr(page.dialog, "open", False):
        page.dialog.open = False
    page.update()