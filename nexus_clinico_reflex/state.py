import reflex as rx
from supabase import create_client, Client
import os
import json
from datetime import datetime
from dotenv import load_dotenv

from .backend import analisador
from .backend.extrator import extrair_texto_pdf_bytes
from .backend.pdf_gerador import gerar_pdf_simples

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        pass

class ClinicoState(rx.State):
    # Variáveis de Estado
    historico_consultas: list[dict] = []
    esta_autenticado: bool = False
    usuario_id: str = ""
    email_login: str = ""
    senha_login: str = ""
    nome_registro: str = ""

    lista_pacientes: list[str] = []
    paciente_ativo: str = ""
    modo_paciente: str = "Selecionar Existente"
    novo_nome_paciente: str = ""
    
    idade_paciente: str = "45"
    sexo_paciente: str = "Masculino"
    peso_paciente: str = "85.0"
    objetivo_paciente: str = "Emagrecimento (Foco Clínico / Síndrome Metabólica)"
    atividade_fisica: str = "Moderado (Musculação 3-4x)"
    contexto_clinico: str = ""
    modulo_analise: str = "Performance, Emagrecimento e Endocrinologia"

    em_processamento: bool = False
    laudo_texto: str = ""
    
    # Acumuladores de memória
    arquivos_processados: list[str] = []
    texto_exames_acumulado: str = ""
    arquivos_sangue: list[str] = []
    arquivos_bio: list[str] = []

    def set_email_login(self, email: str): self.email_login = email
    def set_senha_login(self, senha: str): self.senha_login = senha
    def set_nome_registro(self, nome: str): self.nome_registro = nome
    def set_modo_paciente(self, modo: str): self.modo_paciente = modo
    def set_novo_nome_paciente(self, nome: str): self.novo_nome_paciente = nome
    def set_idade_paciente(self, idade: str): self.idade_paciente = idade
    def set_sexo_paciente(self, sexo: str): self.sexo_paciente = sexo
    def set_peso_paciente(self, peso: str): self.peso_paciente = peso
    def set_objetivo_paciente(self, obj: str): self.objetivo_paciente = obj
    def set_atividade_fisica(self, ativ: str): self.atividade_fisica = ativ
    def set_contexto_clinico(self, contexto: str): self.contexto_clinico = contexto
    def set_modulo_analise(self, modulo: str): self.modulo_analise = modulo

    def fazer_login(self):
        if not self.email_login or not self.senha_login: return rx.window_alert("Preencha e-mail e senha.")
        if supabase:
            try:
                res = supabase.auth.sign_in_with_password({"email": self.email_login, "password": self.senha_login})
                self.usuario_id = res.user.id
                self.esta_autenticado = True
                self.carregar_pacientes()
            except Exception as e: return rx.window_alert("Erro ao autenticar. Verifique as credenciais.")
        else: return rx.window_alert("Erro: Supabase não conectado.")

    def registrar_profissional(self):
        if not self.email_login or len(self.senha_login) < 6: return rx.window_alert("E-mail inválido ou senha muito curta.")
        if supabase:
            try:
                res = supabase.auth.sign_up({"email": self.email_login, "password": self.senha_login})
                return rx.window_alert("Conta criada com sucesso! Pode fazer o Login.")
            except Exception as e: return rx.window_alert(f"Erro ao registrar: {str(e)}")

    def logout(self):
        self.esta_autenticado = False
        self.usuario_id = ""
        self.paciente_ativo = ""
        self.laudo_texto = ""
        self.limpar_uploads() # Limpa os arquivos ao sair

    def carregar_pacientes(self):
        if not self.usuario_id or not supabase: return
        try:
            res = supabase.table("pacientes").select("*").eq("profissional_id", self.usuario_id).execute()
            self.lista_pacientes = [p["nome"] for p in res.data] if res.data else []
            if not self.paciente_ativo and self.lista_pacientes:
                self.set_paciente_ativo(self.lista_pacientes[0])
        except Exception as e:
            print(f"Erro ao carregar pacientes: {e}")

    def set_paciente_ativo(self, nome: str):
        self.paciente_ativo = nome
        self.modo_paciente = "Selecionar Existente"
        self.laudo_texto = ""
        self.limpar_uploads()
        self.historico_consultas = []
        
        if not supabase: return
        
        try:
            pac_res = supabase.table("pacientes").select("id").eq("nome", nome).eq("user_id", self.usuario_id).execute()
            if not pac_res.data: return
            paciente_id = pac_res.data[0]["id"]

            pront_res = supabase.table("prontuarios").select("*").eq("paciente_id", paciente_id).order("data_atendimento", desc=True).execute()
            
            if pront_res.data:
                self.historico_consultas = [{
                    "data": p.get("data_atendimento", "")[:10],
                    "modulo": p.get("modulo", "Análise Clínica"),
                    "laudo": p.get("laudo_texto", "")
                } for p in pront_res.data]

                ultimo_pront = pront_res.data[0]
                biometria = ultimo_pront.get("biometria", {})
                if biometria:
                    self.idade_paciente = str(biometria.get("idade", "45"))
                    self.sexo_paciente = biometria.get("sexo", "Masculino")
                    self.peso_paciente = str(biometria.get("peso", "85.0"))
                    self.objetivo_paciente = biometria.get("objetivo", "Emagrecimento")
                    self.atividade_fisica = biometria.get("atividade", "Moderado")
            else:
                self.idade_paciente = "45"
                self.sexo_paciente = "Masculino"
                self.peso_paciente = "85.0"
                
        except Exception as e:
            print(f"Erro ao carregar dados do paciente: {e}")

    def confirmar_novo_paciente(self):
        if not self.novo_nome_paciente: return rx.window_alert("Digite o nome do paciente.")
        
        self.paciente_ativo = self.novo_nome_paciente
        self.modo_paciente = "Selecionar Existente"
        self.novo_nome_paciente = ""
        self.historico_consultas = []
        
        if self.paciente_ativo not in self.lista_pacientes:
            self.lista_pacientes.append(self.paciente_ativo)
            
        if supabase:
            try:
                supabase.table("pacientes").insert({
                    "profissional_id": self.usuario_id, 
                    "nome": self.paciente_ativo
                }).execute()
            except Exception as e:
                print(f"Erro ao criar paciente: {e}")

    def excluir_paciente(self):
        if not supabase or not self.paciente_ativo: return
        try:
            pac_res = supabase.table("pacientes").select("id").eq("nome", self.paciente_ativo).eq("profissional_id", self.usuario_id).execute()
            if pac_res.data:
                pac_id = pac_res.data[0]["id"]
                supabase.table("prontuarios").delete().eq("paciente_id", pac_id).execute()
                supabase.table("pacientes").delete().eq("id", pac_id).execute()
            self.paciente_ativo = ""
            self.carregar_pacientes()
        except Exception as e:
            print(f"Erro ao excluir paciente: {e}")

    def salvar_perfil_biometrico(self):
        if not supabase or not self.paciente_ativo: 
            return rx.window_alert("Selecione um paciente primeiro.")
        try:
            # Busca o ID do paciente
            pac_res = supabase.table("pacientes").select("id").eq("nome", self.paciente_ativo).eq("user_id", self.usuario_id).execute()
            if pac_res.data:
                pac_id = pac_res.data[0]["id"]
                
                # Salva o perfil como um registo
                supabase.table("prontuarios").insert({
                    "paciente_id": pac_id,
                    "profissional_id": self.usuario_id,
                    "data_atendimento": datetime.now().isoformat(),
                    "modulo": "Atualização de Perfil",
                    "laudo_texto": "Perfil biométrico atualizado.",
                    "biometria": {
                        "idade": self.idade_paciente,
                        "sexo": self.sexo_paciente,
                        "peso": self.peso_paciente,
                        "objetivo": self.objetivo_paciente,
                        "atividade": self.atividade_fisica
                    }
                }).execute()
                
                self.set_paciente_ativo(self.paciente_ativo)
                return rx.window_alert("✅ Perfil atualizado com sucesso!")
        except Exception as e:
            print(f"Erro ao salvar perfil: {e}")

    
    def limpar_uploads(self):
        self.arquivos_processados = []
        self.texto_exames_acumulado = ""
        self.arquivos_sangue = []
        self.arquivos_bio = []
        return [rx.clear_selected_files("up_sangue"), rx.clear_selected_files("up_bio")]

    async def confirmar_sangue(self, files: list[rx.UploadFile]):
        if not files: return
        for file in files:
            if file.filename not in self.arquivos_processados:
                upload_data = await file.read()
                texto_extraido = extrair_texto_pdf_bytes(upload_data)
                if texto_extraido: 
                    self.texto_exames_acumulado += f"\n--- EXAME DE SANGUE: {file.filename} ---\n{texto_extraido}\n"
                self.arquivos_processados.append(file.filename)
                self.arquivos_sangue.append(file.filename)

    async def confirmar_bio(self, files: list[rx.UploadFile]):
        if not files: return
        for file in files:
            if file.filename not in self.arquivos_processados:
                upload_data = await file.read()
                texto_extraido = extrair_texto_pdf_bytes(upload_data)
                if texto_extraido: 
                    self.texto_exames_acumulado += f"\n--- BIOIMPEDÂNCIA/COMPOSIÇÃO: {file.filename} ---\n{texto_extraido}\n"
                self.arquivos_processados.append(file.filename)
                self.arquivos_bio.append(file.filename)

    async def processar_laudo(self):
        if not self.paciente_ativo:
            yield rx.window_alert("Selecione ou crie um paciente primeiro.")
            return
        if not self.texto_exames_acumulado:
            yield rx.window_alert("Anexe e confirme pelo menos um exame antes de analisar.")
            return
        
        self.em_processamento = True
        yield

        try:
            laudo_anterior = ""
            data_anterior = ""
            if self.historico_consultas:
                # Pega o primeiro da lista, que é o mais recente devido ao order desc no SQL
                ultima_consulta = self.historico_consultas[0]
                laudo_anterior = ultima_consulta["laudo"]
                data_anterior = ultima_consulta["data"]

            paciente_dados = {
                "nome": self.paciente_ativo,
                "idade": self.idade_paciente,
                "sexo": self.sexo_paciente,
                "peso": self.peso_paciente,
                "atividade": self.atividade_fisica,
                "objetivo": self.objetivo_paciente,
                "contexto": self.contexto_clinico,
                "laudo_anterior": laudo_anterior,
                "data_anterior": data_anterior
            }

            self.laudo_texto = analisador.processar_exames_clinicos(self.texto_exames_acumulado, paciente_dados, self.modulo_analise)
            
            if supabase:
                pac_res = supabase.table("pacientes").select("id").eq("nome", self.paciente_ativo).eq("profissional_id", self.usuario_id).execute()
                if pac_res.data:
                    paciente_id = pac_res.data[0]["id"]
                    
                    supabase.table("prontuarios").insert({
                        "paciente_id": paciente_id,
                        "profissional_id": self.usuario_id,
                        "data_atendimento": datetime.now().isoformat(),
                        "modulo": self.modulo_analise,
                        "laudo_texto": self.laudo_texto,
                        "biometria": {
                            "idade": self.idade_paciente,
                            "sexo": self.sexo_paciente,
                            "peso": self.peso_paciente,
                            "objetivo": self.objetivo_paciente,
                            "atividade": self.atividade_fisica
                        }
                    }).execute()
                    
                    self.set_paciente_ativo(self.paciente_ativo)

        except Exception as e: self.laudo_texto = f"Erro Crítico: {str(e)}"
        finally:
            self.em_processamento = False
            yield 

    def baixar_pdf(self):
        if not self.laudo_texto: return rx.window_alert("Não há laudo para descarregar.")
        pdf_bytes = gerar_pdf_simples(self.laudo_texto, self.paciente_ativo)
        return rx.download(data=pdf_bytes, filename=f"Dossie_{self.paciente_ativo.replace(' ', '_')}.pdf")

    def baixar_laudo_historico(self, laudo_texto: str, data_str: str):
        if not laudo_texto: return rx.window_alert("Laudo vazio.")
        pdf_bytes = gerar_pdf_simples(laudo_texto, self.paciente_ativo)
        return rx.download(data=pdf_bytes, filename=f"Dossie_{self.paciente_ativo.replace(' ', '_')}_{data_str}.pdf")
