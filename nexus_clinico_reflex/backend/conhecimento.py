import os
import pandas as pd
import PyPDF2
import io

def carregar_base_conhecimento() -> str:
    texto_base = ""
    # Procura a pasta assets/conhecimento na raiz
    caminho_conhecimento = os.path.join(os.getcwd(), "assets", "conhecimento")
    
    if not os.path.exists(caminho_conhecimento):
        return "Nenhuma base de conhecimento adicional encontrada na pasta assets/conhecimento."

    for arquivo in os.listdir(caminho_conhecimento):
        caminho_arquivo = os.path.join(caminho_conhecimento, arquivo)
        
        if arquivo.lower().endswith(".pdf"):
            try:
                with open(caminho_arquivo, "rb") as f:
                    leitor = PyPDF2.PdfReader(f)
                    # Extrai as primeiras páginas para não sobrecarregar os tokens
                    txt = "".join([leitor.pages[i].extract_text() or "" for i in range(min(15, len(leitor.pages)))])
                    texto_base += f"\n--- DIRETRIZ OFICIAL ({arquivo}) ---\n" + txt[:3000].replace('\n', ' ') + "\n"
            except Exception as e:
                print(f"Erro ao ler PDF {arquivo}: {e}")
                
        elif arquivo.lower().endswith(".csv"):
            try:
                # Tenta ler a Tabela TACO ou similar
                df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
                texto_base += f"\n--- TABELA NUTRICIONAL ({arquivo}) ---\n{df.head(250).to_string()}\n"
            except Exception:
                try: # Fallback de codificação para tabelas vindas do Excel
                    df = pd.read_csv(caminho_arquivo, sep=None, engine='python', encoding='latin-1', on_bad_lines='skip')
                    texto_base += f"\n--- TABELA NUTRICIONAL ({arquivo}) ---\n{df.head(250).to_string()}\n"
                except Exception as e2:
                    print(f"Erro ao ler CSV {arquivo}: {e2}")

    return texto_base