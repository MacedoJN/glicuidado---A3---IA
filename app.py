import streamlit as st
import pandas as pd
import base64

from database.db import (
    conectar,
    criar_tabela,
    obter_paciente,
    salvar_paciente,
    obter_ultimo_registro,
    inserir_medicao
)
from models.previsao import prever
from utils.estilo import aplicar_tema
from utils.autenticacao import exibir_autenticacao
from utils.perfil import render_perfil

criar_tabela()

st.set_page_config(
    page_title="Glicuidado",
    layout="wide"
)

aplicar_tema()

# --------------------------------------------------------------------------
# AUTENTICAÇÃO
# --------------------------------------------------------------------------
if "usuario_logado" not in st.session_state:
    exibir_autenticacao()
    st.stop()

usuario = st.session_state["usuario_logado"]

paciente = obter_paciente(usuario["id"])

# --------------------------------------------------------------------------
# CADASTRO INICIAL DO PACIENTE (obrigatório antes de usar o app)
# --------------------------------------------------------------------------
if paciente is None:

    st.title("🩺 Glicuidado")

    st.header("Complete seu cadastro")

    st.info("Antes de continuar, precisamos de alguns dados sobre você.")

    nome = st.text_input(
        "Nome*",
        value=usuario["nome_exibicao"] or ""
    )

    data_nascimento = st.text_input(
        "Data de Nascimento* (dd/mm/aaaa)"
    )

    numero_sus = st.text_input(
        "Número do Cartão SUS*"
    )

    medicacoes = st.text_area(
        "Medicações utilizadas (separe por vírgula)",
        placeholder="Ex: Insulina, Metformina"
    )

    st.caption("* Campos obrigatórios")

    if st.button("Salvar e Continuar"):

        if not nome.strip() or not data_nascimento.strip() or not numero_sus.strip():
            st.warning("Preencha todos os campos obrigatórios (Nome, Data de Nascimento e Número do SUS).")
        else:
            salvar_paciente(
                usuario["id"],
                nome.strip(),
                data_nascimento.strip(),
                numero_sus.strip(),
                medicacoes.strip()
            )
            st.success("Cadastro salvo com sucesso.")
            st.rerun()

    st.stop()

# --------------------------------------------------------------------------
# APP (usuário autenticado e com perfil completo)
# --------------------------------------------------------------------------
st.title("🩺 Glicuidado")

primeiro_nome = paciente["nome"].split()[0] if paciente["nome"] else ""

with st.sidebar:

    # Avatar clicável -> abre o perfil
    if paciente.get("foto"):
        foto_b64 = base64.b64encode(paciente["foto"]).decode("utf-8")
        avatar_html = f'<img src="data:image/png;base64,{foto_b64}" class="gc-avatar-img" />'
    else:
        avatar_html = (
            '<div class="gc-avatar-img" style="display:flex;align-items:center;'
            'justify-content:center;background:linear-gradient(135deg,#2F6FED,#5B9BFF);'
            'font-size:1.5rem;">👤</div>'
        )

    st.markdown(avatar_html, unsafe_allow_html=True)

    if st.button("Editar Perfil", key="btn_abrir_perfil"):
        st.session_state["mostrar_perfil"] = True
        st.rerun()

    st.markdown(f'<div class="gc-welcome-text">Bem Vindo, {primeiro_nome}</div>', unsafe_allow_html=True)

    st.markdown('<div class="gc-menu-section">Paciente</div>', unsafe_allow_html=True)

    opcoes_paciente = ["Histórico"]

    st.markdown('<div class="gc-menu-section">Saúde</div>', unsafe_allow_html=True)

    opcoes_saude = ["Cadastrar Medição", "Predição IA", "Dashboard", "Gerar Relatório"]

    todas_opcoes = opcoes_paciente + opcoes_saude

    menu = st.radio(
        "Menu",
        todas_opcoes,
        label_visibility="collapsed"
    )

    # Espaçador para empurrar o botão "Sair" para o final da sidebar
    st.markdown('<div class="gc-sidebar-spacer"></div>', unsafe_allow_html=True)

    if st.button("Sair", use_container_width=True, key="btn_sair"):
        del st.session_state["usuario_logado"]
        st.session_state.pop("mostrar_perfil", None)
        st.rerun()

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
# CADASTRAR MEDIÇÃO
# --------------------------------------------------------------------------
if menu == "Cadastrar Medição":

    import datetime

    st.header("Registro de Glicemia")

    st.caption(f"Paciente: **{paciente['nome']}**")

    glicemia = st.number_input(
        "Glicemia",
        min_value=0,
        max_value=500
    )

    medicao_agora = st.selectbox(
        "Medição realizada agora?",
        ["Sim", "Não"]
    )

    data_registro = None

    if medicao_agora == "Não":

        col_data, col_hora = st.columns(2)

        with col_data:
            data_medicao = st.date_input(
                "Data da medição",
                value=datetime.date.today(),
                max_value=datetime.date.today()
            )

        with col_hora:
            hora_medicao = st.time_input(
                "Horário da medição",
                value=datetime.datetime.now().time()
            )

        data_registro = datetime.datetime.combine(data_medicao, hora_medicao).strftime("%Y-%m-%d %H:%M:%S")

    medicacao = st.selectbox(
        "Tomou medicação?",
        ["Sim", "Não"]
    )

    medicacoes_utilizadas = []

    if medicacao == "Sim":

        opcoes_medicacao = [
            m.strip() for m in paciente["medicacoes"].split(",") if m.strip()
        ]

        if opcoes_medicacao:
            medicacoes_utilizadas = st.multiselect(
                "Quais medicações foram utilizadas?",
                opcoes_medicacao
            )
        else:
            st.info(
                "Nenhuma medicação cadastrada no seu perfil. "
                "Acesse 'Editar Perfil' para cadastrar suas medicações."
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
            usuario["id"],
            glicemia,
            1 if medicacao == "Sim" else 0,
            ", ".join(medicacoes_utilizadas),
            1 if atividade == "Sim" else 0,
            1 if jejum == "Sim" else 0,
            refeicao,
            data_registro
        )

        st.success("Registro salvo com sucesso.")

