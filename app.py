import streamlit as st
import pandas as pd
import base64
import datetime

from database.db import (
    conectar,
    criar_tabela,
    criar_usuario,
    obter_paciente,
    salvar_paciente,
    listar_pacientes_do_responsavel,
    inserir_medicao,
    obter_usuario_por_token,
    remover_sessao
)
from models.previsao import prever_risco, carregar_metricas
from utils.estilo import aplicar_tema
from utils.autenticacao import exibir_autenticacao
from utils.auth import gerar_hash_senha
from utils.perfil import render_perfil
from utils.sessao import obter_param, limpar_params

criar_tabela()


def calcular_idade(data_nascimento):
    """Calcula a idade (anos completos) a partir de uma data 'dd/mm/aaaa'.

    Retorna None se a data estiver vazia ou em formato inválido.
    """
    if not data_nascimento:
        return None
    try:
        nasc = datetime.datetime.strptime(data_nascimento.strip(), "%d/%m/%Y").date()
    except (ValueError, AttributeError):
        return None

    hoje = datetime.date.today()
    return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))


def calcular_imc(peso, altura):
    """Calcula o IMC (kg/m²) a partir de peso (kg) e altura (m). None se inválido."""
    if not peso or not altura or altura <= 0:
        return None
    return round(peso / (altura ** 2), 1)


def calcular_data_default(paciente):
    """Converte a data de nascimento salva ('dd/mm/aaaa') em date para o seletor.

    Retorna None quando não há cadastro ou a data é inválida (campo fica vazio).
    """
    if paciente and paciente.get("data_nascimento"):
        try:
            return datetime.datetime.strptime(
                paciente["data_nascimento"].strip(), "%d/%m/%Y"
            ).date()
        except (ValueError, AttributeError):
            return None
    return None


def render_campos_clinicos(prefixo, paciente=None):
    """Renderiza os campos clínicos do paciente e devolve os valores num dict.

    `prefixo` mantém as chaves dos widgets únicas (permite vários formulários na
    mesma página); `paciente` pré-preenche o formulário em edições.
    """
    col_foto, col_dados = st.columns([1, 3])

    with col_foto:
        if paciente and paciente.get("foto"):
            st.image(paciente["foto"], width=150)
        else:
            st.markdown(
                '<div style="width:150px;height:150px;border-radius:50%;'
                'background:linear-gradient(135deg,#2F6FED,#5B9BFF);'
                'display:flex;align-items:center;justify-content:center;'
                'font-size:3rem;">👤</div>',
                unsafe_allow_html=True
            )

        nova_foto = st.file_uploader(
            "Foto do paciente",
            type=["png", "jpg", "jpeg"],
            key=f"foto_{prefixo}"
        )

    with col_dados:
        nome = st.text_input(
            "Nome*",
            value=paciente["nome"] if paciente else "",
            key=f"nome_{prefixo}"
        )

        data_nascimento_dt = st.date_input(
            "Data de Nascimento*",
            value=calcular_data_default(paciente),
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
            format="DD/MM/YYYY",
            key=f"nasc_{prefixo}"
        )

        if data_nascimento_dt:
            idade = calcular_idade(data_nascimento_dt.strftime("%d/%m/%Y"))
            st.caption(f"Idade: **{idade} anos** (calculada automaticamente)")

    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        opcoes_genero = ["Feminino", "Masculino"]
        idx_genero = (
            opcoes_genero.index(paciente["genero"])
            if paciente and paciente.get("genero") in opcoes_genero
            else 0
        )
        genero = st.selectbox("Gênero*", opcoes_genero, index=idx_genero, key=f"genero_{prefixo}")

    with col_g2:
        peso = st.number_input(
            "Peso (kg)", min_value=0.0, max_value=400.0, step=0.1,
            value=float(paciente["peso"]) if paciente and paciente.get("peso") else 0.0,
            key=f"peso_{prefixo}"
        )

    with col_g3:
        altura = st.number_input(
            "Altura (m)", min_value=0.0, max_value=2.5, step=0.01,
            value=float(paciente["altura"]) if paciente and paciente.get("altura") else 0.0,
            key=f"altura_{prefixo}"
        )

    imc = calcular_imc(peso, altura)
    if imc:
        st.caption(f"IMC: **{imc} kg/m²** (calculado automaticamente)")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        opcoes_status = ["Ativo", "Inativo"]
        idx_status = (
            opcoes_status.index(paciente["status"])
            if paciente and paciente.get("status") in opcoes_status
            else 0
        )
        status = st.selectbox("Status", opcoes_status, index=idx_status, key=f"status_{prefixo}")

    with col_s2:
        numero_sus = st.text_input(
            "Número do Cartão SUS",
            value=paciente["numero_sus"] if paciente else "",
            key=f"sus_{prefixo}"
        )

    medicacoes = st.text_area(
        "Medicamentos (separe por vírgula)",
        value=paciente["medicacoes"] if paciente else "",
        placeholder="Ex: Insulina, Metformina",
        key=f"med_{prefixo}"
    )

    return {
        "nome": nome,
        "data_nascimento_dt": data_nascimento_dt,
        "genero": genero,
        "peso": peso,
        "altura": altura,
        "status": status,
        "numero_sus": numero_sus,
        "medicacoes": medicacoes,
        "nova_foto": nova_foto,
    }


