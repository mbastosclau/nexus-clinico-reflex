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
        self.arquivos_processados = []
        self.texto_exames_acumulado = ""
        self.arquivos_sangue = []
        self.arquivos_bio = []

    def get_pasta_bd(self) -> str:
        pasta = f"banco_pacientes_{self.usuario_id}"
        os.makedirs(pasta, exist_ok=True)
        return pasta

    def carregar_pacientes(self):
        if not self.usuario_id: return
        pasta = self.get_pasta_bd()
        self.lista_pacientes = [f.replace('.json', '') for f in os.listdir(pasta) if f.endswith('.json')]
        if not self.paciente_ativo and self.lista_pacientes:
            self.set_paciente_ativo(self.lista_pacientes[0])

    def set_paciente_ativo(self, nome: str):
        self.paciente_ativo = nome
        self.modo_paciente = "Selecionar Existente"
        self.laudo_texto = ""
        self.arquivos_processados = []
        self.texto_exames_acumulado = ""
        self.arquivos_sangue = []
        self.arquivos_bio = []
        
        caminho = os.path.join(self.get_pasta_bd(), f"{nome}.json")
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                try:
                    historico = json.load(f)
                    if historico and isinstance(historico, list):
                        ultimo_registro = historico[-1]
                        biometria = ultimo_registro.get("biometria", {})
                        if biometria:
                            self.idade_paciente = biometria.get("idade", "45")
                            self.sexo_paciente = biometria.get("sexo", "Masculino")
                            self.peso_paciente = biometria.get("peso", "85.0")
                            self.objetivo_paciente = biometria.get("objetivo", "Emagrecimento (Foco Clínico / Síndrome Metabólica)")
                            self.atividade_fisica = biometria.get("atividade", "Moderado (Musculação 3-4x)")
                            return 
                except Exception as e:
                    print(f"Erro ao carregar dados: {e}")
        
        self.idade_paciente = "45"
        self.sexo_paciente = "Masculino"
        self.peso_paciente = "85.0"

    def confirmar_novo_paciente(self):
        if self.novo_nome_paciente:
            self.paciente_ativo = self.novo_nome_paciente
            self.modo_paciente = "Selecionar Existente"
            self.novo_nome_paciente = ""
            self.arquivos_processados = []
            self.texto_exames_acumulado = ""
            self.arquivos_sangue = []
            self.arquivos_bio = []
            
            if self.paciente_ativo not in self.lista_pacientes:
                self.lista_pacientes.append(self.paciente_ativo)
            
            if supabase:
                try:
                    supabase.table("pacientes").insert({"user_id": self.usuario_id, "nome": self.paciente_ativo}).execute()
                except Exception as e:
                    print(f"Erro Supabase: {e}")
            
            caminho = os.path.join(self.get_pasta_bd(), f"{self.paciente_ativo}.json")
            if not os.path.exists(caminho):
                with open(caminho, 'w', encoding='utf-8') as f:
                    json.dump([{"modulo": "Cadastro Inicial", "data": datetime.now().strftime("%d/%m/%Y"), "biometria": {
                        "idade": self.idade_paciente, "sexo": self.sexo_paciente, "peso": self.peso_paciente,
                        "objetivo": self.objetivo_paciente, "atividade": self.atividade_fisica
                    }}], f, ensure_ascii=False, indent=4)
        else:
            return rx.window_alert("Digite o nome do paciente.")

    def excluir_paciente(self):
        if self.paciente_ativo:
            caminho = os.path.join(self.get_pasta_bd(), f"{self.paciente_ativo}.json")
            if os.path.exists(caminho): os.remove(caminho)
            self.paciente_ativo = ""
            self.carregar_pacientes()

    def salvar_perfil_biometrico(self):
        if not self.paciente_ativo: return rx.window_alert("Selecione um paciente primeiro.")
        caminho = os.path.join(self.get_pasta_bd(), f"{self.paciente_ativo}.json")
        historico = []
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                try: historico = json.load(f)
                except: historico = []
        if not historico:
            historico.append({"modulo": "Atualização de Perfil", "laudo": "", "data": datetime.now().strftime("%d/%m/%Y")})
            
        historico[-1]["biometria"] = {
            "idade": self.idade_paciente, "sexo": self.sexo_paciente, "peso": self.peso_paciente,
            "objetivo": self.objetivo_paciente, "atividade": self.atividade_fisica
        }
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(historico, f, ensure_ascii=False, indent=4)
        return rx.window_alert("✅ Perfil salvo!")

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
            caminho = os.path.join(self.get_pasta_bd(), f"{self.paciente_ativo}.json")
            historico = []
            if os.path.exists(caminho):
                with open(caminho, 'r', encoding='utf-8') as f:
                    try: historico = json.load(f)
                    except: historico = []
            
            laudo_anterior = ""
            data_anterior = ""
            for registro in reversed(historico):
                if registro.get("laudo"):
                    laudo_anterior = registro["laudo"]
                    data_anterior = registro.get("data", "Consulta anterior")
                    break

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
            
            data_atual = datetime.now().strftime("%d/%m/%Y")
            historico.append({
                "modulo": self.modulo_analise, 
                "data": data_atual,
                "laudo": self.laudo_texto,
                "biometria": {
                    "idade": self.idade_paciente,
                    "sexo": self.sexo_paciente,
                    "peso": self.peso_paciente,
                    "objetivo": self.objetivo_paciente,
                    "atividade": self.atividade_fisica
                }
            })
            
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(historico, f, ensure_ascii=False, indent=4)

        except Exception as e: self.laudo_texto = f"Erro Crítico: {str(e)}"
        finally:
            self.em_processamento = False
            yield 

    def baixar_pdf(self):
        if not self.laudo_texto: return rx.window_alert("Não há laudo para descarregar.")
        pdf_bytes = gerar_pdf_simples(self.laudo_texto, self.paciente_ativo)
        return rx.download(data=pdf_bytes, filename=f"Dossie_{self.paciente_ativo.replace(' ', '_')}.pdf")