# --------------------------------------------------------------------------
# PREDIÇÃO IA
# --------------------------------------------------------------------------
elif menu == "Predição IA":

    st.header("Predição de Hiperglicemia")

    ultimo = obter_ultimo_registro(usuario["id"])

    if ultimo is None:
        st.warning(
            "Nenhuma medição encontrada. "
            "Cadastre uma medição na aba 'Cadastrar Medição' antes de usar a Predição IA."
        )

    else:
        st.caption(f"Paciente: **{paciente['nome']}**")

        st.metric("Última glicemia registrada (mg/dL)", f"{ultimo['glicemia']:.0f}")
        st.caption(f"Registrado em: {ultimo['data_registro']}")

        medicacao = st.selectbox(
            "Tomou medicação?",
            ["Sim", "Não"]
        )

        atividade = st.selectbox(
            "Praticou atividade física?",
            ["Sim", "Não"]
        )

        if st.button("Analisar"):

            try:
                resultado = prever(
                    ultimo["glicemia"],
                    1 if medicacao == "Sim" else 0,
                    1 if atividade == "Sim" else 0
                )

                if resultado == 1:
                    st.error("⚠️ Risco de Hiperglicemia")
                else:
                    st.success("✅ Glicemia Controlada")

            except FileNotFoundError as e:
                st.error(str(e))

# --------------------------------------------------------------------------
# HISTÓRICO
# --------------------------------------------------------------------------
elif menu == "Histórico":

    st.header("Histórico de Registros")

    st.caption(f"Paciente: **{paciente['nome']}**")

    conn = conectar()

    df = pd.read_sql(
        "SELECT glicemia, medicacao, medicacoes_utilizadas, atividade, jejum, refeicao, data_registro "
        "FROM glicemia WHERE usuario_id = ? ORDER BY id DESC",
        conn,
        params=(usuario["id"],)
    )

    conn.close()

    st.dataframe(df)

# --------------------------------------------------------------------------
# DASHBOARD
# --------------------------------------------------------------------------
elif menu == "Dashboard":

    from dashboards.dashboard import render_dashboard

    st.header("📊 Dashboard")

    st.caption(f"Paciente: **{paciente['nome']}**")

    render_dashboard(usuario["id"])

# --------------------------------------------------------------------------
# GERAR RELATÓRIO
# --------------------------------------------------------------------------
elif menu == "Gerar Relatório":

    st.header("Gerar Relatório")

    st.caption(f"Paciente: **{paciente['nome']}**")

    st.write(
        "Baixe um arquivo CSV com todas as suas medições registradas. "
        "Você pode mostrar ou imprimir esse arquivo para apresentar ao seu médico."
    )

    conn = conectar()

    df = pd.read_sql(
        """
        SELECT
            data_registro AS "Data/Hora",
            glicemia AS "Glicemia (mg/dL)",
            CASE medicacao WHEN 1 THEN 'Sim' ELSE 'Não' END AS "Tomou Medicação",
            medicacoes_utilizadas AS "Medicações Utilizadas",
            CASE atividade WHEN 1 THEN 'Sim' ELSE 'Não' END AS "Atividade Física",
            CASE jejum WHEN 1 THEN 'Sim' ELSE 'Não' END AS "Jejum",
            COALESCE(refeicao, '-') AS "Refeição"
        FROM glicemia
        WHERE usuario_id = ?
        ORDER BY id DESC
        """,
        conn,
        params=(usuario["id"],)
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
            file_name=f"relatorio_glicuidado_{paciente['nome'].replace(' ', '_')}.csv",
            mime="text/csv"
        )