def persistir_paciente(id_alvo, dados, responsavel_id=None):
    """Valida e salva os dados clínicos de um formulário. Retorna True se salvou."""
    if not dados["nome"].strip() or dados["data_nascimento_dt"] is None:
        st.warning("Preencha ao menos o Nome e a Data de Nascimento.")
        return False

    foto_bytes = dados["nova_foto"].read() if dados["nova_foto"] is not None else None

    salvar_paciente(
        id_alvo,
        dados["nome"].strip(),
        dados["data_nascimento_dt"].strftime("%d/%m/%Y"),
        dados["numero_sus"].strip(),
        dados["medicacoes"].strip(),
        genero=dados["genero"],
        peso=dados["peso"] if dados["peso"] > 0 else None,
        altura=dados["altura"] if dados["altura"] > 0 else None,
        status=dados["status"],
        foto=foto_bytes,
        responsavel_id=responsavel_id
    )
    return True

st.set_page_config(
    page_title="Glicuidado",
    layout="wide"
)

aplicar_tema()

# --------------------------------------------------------------------------
# AUTENTICAÇÃO
# --------------------------------------------------------------------------
# Restaura a sessão persistente a partir do token na URL (sobrevive ao F5).
if "usuario_logado" not in st.session_state:
    token = obter_param("sid")
    if token:
        usuario_restaurado = obter_usuario_por_token(token)
        if usuario_restaurado:
            st.session_state["usuario_logado"] = usuario_restaurado
        else:
            # Token inválido ou expirado: limpa a URL.
            limpar_params()

if "usuario_logado" not in st.session_state:
    exibir_autenticacao()
    st.stop()

usuario = st.session_state["usuario_logado"]

# --------------------------------------------------------------------------
# APP (usuário autenticado)
# --------------------------------------------------------------------------
# Tipo de conta: 'Profissional' (enfermeiro/cuidador) administra vários
# pacientes; 'Paciente' gerencia apenas o próprio histórico.
eh_profissional = usuario.get("tipo") == "Profissional"

# Pacientes administrados pelo profissional (alimenta o seletor da sidebar).
lista_pacientes = listar_pacientes_do_responsavel(usuario["id"]) if eh_profissional else []

# Identidade exibida no cabeçalho da sidebar (avatar/nome).
paciente_perfil = None if eh_profissional else obter_paciente(usuario["id"])

if eh_profissional:
    nome_cabecalho = usuario.get("nome_exibicao") or usuario["email"]
else:
    nome_cabecalho = (
        paciente_perfil["nome"] if paciente_perfil and paciente_perfil.get("nome")
        else (usuario.get("nome_exibicao") or usuario["email"])
    )

st.title("🩺 Glicuidado")

primeiro_nome = nome_cabecalho.split()[0] if nome_cabecalho else ""

