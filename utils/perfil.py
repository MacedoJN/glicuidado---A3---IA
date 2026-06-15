import streamlit as st

from database.db import atualizar_email_usuario, atualizar_conta_usuario


def render_perfil(usuario):
    """Tela de conta do usuário (login).

    Os dados clínicos do paciente (nome, nascimento, gênero, peso, altura,
    medicamentos, foto, SUS) ficam na aba 'Cadastro de Paciente'. Aqui ficam
    apenas os dados da conta: nome de exibição, função e email.
    """

    st.header("Perfil do Usuário")

    st.caption(
        "Dados da sua conta. Os dados clínicos do paciente ficam na aba "
        "**Cadastro de Paciente**."
    )

    nome_exibicao = st.text_input(
        "Nome de exibição",
        value=usuario.get("nome_exibicao") or "",
        placeholder="Como quer ser chamado"
    )

    funcao = st.text_input(
        "Função",
        value=usuario.get("funcao") or "",
        placeholder="Ex: Paciente, Enfermeiro(a), Cuidador(a)"
    )

    email = st.text_input(
        "Email",
        value=usuario["email"]
    )

    if st.button("Salvar Alterações"):

        if not email.strip():
            st.warning("O email não pode ficar em branco.")
        else:
            atualizar_conta_usuario(
                usuario["id"],
                nome_exibicao.strip(),
                funcao.strip()
            )

            usuario["nome_exibicao"] = nome_exibicao.strip()
            usuario["funcao"] = funcao.strip()

            if email.strip().lower() != usuario["email"]:
                ok = atualizar_email_usuario(usuario["id"], email.strip().lower())

                if not ok:
                    st.error("Este email já está em uso por outra conta. As demais alterações foram salvas.")
                    st.session_state["usuario_logado"] = usuario
                    return

                usuario["email"] = email.strip().lower()

            st.session_state["usuario_logado"] = usuario
            st.success("Perfil atualizado com sucesso.")
            st.rerun()
