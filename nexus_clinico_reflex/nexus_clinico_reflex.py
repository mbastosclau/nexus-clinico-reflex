import reflex as rx
from .state import ClinicoState

def tela_login() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.hstack(
                rx.text("🧬", size="8"),
                rx.heading("Nexus Clínico", size="8", color="#38bdf8", weight="bold"),
                align_items="center", justify="center", width="100%"
            ),
            rx.text("Plataforma Comercial SaaS 🔗", size="4", color="#94a3b8", text_align="center", width="100%", margin_bottom="4"),
            
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("🔐 Entrar no Sistema", value="login", color="#e2e8f0"),
                    rx.tabs.trigger("📝 Criar Conta", value="registro", color="#e2e8f0"),
                    width="100%", justify_content="center"
                ),
                rx.tabs.content(
                    rx.vstack(
                        rx.text("E-mail Profissional:", color="#f8fafc", weight="bold"),
                        rx.input(
                            placeholder="seu@email.com", 
                            on_change=ClinicoState.set_email_login, 
                            width="100%", size="3", 
                            background_color="white", color="#0f172a", border_radius="8px"
                        ),
                        rx.text("Senha:", color="#f8fafc", weight="bold", margin_top="2"),
                        rx.input(
                            placeholder="••••••••", type="password", 
                            on_change=ClinicoState.set_senha_login, 
                            width="100%", size="3", 
                            background_color="white", color="#0f172a", border_radius="8px"
                        ),
                        rx.button("Acessar Plataforma", on_click=ClinicoState.fazer_login, width="100%", size="3", background_color="#38bdf8", color="#0f172a", weight="bold", margin_top="4"),
                        width="100%", align_items="start"
                    ),
                    value="login", padding_top="5"
                ),
                rx.tabs.content(
                    rx.vstack(
                        rx.text("Nome Completo:", color="#f8fafc", weight="bold"),
                        rx.input(on_change=ClinicoState.set_nome_registro, width="100%", size="3", background_color="white", color="#0f172a", border_radius="8px"),
                        rx.text("E-mail de Trabalho:", color="#f8fafc", weight="bold", margin_top="2"),
                        rx.input(on_change=ClinicoState.set_email_login, width="100%", size="3", background_color="white", color="#0f172a", border_radius="8px"),
                        rx.text("Senha (mín. 6 dígitos):", color="#f8fafc", weight="bold", margin_top="2"),
                        rx.input(type="password", on_change=ClinicoState.set_senha_login, width="100%", size="3", background_color="white", color="#0f172a", border_radius="8px"),
                        rx.button("Registrar Profissional", on_click=ClinicoState.registrar_profissional, width="100%", size="3", background_color="#10b981", color="white", weight="bold", margin_top="4"),
                        width="100%", align_items="start"
                    ),
                    value="registro", padding_top="5"
                ),
                default_value="login",
                width="100%"
            ),
            width=["90%", "450px"],
            padding="8",
            background_color="#1e293b",
            border_radius="16px",
            border="1px solid #334155",
            box_shadow="0 10px 40px -10px rgba(0,0,0,0.7)"
        ),
        width="100vw", height="100vh", background_color="#0f172a"
    )

def menu_lateral() -> rx.Component:
    return rx.vstack(
        rx.heading("👥 Gestão de Pacientes", size="5", color="white", margin_bottom="4"),
        
        rx.radio(
            ["Selecionar Existente", "Novo Paciente"], 
            value=ClinicoState.modo_paciente, 
            on_change=ClinicoState.set_modo_paciente,
            color="white", margin_bottom="4"
        ),
        
        rx.cond(
            ClinicoState.modo_paciente == "Selecionar Existente",
            rx.vstack(
                rx.text("Escolha o Paciente:", color="#94a3b8"),
                rx.select(ClinicoState.lista_pacientes, value=ClinicoState.paciente_ativo, on_change=ClinicoState.set_paciente_ativo, width="100%"),
                align_items="start", width="100%"
            ),
            rx.vstack(
                rx.text("Nome do Novo Paciente:", color="#94a3b8"),
                rx.input(on_change=ClinicoState.set_novo_nome_paciente, width="100%", placeholder="Ex: João Silva"),
                rx.button("Criar Paciente", on_click=ClinicoState.confirmar_novo_paciente, width="100%", background_color="#38bdf8", color="#0f172a"),
                align_items="start", width="100%"
            )
        ),
        
        rx.divider(margin_y="6"),
        rx.heading("⚙️ Gestão de Dados", size="4", color="white", margin_bottom="4"),
        
        rx.cond(
            ClinicoState.paciente_ativo != "",
            rx.box(
                rx.text("⚠️ Zona de Perigo", color="#ef4444", weight="bold", margin_bottom="2"),
                rx.text("Apagar Paciente apagará todo o histórico e laudos.", size="1", color="#94a3b8", margin_bottom="2"),
                rx.button("🚨 Excluir Paciente", on_click=ClinicoState.excluir_paciente, width="100%", background_color="#7f1d1d", color="white"),
                border="1px solid #7f1d1d", padding="4", border_radius="8px", width="100%"
            ),
            rx.text("")
        ),
        
        width="300px", height="100vh", background_color="#1e293b", padding="6", align_items="start"
    )

