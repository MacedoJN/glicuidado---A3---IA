import streamlit as st

from database.db import (
    criar_usuario,
    obter_usuario_por_email,
    criar_sessao,
)
from utils.auth import gerar_hash_senha, verificar_senha
from utils.sessao import definir_param


def _ir_para(tela):
    st.session_state["tela_auth"] = tela
    st.rerun()


def tela_login():

    st.markdown('<div class="gc-auth-icon">👤</div>', unsafe_allow_html=True)
    st.markdown('<div class="gc-auth-title">Bem vindo ao Glicuidado</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="gc-auth-subtitle">Entre com suas credenciais para continuar</div>',
        unsafe_allow_html=True
    )

    _, col_centro, _ = st.columns([1, 2, 1])

    with col_centro:

        st.markdown('<div class="gc-field-label">Email</div>', unsafe_allow_html=True)
        email = st.text_input(
            "Email",
            placeholder="seu@email.com",
            label_visibility="collapsed",
            key="login_email"
        )

        st.markdown('<div class="gc-field-label">Senha</div>', unsafe_allow_html=True)
        senha = st.text_input(
            "Senha",
            placeholder="••••••••",
            type="password",
            label_visibility="collapsed",
            key="login_senha"
        )

        if st.button("Entrar", use_container_width=True):

            if not email.strip() or not senha:
                st.warning("Preencha email e senha.")
            else:
                usuario = obter_usuario_por_email(email.strip().lower())

                if usuario is None or not verificar_senha(senha, usuario["senha_hash"]):
                    st.error("Email ou senha inválidos.")
                else:
                    st.session_state["usuario_logado"] = {
                        "id": usuario["id"],
                        "email": usuario["email"],
                        "nome_exibicao": usuario["nome_exibicao"],
                        "funcao": usuario.get("funcao", ""),
                        "tipo": usuario.get("tipo", "Paciente")
                    }
                    # Cria sessão persistente e guarda o token na URL (sobrevive ao F5).
                    definir_param("sid", criar_sessao(usuario["id"]))
                    st.rerun()

        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("Criar conta", use_container_width=True, key="btn_ir_criar_conta"):
                _ir_para("cadastro")

        with col_b:
            if st.button("Esqueci minha senha", use_container_width=True, key="btn_esqueci_senha"):
                st.info(
                    "Recuperação de senha ainda não disponível. "
                    "Entre em contato com o suporte para redefinir sua senha."
                )

        st.markdown(
            '<div class="gc-auth-footer">🛡️ Seguro e Criptografado</div>',
            unsafe_allow_html=True
        )


def tela_cadastro():

    st.markdown('<div class="gc-auth-icon">🩺</div>', unsafe_allow_html=True)
    st.markdown('<div class="gc-auth-title">Criar Conta</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="gc-auth-subtitle">Preencha os dados abaixo</div>',
        unsafe_allow_html=True
    )

    _, col_centro, _ = st.columns([1, 2, 1])

    with col_centro:

        st.markdown(
            '<div class="gc-field-label">Nome de exibição '
            '<span class="gc-optional">(opcional)</span></div>',
            unsafe_allow_html=True
        )
        nome_exibicao = st.text_input(
            "Nome de exibição",
            placeholder="Como quer ser chamado",
            label_visibility="collapsed",
            key="cad_nome"
        )

        st.markdown(
            '<div class="gc-field-label">Tipo de conta</div>',
            unsafe_allow_html=True
        )
        tipo = st.selectbox(
            "Tipo de conta",
            ["Paciente", "Profissional de saúde"],
            label_visibility="collapsed",
            key="cad_tipo",
            help="Profissional de saúde (ex.: enfermeiro) pode cadastrar e "
                 "acompanhar vários pacientes."
        )

        st.markdown(
            '<div class="gc-field-label">Função '
            '<span class="gc-optional">(opcional)</span></div>',
            unsafe_allow_html=True
        )
        funcao = st.text_input(
            "Função",
            placeholder="Ex: Paciente, Enfermeiro(a), Cuidador(a)",
            label_visibility="collapsed",
            key="cad_funcao"
        )

        st.markdown('<div class="gc-field-label">Email</div>', unsafe_allow_html=True)
        email = st.text_input(
            "Email",
            placeholder="seu@email.com",
            label_visibility="collapsed",
            key="cad_email"
        )

        st.markdown('<div class="gc-field-label">Senha</div>', unsafe_allow_html=True)
        senha = st.text_input(
            "Senha",
            placeholder="••••••••",
            type="password",
            label_visibility="collapsed",
            key="cad_senha"
        )

        st.markdown('<div class="gc-field-label">Confirmar senha</div>', unsafe_allow_html=True)
        confirmar_senha = st.text_input(
            "Confirmar senha",
            placeholder="••••••••",
            type="password",
            label_visibility="collapsed",
            key="cad_confirmar_senha"
        )

        if st.button("Criar Conta", use_container_width=True):

            if not email.strip() or not senha or not confirmar_senha:
                st.warning("Preencha email e senha (e a confirmação).")
            elif senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            elif len(senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            else:
                senha_hash = gerar_hash_senha(senha)

                tipo_db = "Profissional" if tipo.startswith("Profissional") else "Paciente"

                novo_id = criar_usuario(
                    email.strip().lower(),
                    senha_hash,
                    nome_exibicao.strip(),
                    funcao.strip(),
                    tipo_db
                )

                if novo_id is None:
                    st.error("Este email já está cadastrado.")
                else:
                    st.success("Conta criada com sucesso! Faça login para continuar.")
                    _ir_para("login")

        st.markdown(
            '<div class="gc-switch-text">Já tem uma conta?</div>',
            unsafe_allow_html=True
        )

        if st.button("Entrar", use_container_width=True, key="btn_ir_login"):
            _ir_para("login")


def exibir_autenticacao():
    """Exibe a tela de login ou cadastro, controlando o estado da sessão."""

    if "tela_auth" not in st.session_state:
        st.session_state["tela_auth"] = "login"

    if st.session_state["tela_auth"] == "login":
        tela_login()
    else:
        tela_cadastro()