with st.sidebar:

    # Avatar clicável -> abre o perfil
    if paciente_perfil and paciente_perfil.get("foto"):
        foto_b64 = base64.b64encode(paciente_perfil["foto"]).decode("utf-8")
        avatar_html = f'<img src="data:image/png;base64,{foto_b64}" class="gc-avatar-img" />'
    else:
        avatar_html = (
            '<div class="gc-avatar-img" style="display:flex;align-items:center;'
            'justify-content:center;background:linear-gradient(135deg,#2F6FED,#5B9BFF);'
            'font-size:1.5rem;">👤</div>'
        )

    st.markdown(
        f'<div class="gc-avatar-wrapper">{avatar_html}</div>',
        unsafe_allow_html=True
    )

    if st.button("Editar Perfil", key="btn_abrir_perfil", use_container_width=True):
        st.session_state["mostrar_perfil"] = True
        st.rerun()

    st.markdown(f'<div class="gc-welcome-text">Bem Vindo, {primeiro_nome}</div>', unsafe_allow_html=True)

    # Profissional: seletor do paciente atualmente em atendimento.
    if eh_profissional:
        st.markdown('<div class="gc-menu-section">Paciente em atendimento</div>', unsafe_allow_html=True)

        if lista_pacientes:
            ids_pacientes = [p["usuario_id"] for p in lista_pacientes]
            rotulos = {p["usuario_id"]: f'{p["nome"]} · {p["status"]}' for p in lista_pacientes}

            atual = st.session_state.get("paciente_alvo_id")
            indice = ids_pacientes.index(atual) if atual in ids_pacientes else 0

            selecionado = st.selectbox(
                "Paciente em atendimento",
                ids_pacientes,
                index=indice,
                format_func=lambda i: rotulos.get(i, "—"),
                label_visibility="collapsed",
                key="sel_paciente_alvo",
            )
            st.session_state["paciente_alvo_id"] = selecionado
        else:
            st.caption("Nenhum paciente cadastrado. Use **Meus Pacientes**.")
            st.session_state["paciente_alvo_id"] = None

    st.markdown('<div class="gc-menu-section">Saúde</div>', unsafe_allow_html=True)

    if eh_profissional:
        todas_opcoes = [
            "Meus Pacientes",
            "Cadastrar Medição",
            "Predição IA",
            "Dashboard",
            "Gerar Relatório",
        ]
    else:
        todas_opcoes = [
            "Cadastro de Paciente",
            "Cadastrar Medição",
            "Predição IA",
            "Dashboard",
            "Gerar Relatório",
        ]

    icones_menu = {
        "Meus Pacientes": "👥",
        "Cadastro de Paciente": "🧑‍⚕️",
        "Cadastrar Medição": "🩸",
        "Predição IA": "🤖",
        "Dashboard": "📊",
        "Gerar Relatório": "📥",
    }

    menu = st.radio(
        "Menu",
        todas_opcoes,
        format_func=lambda opcao: f"{icones_menu.get(opcao, '')}  {opcao}",
        label_visibility="collapsed"
    )

    # Espaçador para empurrar o botão "Sair" para o final da sidebar
    st.markdown('<div class="gc-sidebar-spacer"></div>', unsafe_allow_html=True)

    if st.button("Sair", use_container_width=True, key="btn_sair"):
        token = obter_param("sid")
        if token:
            remover_sessao(token)
        limpar_params()
        del st.session_state["usuario_logado"]
        st.session_state.pop("mostrar_perfil", None)
        st.session_state.pop("paciente_alvo_id", None)
        st.rerun()

# --------------------------------------------------------------------------
# CONTEXTO DO PACIENTE-ALVO (quem é alvo das medições/predições/relatórios)
# --------------------------------------------------------------------------
if eh_profissional:
    id_alvo = st.session_state.get("paciente_alvo_id")
    paciente = obter_paciente(id_alvo) if id_alvo else None
else:
    id_alvo = usuario["id"]
    paciente = paciente_perfil

nome_paciente = (
    paciente["nome"] if paciente and paciente.get("nome")
    else (usuario.get("nome_exibicao") or usuario["email"])
)

# --------------------------------------------------------------------------
# TELA DE PERFIL (sobrepõe o conteúdo principal quando aberta)
# --------------------------------------------------------------------------
if st.session_state.get("mostrar_perfil"):

    if st.button("← Voltar"):
        st.session_state["mostrar_perfil"] = False
        st.rerun()

    render_perfil(usuario)

    st.stop()