def dashboard_principal() -> rx.Component:
    return rx.hstack(
        menu_lateral(),
        rx.vstack(
            rx.hstack(
                rx.heading("🧬 Nova Análise Laboratorial", size="7", color="#1e3a8a"),
                rx.spacer(),
                rx.button("🚪 Sair", on_click=ClinicoState.logout, color_scheme="red", variant="ghost"),
                width="100%", margin_bottom="6"
            ),
            
            rx.cond(
                ClinicoState.paciente_ativo == "",
                rx.callout("👈 Selecione ou crie um paciente no menu lateral para iniciar.", icon="info", color_scheme="blue", width="100%"),
                rx.vstack(
                    rx.text(f"Paciente Ativo: {ClinicoState.paciente_ativo}", size="5", weight="bold", color="#0369a1"),
                    
                    # BIOMETRIA COMPLETA
                    rx.card(
                        rx.vstack(
                            rx.heading("1. Perfil Biométrico e Objetivo", size="4", color="#334155"),
                            rx.hstack(
                                rx.box(rx.text("Idade"), rx.input(value=ClinicoState.idade_paciente, on_change=ClinicoState.set_idade_paciente)),
                                rx.box(rx.text("Sexo"), rx.select(["Masculino", "Feminino"], value=ClinicoState.sexo_paciente, on_change=ClinicoState.set_sexo_paciente)),
                                rx.box(rx.text("Peso (kg)"), rx.input(value=ClinicoState.peso_paciente, on_change=ClinicoState.set_peso_paciente)),
                                rx.box(
                                    rx.text("Objetivo Clínico/Esportivo"), 
                                    rx.select([
                                        "Emagrecimento (Foco Clínico / Síndrome Metabólica)", 
                                        "Manutenção / Saúde Geral", 
                                        "Hipertrofia Estrita (Ganho de Massa Magra)", 
                                        "Performance Atlética de Elite"
                                    ], value=ClinicoState.objetivo_paciente, on_change=ClinicoState.set_objetivo_paciente)
                                ),
                                width="100%"
                            ),
                            rx.hstack(
                                rx.box(
                                    rx.text("Treino/Atividade"), 
                                    rx.select([
                                        "Sedentário", 
                                        "Leve (1-2x sem)", 
                                        "Moderado (Musculação 3-4x)", 
                                        "Intenso (Musculação 5-6x)", 
                                        "Atleta de Elite"
                                    ], value=ClinicoState.atividade_fisica, on_change=ClinicoState.set_atividade_fisica), 
                                    width="50%"
                                ),
                                rx.box(
                                    rx.text("Módulo Clínico de Análise"), 
                                    rx.select([
                                        "Fisiologia do Esporte e Alta Performance",
                                        "Performance, Emagrecimento e Endocrinologia",
                                        "Microbiologia (Cultura e Antibiograma)",
                                        "Painel Completo (Bioquímica + Hematologia)",
                                        "Imunologia (Sorologias Básicas)",
                                        "Imunologia - Autoimunidade",
                                        "Imunologia - Alergias (IgE Específicas)",
                                        "Imunologia - Marcadores Tumorais",
                                        "Imunologia - Toxoplasmose",
                                        "Imunologia - COVID-19"
                                    ], value=ClinicoState.modulo_analise, on_change=ClinicoState.set_modulo_analise), 
                                    width="50%"
                                ),
                                width="100%"
                            ),
                            rx.button("💾 Salvar Perfil (Sem Exame)", on_click=ClinicoState.salvar_perfil_biometrico, color_scheme="gray", variant="outline", margin_top="2"),
                            rx.box(rx.text("Contexto (Opcional)"), rx.text_area(placeholder="Uso de medicamentos, sintomas, rotina alimentar...", 						                    on_change=ClinicoState.set_contexto_clinico, width="100%"), width="100%", margin_top="2"),
                            width="100%", align_items="start"
                        ),
                        width="100%", padding="5", margin_bottom="4"
                    ),
                    
                   # UPLOADS SEPARADOS
                    rx.card(
                        rx.vstack(
                            rx.heading("2. Importação de Exames", size="4", color="#334155"),
                            rx.text("Carregue os PDFs e clique em Confirmar. (Pode carregar vários PDFs de uma vez em cada categoria)", size="2", color="#64748b"),
                            
                            rx.hstack(
                                # CAIXA 1: SANGUE
                                rx.box(
                                    rx.text("🩸 Laboratoriais (Sangue)", size="2", weight="bold"),
                                    rx.upload(
                                        rx.text("Arraste exames de sangue", size="1"),
                                        id="up_sangue",
                                        multiple=True,
                                        border="1px dashed #cbd5e1", padding="2em", border_radius="6px"
                                    ),
                                    rx.button("Confirmar Sangue", on_click=ClinicoState.confirmar_sangue(rx.upload_files(upload_id="up_sangue")), size="1", color_scheme="red", margin_top="2", width="100%"),
                                    rx.foreach(ClinicoState.arquivos_sangue, lambda arq: rx.text("📄 " + arq, size="1", color="green")),
                                    width="50%"
                                ),
                                # CAIXA 2: BIOIMPEDÂNCIA
                                rx.box(
                                    rx.text("⚖️ Bioimpedância / Imagem", size="2", weight="bold"),
                                    rx.upload(
                                        rx.text("Arraste Bioimpedância", size="1"),
                                        id="up_bio",
                                        multiple=True,
                                        border="1px dashed #cbd5e1", padding="2em", border_radius="6px"
                                    ),
                                    rx.button("Confirmar Bio", on_click=ClinicoState.confirmar_bio(rx.upload_files(upload_id="up_bio")), size="1", color_scheme="blue", margin_top="2", width="100%"),
                                    rx.foreach(ClinicoState.arquivos_bio, lambda arq: rx.text("📄 " + arq, size="1", color="green")),
                                    width="50%"
                                ),
                                spacing="4", width="100%", align_items="start"
                            ),
                            
                            rx.button(
                                "PROCESSAR DOSSIÊ EXECUTIVO", 
                                on_click=ClinicoState.processar_laudo, 
                                loading=ClinicoState.em_processamento, 
                                width="100%", size="4", background_color="#1e3a8a", color="white", margin_top="4"
                            ),
                            width="100%"
                        ),
                        width="100%", padding="5", margin_bottom="4"
                    ),
                    
                    # RESULTADO E PDF
                    rx.cond(
                        ClinicoState.laudo_texto != "",
                        rx.card(
                            rx.vstack(
                                rx.heading("3. Dossiê Executivo Gerado", size="4", color="#16a34a"),
                                rx.markdown(ClinicoState.laudo_texto),
                                rx.button("Descarregar Dossiê em PDF", on_click=ClinicoState.baixar_pdf, width="100%", size="3", color_scheme="green"),
                                width="100%"
                            ),
                            width="100%", padding="5"
                        ),
                        rx.text("")
                    ),
                    width="100%", max_width="900px", margin="0 auto"
                ) # <-- ESTE FECHA O SEU VSTACK DA LINHA 124
            ), # <-- ESTE FECHA A CAIXA (BOX) PRINCIPAL DA TELA
            width="100%", height="100vh", overflow_y="auto", padding="10", background_color="#f8fafc"
        ),
        width="100vw", height="100vh"
    ) # <-- ESTE FECHA O CONDICIONAL DO PACIENTE ATIVO E O FICHEIRO
def index() -> rx.Component:
    return rx.cond(
        ClinicoState.esta_autenticado,
        dashboard_principal(),
        tela_login()
    )

app = rx.App()
app.add_page(index)