import os
import json
from anthropic import Anthropic
from dotenv import load_dotenv
from . import conhecimento

load_dotenv()

def processar_exames_clinicos(texto_exames: str, paciente: dict, modulo: str) -> str:
    try:
        client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"), timeout=90.0, max_retries=1)
    except Exception as e:
        return f"Erro de configuração da API: {str(e)}"

    # Carrega a tabela TACO e PDFs
    base_literatura = conhecimento.carregar_base_conhecimento()

    # CORREÇÃO 2: Injetar o histórico do paciente (se houver) no prompt mestre
    historico_prompt = ""
    if paciente.get('laudo_anterior'):
        historico_prompt = f"""
    HISTÓRICO DO PACIENTE (ATENDIMENTO DE RETORNO):
    Data da Última Consulta: {paciente.get('data_anterior')}
    Laudo Anterior: {paciente.get('laudo_anterior')}
    
    -> IMPORTANTE: Como este é um paciente de RETORNO, você deve comparar os novos exames com o laudo anterior e destacar explicitamente a evolução clínica (melhora, piora ou estabilidade) nos eixos metabólicos, mencionando a data da última consulta.
    """

    prompt_mestre = f"""
    DADOS DO PACIENTE:
    Nome: {paciente.get('nome', 'N/A')} | Idade: {paciente.get('idade', 'N/A')} | Sexo: {paciente.get('sexo', 'N/A')}
    Objetivo: {paciente.get('objetivo', 'N/A')}
    Contexto Biométrico e Atividade: {paciente.get('contexto', 'N/A')}
    {historico_prompt}
    
    MÓDULO DE ANÁLISE: {modulo}
    
    RESULTADOS LABORATORIAIS E BIOIMPEDÂNCIA EXTRAÍDOS:
    {texto_exames}
    
    DOCUMENTOS OFICIAIS DE BASE (TACO E DIRETRIZES DO PROJETO):
    {base_literatura}
    
    DIRETRIZ CLÍNICA - SÍNTESE EXECUTIVA (ECONOMIA DE TOKENS):
    Você é um Copiloto Médico Sênior. O usuário final já é um médico experiente, portanto, É ESTRITAMENTE PROIBIDO explicar conceitos básicos de medicina (ex: não explique o que é HOMA-IR ou por que o jejum não é mais necessário). Vá direto aos achados.
    
    REGRAS DE CONCISÃO EXTREMA (MÁXIMO DE 2 PÁGINAS):
    1. Na Seção 2, agrupe os eixos em BULLET POINTS (tópicos curtos). Proibido usar parágrafos longos. Ignore eixos 100% normais se não forem relevantes.
    2. NÃO GERE cardápios.
    3. Na Seção 3, cite de 3 a 4 alimentos da TABELA TACO de forma ULTRA-RESUMIDA (Apenas nome e principal benefício em uma linha).
    4. Na Seção 4, cite as 2 ou 3 diretrizes base mais relevantes em uma ÚNICA FRASE CONCISA. Proibido listar e explicar o que cada diretriz fez.
    
    ESTRUTURA OBRIGATÓRIA:
    1. RESUMO EXECUTIVO E ALERTAS
    2. ANÁLISE DOS EIXOS METABÓLICOS (Apenas achados relevantes, em tópicos diretos)
    3. PLANO DE AÇÃO E ESTRATÉGIA NUTRICIONAL (Ultra-conciso, com 3-4 exemplos TACO)
    4. PARECER, REFERENCIAL TEÓRICO (Citar 2-3 fontes em 1 linha) E RESSALVA LEGAL (Incluir a frase de responsabilidade do profissional).
    """

    sistema_prompt = "Você é uma IA médica de alta performance. Complete obrigatoriamente todas as 4 seções até a RESSALVA LEGAL."
    mensagens_api = [{"role": "user", "content": prompt_mestre}]
    laudo_acumulado = ""

    try:
        # Loop idêntico ao do Nexus Estética para evitar laudos cortados
        for tentativa in range(3):
            try:
                resposta = client.messages.create(
                    model="claude-sonnet-5-5",
                    max_tokens=8192,
                    thinking={"type": "between_tools"},
                    system=sistema_prompt,
                    messages=mensagens_api
                )
            except Exception:
                resposta = client.messages.create(
                    model="claude-sonnet-5-5",
                    max_tokens=8192,
                    system=sistema_prompt,
                    messages=mensagens_api
                )

            trecho_atual = []
            for bloco in resposta.content:
                if getattr(bloco, 'type', None) == 'text' and hasattr(bloco, 'text'):
                    trecho_atual.append(bloco.text)
                elif hasattr(bloco, 'text') and bloco.text:
                    trecho_atual.append(bloco.text)
                elif isinstance(bloco, dict) and bloco.get('type') == 'text':
                    trecho_atual.append(bloco.get('text', ''))

            texto_trecho = "\n\n".join(trecho_atual).strip()
            if texto_trecho:
                if not laudo_acumulado:
                    laudo_acumulado = texto_trecho
                else:
                    separador = " " if not laudo_acumulado.endswith((".", ":", "\n")) else "\n"
                    laudo_acumulado = laudo_acumulado + separador + texto_trecho

            motivo_parada = getattr(resposta, "stop_reason", "")
            texto_lower = laudo_acumulado.lower()

            # Condição de paragem
            concluiu_secao_4 = ("4." in laudo_acumulado and "responsabilidade" in texto_lower)

            if concluiu_secao_4 or (motivo_parada != "max_tokens" and "4." in laudo_acumulado):
                break

            # Força a IA a continuar de onde parou
            mensagens_api = [
                {"role": "user", "content": prompt_mestre},
                {"role": "assistant", "content": laudo_acumulado},
                {
                    "role": "user",
                    "content": "Continue o dossiê clínico EXATAMENTE da última palavra onde parou, sem repetir absolutamente nada do que já foi escrito e sem comentários introdutórios, completando o restante até a RESSALVA LEGAL da seção 4."
                }
            ]

        return laudo_acumulado.strip() if laudo_acumulado else "Erro: Nenhum texto retornado pela IA."
        
    except Exception as e:
        return f"Erro na comunicação com a API do Claude: {str(e)}"