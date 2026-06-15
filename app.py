import streamlit as st
import pandas as pd
import base64

from database.db import (
    conectar,
    criar_tabela,
    obter_paciente,
    salvar_paciente,
    obter_ultimo_registro,
    inserir_medicao,
    obter_usuario_por_token,
    remover_sessao
)
from models.previsao import prever_risco, carregar_metricas
from utils.estilo import aplicar_tema
from utils.autenticacao import exibir_autenticacao
from utils.perfil import render_perfil
from utils.sessao import obter_param, limpar_params

criar_tabela()

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

    st.markdown(
        f'<div class="gc-avatar-wrapper">{avatar_html}</div>',
        unsafe_allow_html=True
    )

    if st.button("Editar Perfil", key="btn_abrir_perfil", use_container_width=True):
        st.session_state["mostrar_perfil"] = True
        st.rerun()

    st.markdown(f'<div class="gc-welcome-text">Bem Vindo, {primeiro_nome}</div>', unsafe_allow_html=True)

    st.markdown('<div class="gc-menu-section">Saúde</div>', unsafe_allow_html=True)

    todas_opcoes = ["Cadastrar Medição", "Predição IA", "Dashboard", "Gerar Relatório"]

    icones_menu = {
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
# PREDIÇÃO IA — Risco de Diabetes
# --------------------------------------------------------------------------
elif menu == "Predição IA":

    st.header("Predição de Risco de Diabetes")
    st.caption(f"Paciente: **{paciente['nome']}**")

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

        # Pré-preenche a glicemia com a última medição do paciente, se houver,
        # limitando a uma faixa clinicamente plausível (40–400 mg/dL).
        ultimo = obter_ultimo_registro(usuario["id"])
        glicemia_default = int(ultimo["glicemia"]) if ultimo else 120
        glicemia_default = max(40, min(400, glicemia_default))

        st.markdown("Preencha os dados clínicos para estimar o risco de diabetes:")

        col1, col2 = st.columns(2)

        with col1:
            glicemia = st.number_input(
                "Glicemia (mg/dL)", min_value=40, max_value=400, value=glicemia_default
            )
            imc = st.number_input(
                "IMC (kg/m²)", min_value=0.0, max_value=70.0, value=28.0, step=0.1
            )
            idade = st.number_input("Idade", min_value=1, max_value=120, value=35)
            pressao_arterial = st.number_input(
                "Pressão arterial diastólica (mmHg)", min_value=0, max_value=200, value=72
            )

        with col2:
            gestacoes = st.number_input(
                "Nº de gestações", min_value=0, max_value=20, value=0
            )
            insulina = st.number_input(
                "Insulina sérica (mu U/ml)", min_value=0, max_value=900, value=0
            )
            dobra_cutanea = st.number_input(
                "Dobra cutânea do tríceps (mm)", min_value=0, max_value=100, value=20
            )
            hist_familiar = st.number_input(
                "Histórico familiar (função pedigree)",
                min_value=0.0,
                max_value=3.0,
                value=0.5,
                step=0.01,
            )

        if st.button("Analisar Risco"):

            try:
                resultado = prever_risco(
                    {
                        "gestacoes": gestacoes,
                        "glicemia": glicemia,
                        "pressao_arterial": pressao_arterial,
                        "dobra_cutanea": dobra_cutanea,
                        "insulina": insulina,
                        "imc": imc,
                        "hist_familiar": hist_familiar,
                        "idade": idade,
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