# --------------------------------------------------------------------------
# MEUS PACIENTES (profissional): edita o selecionado e cadastra novos logins
# --------------------------------------------------------------------------
if menu == "Meus Pacientes":

    st.header("👥 Meus Pacientes")

    if paciente is not None:
        st.subheader(f"Editar dados de {paciente['nome']}")
        dados = render_campos_clinicos("edit", paciente)
        st.caption("* Campos obrigatórios")

        if st.button("Salvar Alterações"):
            if persistir_paciente(id_alvo, dados):
                st.success("Dados atualizados com sucesso.")
                st.rerun()
    else:
        st.info("Selecione um paciente na barra lateral ou cadastre um novo abaixo.")

    st.divider()
    st.subheader("➕ Cadastrar novo paciente")
    st.caption(
        "Cria um **login próprio** para o paciente, vinculado a você como responsável."
    )

    # st.form envia todos os campos juntos no clique (leitura atômica), evitando
    # que valores preenchidos pelo navegador (autofill) cheguem vazios.
    with st.form("form_novo_paciente"):

        nome_novo = st.text_input("Nome do paciente*", key="novo_nome")

        col_login1, col_login2 = st.columns(2)
        with col_login1:
            email_novo = st.text_input("Email de acesso*", key="novo_email")
        with col_login2:
            senha_nova = st.text_input("Senha de acesso*", type="password", key="nova_senha")

        data_nova = st.date_input(
            "Data de Nascimento*",
            value=None,
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.date.today(),
            format="DD/MM/YYYY",
            key="nova_data"
        )

        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            genero_novo = st.selectbox("Gênero*", ["Feminino", "Masculino"], key="novo_genero")
        with col_n2:
            peso_novo = st.number_input(
                "Peso (kg)", min_value=0.0, max_value=400.0, step=0.1, value=0.0, key="novo_peso"
            )
        with col_n3:
            altura_nova = st.number_input(
                "Altura (m)", min_value=0.0, max_value=2.5, step=0.01, value=0.0, key="nova_altura"
            )

        col_n4, col_n5 = st.columns(2)
        with col_n4:
            sus_novo = st.text_input("Número do Cartão SUS", key="novo_sus")
        with col_n5:
            medicacoes_novas = st.text_input(
                "Medicamentos (separe por vírgula)",
                placeholder="Ex: Insulina, Metformina", key="novas_med"
            )

        st.caption("* Campos obrigatórios")

        enviado = st.form_submit_button("Cadastrar Paciente")

    if enviado:

        faltando = []
        if not nome_novo.strip():
            faltando.append("Nome")
        if not email_novo.strip():
            faltando.append("Email")
        if not senha_nova:
            faltando.append("Senha")
        if data_nova is None:
            faltando.append("Data de Nascimento")

        if faltando:
            st.warning("Preencha o(s) campo(s): " + ", ".join(faltando) + ".")
        elif len(senha_nova) < 6:
            st.error("A senha deve ter pelo menos 6 caracteres.")
        else:
            novo_id = criar_usuario(
                email_novo.strip().lower(),
                gerar_hash_senha(senha_nova),
                nome_novo.strip(),
                "Paciente",
                "Paciente"
            )

            if novo_id is None:
                st.error("Este email já está cadastrado.")
            else:
                salvar_paciente(
                    novo_id,
                    nome_novo.strip(),
                    data_nova.strftime("%d/%m/%Y"),
                    sus_novo.strip(),
                    medicacoes_novas.strip(),
                    genero=genero_novo,
                    peso=peso_novo if peso_novo > 0 else None,
                    altura=altura_nova if altura_nova > 0 else None,
                    status="Ativo",
                    responsavel_id=usuario["id"]
                )
                st.session_state["paciente_alvo_id"] = novo_id
                st.success(f"Paciente {nome_novo.strip()} cadastrado e selecionado.")
                st.rerun()

    if lista_pacientes:
        st.divider()
        st.subheader("Pacientes cadastrados")
        df_pacientes = pd.DataFrame(
            [
                {"Nome": p["nome"], "Status": p["status"], "Email de acesso": p["email"]}
                for p in lista_pacientes
            ]
        )
        st.dataframe(df_pacientes, use_container_width=True, hide_index=True)

# --------------------------------------------------------------------------
# CADASTRO DE PACIENTE (conta do tipo Paciente edita os próprios dados)
# --------------------------------------------------------------------------
elif menu == "Cadastro de Paciente":

    st.header("Cadastro de Paciente")

    if paciente is None:
        st.info("Preencha os dados do paciente para liberar todos os recursos do app.")

    dados = render_campos_clinicos("self", paciente)
    st.caption("* Campos obrigatórios")

    if st.button("Salvar Cadastro"):
        if persistir_paciente(id_alvo, dados):
            st.success("Cadastro salvo com sucesso.")
            st.rerun()

