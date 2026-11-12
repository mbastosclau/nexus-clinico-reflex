from fpdf import FPDF
from datetime import datetime

class PDFExecutivo(FPDF):
    def header(self):
        # Fonte Arial negrito 14
        self.set_font('Arial', 'B', 14)
        # Cor do texto do cabeçalho (Azul Marinho / Cinza Escuro)
        self.set_text_color(41, 50, 65)
        # Título centralizado
        self.cell(0, 10, 'NEXUS CLINICO - DOSSIE EXECUTIVO', border=0, ln=1, align='C')
        # Linha de separação elegante
        self.set_draw_color(41, 50, 65)
        self.set_line_width(0.5)
        self.line(10, 22, 200, 22)
        self.ln(10)

    def footer(self):
        # Posição a 1.5 cm do final da página
        self.set_y(-15)
        # Fonte Arial itálico 8
        self.set_font('Arial', 'I', 8)
        # Cor cinza claro para o rodapé
        self.set_text_color(128, 128, 128)
        # Número da página dinâmico e aviso de CDS
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}} | Sistema de Apoio a Decisao Clinica (CDS)', 0, 0, 'C')

def gerar_pdf_simples(texto_laudo: str, nome_paciente: str) -> bytes:
    """Gera o PDF formatado com design executivo pronto para download."""
    # Instancia a nossa classe personalizada
    pdf = PDFExecutivo()
    # Ativa a contagem total de páginas (para o {nb} do rodapé)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Tratamento de caracteres especiais (substituindo acentos problemáticos no FPDF básico)
    substituicoes = {
        '**': '', '###': '', '##': '', '#': '', '–': '-', '—': '-', 
        '≥': '>=', '≤': '<=', '“': '"', '”': '"', '’': "'", '‘': "'", 
        '•': '-', 'µ': 'u', 'º': 'o', 'ª': 'a'
    }
    for k, v in substituicoes.items():
        texto_laudo = texto_laudo.replace(k, v)
        
    # Força a codificação para latin-1 para evitar erros de renderização
    texto_limpo = texto_laudo.encode('latin-1', 'replace').decode('latin-1')
    
    # --- BLOCO DE IDENTIFICAÇÃO DO PACIENTE ---
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    data_atual = datetime.now().strftime("%d/%m/%Y as %H:%M")
    
    # Adiciona um pequeno fundo cinza claro para os dados do paciente
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(0, 8, f"  Paciente: {nome_paciente}", ln=1, fill=True)
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 6, f"  Data da Analise: {data_atual}", ln=1, fill=True)
    pdf.ln(8)
    
    # --- BLOCO DE IMPRESSÃO DO LAUDO (COM FORMATAÇÃO INTELIGENTE) ---
    linhas = texto_limpo.split('\n')
    
    for linha in linhas:
        texto_linha = linha.strip()
        if not texto_linha:
            pdf.ln(3)
            continue
            
        # 1. Se a linha for um Título Principal (tudo em maiúsculas e maior que 5 letras)
        if texto_linha.isupper() and len(texto_linha) > 5 and not texto_linha.startswith("-"):
            pdf.ln(4)
            pdf.set_font("Arial", 'B', 11)
            pdf.set_text_color(41, 50, 65) # Azul Marinho
            pdf.multi_cell(0, 6, txt=texto_linha)
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(0, 0, 0)
            
        # 2. Se a linha for a Ressalva Legal (destaque de segurança)
        elif "RESSALVA LEGAL" in texto_linha.upper() or "RESPONSABILIDADE" in texto_linha.upper():
            pdf.ln(4)
            pdf.set_font("Arial", 'BI', 9)
            pdf.set_text_color(180, 50, 50) # Tom vermelho escuro/alerta
            pdf.multi_cell(0, 5, txt=texto_linha)
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(0, 0, 0)
            
        # 3. Texto normal do laudo
        else:
            pdf.set_font("Arial", '', 10)
            pdf.set_text_color(50, 50, 50) # Cinza muito escuro para leitura mais confortável
            pdf.multi_cell(0, 5.5, txt=texto_linha)
        
    saida = pdf.output(dest='S')
    return saida.encode('latin-1') if isinstance(saida, str) else bytes(saida)