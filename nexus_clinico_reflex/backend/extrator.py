import io
import PyPDF2

def extrair_texto_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extrai todo o texto legível de um ficheiro PDF enviado em bytes."""
    try:
        leitor = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        texto = ""
        for pagina in leitor.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                texto += texto_pagina + "\n"
        return texto.strip()
    except Exception as e:
        return f"Erro ao extrair PDF: {str(e)}"