# --------------------------------------------------------------------------
# CADASTRAR MEDIÇÃO
# --------------------------------------------------------------------------
elif menu == "Cadastrar Medição":

    st.header("Registro de Glicemia")

    if id_alvo is None:
        st.warning("Selecione um paciente na barra lateral (ou cadastre em **Meus Pacientes**).")
        st.stop()

    st.caption(f"Paciente: **{nome_paciente}**")

    # Limite de glicemia clinicamente plausível (igual ao da Predição IA).
    glicemia = st.number_input(
        "Glicemia (mg/dL)",
        min_value=40,
        max_value=400,
        value=120
    )

    medicacao = st.selectbox(
        "Tomou medicação?",
        ["Sim", "Não"]
    )

    data_registro = None
    medicacao_nome = ""
    medicacao_dosagem = ""

    if medicacao == "Sim":

        col_data, col_hora = st.columns(2)

        with col_data:
            data_medicao = st.date_input(
                "Data da medição",
                value=datetime.date.today(),
                max_value=datetime.date.today(),
                format="DD/MM/YYYY"
            )

        with col_hora:
            hora_medicao = st.time_input(
                "Horário da medição",
                value=datetime.datetime.now().time()
            )

        data_registro = datetime.datetime.combine(
            data_medicao, hora_medicao
        ).strftime("%Y-%m-%d %H:%M:%S")

        col_med, col_dose = st.columns(2)

        with col_med:
            medicacao_nome = st.text_input(
                "Nome da medicação",
                placeholder="Ex: Insulina"
            )

        with col_dose:
            medicacao_dosagem = st.text_input(
                "Dosagem administrada",
                placeholder="Ex: 10 UI"
            )

    atividade = st.selectbox(
        "Praticou atividade física?",
        ["Sim", "Não"]
    )

    jejum = st.selectbox(
        "Foi ingerido em jejum?",
        ["Sim", "Não"]
    )

    refeicao = None

    if jejum == "Não":
        refeicao = st.selectbox(
            "Qual refeição?",
            ["Café da manhã", "Almoço", "Café da tarde", "Jantar"]
        )

    if st.button("Salvar"):

        inserir_medicao(
            id_alvo,
            glicemia,
            1 if medicacao == "Sim" else 0,
            medicacao_nome.strip(),
            medicacao_dosagem.strip(),
            1 if atividade == "Sim" else 0,
            1 if jejum == "Sim" else 0,
            refeicao,
            data_registro
        )

        st.success("Registro salvo com sucesso.")

# --------------------------------------------------------------------------
# PREDIÇÃO IA — Risco de Diabetes
# --------------------------------------------------------------------------
elif menu == "Predição IA":

    st.header("Predição de Risco de Diabetes")

    if id_alvo is None:
        st.warning("Selecione um paciente na barra lateral (ou cadastre em **Meus Pacientes**).")
        st.stop()

    st.caption(f"Paciente: **{nome_paciente}**")

    metricas = carregar_metricas()

    if metricas is None:
        st.warning(
            "Modelo ainda não treinado. Execute `python models/treino_modelo.py` "
            "para gerar o modelo antes de usar a Predição IA."
        )

    else:
        st.info(
            f"Modelo em uso: **{metricas['melhor_modelo']}**  ·  "
            f"ROC-AUC (teste): **{metricas['teste']['roc_auc']:.2f}**  ·  "
            f"Recall: **{metricas['teste']['recall_positivo']:.2f}**"
        )

        # Dados puxados automaticamente do Cadastro de Paciente.
        genero_paciente = paciente.get("genero") if paciente else ""
        sexo_valor = 1 if genero_paciente == "Masculino" else 0
        idade_auto = calcular_idade(paciente.get("data_nascimento")) if paciente else None
        imc_auto = (
            calcular_imc(paciente.get("peso"), paciente.get("altura"))
            if paciente else None
        )

        st.markdown(
            "Estimativa a partir do **perfil e estilo de vida** "
            "(modelo treinado com a PNS 2019 — IBGE):"
        )

        col1, col2 = st.columns(2)

        with col1:
            # Idade — automática a partir da data de nascimento do cadastro.
            if idade_auto:
                idade = idade_auto
                st.number_input(
                    "Idade — do cadastro", value=int(idade_auto), disabled=True
                )
            else:
                idade = st.number_input("Idade", min_value=18, max_value=120, value=40)

            # IMC — automático a partir do peso e altura do cadastro.
            if imc_auto:
                imc = imc_auto
                st.number_input(
                    "IMC (kg/m²) — calculado do cadastro",
                    value=float(imc_auto), disabled=True
                )
            else:
                imc = st.number_input(
                    "IMC (kg/m²)", min_value=10.0, max_value=70.0, value=26.0, step=0.1
                )
                st.caption(
                    "Informe peso e altura no **Cadastro de Paciente** para o "
                    "IMC ser calculado automaticamente."
                )

            # Sexo — vem do gênero do cadastro.
            st.caption(f"Sexo (do cadastro): **{genero_paciente or '—'}**")

        with col2:
            hipertensao = st.selectbox(
                "Tem diagnóstico de hipertensão (pressão alta)?", ["Não", "Sim"]
            )
            atividade_fisica = st.selectbox(
                "Pratica atividade física regularmente?", ["Não", "Sim"]
            )
            tabagismo = st.selectbox("É fumante?", ["Não", "Sim"])

        if st.button("Analisar Risco"):

            try:
                resultado = prever_risco(
                    {
                        "idade": idade,
                        "sexo": sexo_valor,
                        "imc": imc,
                        "hipertensao": 1 if hipertensao == "Sim" else 0,
                        "atividade_fisica": 1 if atividade_fisica == "Sim" else 0,
                        "tabagismo": 1 if tabagismo == "Sim" else 0,
                    }
                )

                prob = resultado["probabilidade"]

                # Evita exibir "0%"/"100%", que passam falsa certeza absoluta.
                if prob < 0.01:
                    prob_txt = "<1%"
                elif prob > 0.99:
                    prob_txt = ">99%"
                else:
                    prob_txt = f"{prob:.0%}"

                if resultado["classe"] == 1:
                    st.error(f"⚠️ Risco de Diabetes — probabilidade estimada: {prob_txt}")
                else:
                    st.success(f"✅ Baixo risco — probabilidade estimada: {prob_txt}")

                st.progress(prob)

                # Explicabilidade: fatores globais mais influentes no modelo.
                importancias = metricas.get("importancia_features", {})
                if importancias:
                    top = sorted(
                        importancias.items(), key=lambda kv: kv[1], reverse=True
                    )[:3]
                    st.caption(
                        "Fatores que mais pesam na decisão do modelo: "
                        + ", ".join(f"**{nome}**" for nome, _ in top)
                    )

                st.caption(
                    "⚕️ Esta estimativa é uma ferramenta de apoio e **não substitui** "
                    "avaliação médica. Consulte um profissional de saúde."
                )

            except FileNotFoundError as e:
                st.error(str(e))

# --------------------------------------------------------------------------
# DASHBOARD (inclui o histórico de registros)
# --------------------------------------------------------------------------
elif menu == "Dashboard":

    from dashboards.dashboard import render_dashboard

    st.header("📊 Dashboard")

    if id_alvo is None:
        st.warning("Selecione um paciente na barra lateral (ou cadastre em **Meus Pacientes**).")
        st.stop()

    st.caption(f"Paciente: **{nome_paciente}**")

    render_dashboard(id_alvo)

# --------------------------------------------------------------------------
# GERAR RELATÓRIO
# --------------------------------------------------------------------------
elif menu == "Gerar Relatório":

    st.header("Gerar Relatório")

    if id_alvo is None:
        st.warning("Selecione um paciente na barra lateral (ou cadastre em **Meus Pacientes**).")
        st.stop()

    st.caption(f"Paciente: **{nome_paciente}**")

    st.write(
        "Baixe um arquivo CSV com todas as suas medições registradas. "
        "Você pode mostrar ou imprimir esse arquivo para apresentar ao seu médico."
    )

    conn = conectar()

    # A exportação reflete os campos atuais: nome e dosagem da medicação
    # (substituem a antiga lista de medicações), além de manter o legado.
    df = pd.read_sql(
        """
        SELECT
            data_registro AS "Data/Hora",
            glicemia AS "Glicemia (mg/dL)",
            CASE medicacao WHEN 1 THEN 'Sim' ELSE 'Não' END AS "Tomou Medicação",
            COALESCE(NULLIF(medicacao_nome, ''), medicacoes_utilizadas, '-') AS "Medicação",
            COALESCE(NULLIF(medicacao_dosagem, ''), '-') AS "Dosagem",
            CASE atividade WHEN 1 THEN 'Sim' ELSE 'Não' END AS "Atividade Física",
            CASE jejum WHEN 1 THEN 'Sim' ELSE 'Não' END AS "Jejum",
            COALESCE(refeicao, '-') AS "Refeição"
        FROM glicemia
        WHERE usuario_id = ?
        ORDER BY id DESC
        """,
        conn,
        params=(id_alvo,)
    )

    conn.close()

    if len(df) == 0:
        st.warning("Nenhuma medição registrada ainda.")
    else:
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            label="📥 Baixar Relatório (CSV)",
            data=csv,
            file_name=f"relatorio_glicuidado_{nome_paciente.replace(' ', '_')}.csv",
            mime="text/csv"
        )
