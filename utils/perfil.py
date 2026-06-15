import streamlit as st

from database.db import obter_paciente, salvar_paciente, atualizar_email_usuario


def render_perfil(usuario):

    st.header("Perfil do Usuário")

    paciente = obter_paciente(usuario["id"])

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
            "Trocar foto",
            type=["png", "jpg", "jpeg"],
            key="upload_foto_perfil"
        )

    with col_dados:

        nome = st.text_input(
            "Nome",
            value=paciente["nome"] if paciente else ""
        )

        data_nascimento = st.text_input(
            "Data de Nascimento (dd/mm/aaaa)",
            value=paciente["data_nascimento"] if paciente else ""
        )

        email = st.text_input(
            "Email",
            value=usuario["email"]
        )

        numero_sus = st.text_input(
            "Número do Cartão SUS",
            value=paciente["numero_sus"] if paciente else ""
        )

        medicacoes = st.text_area(
            "Medicações utilizadas (separe por vírgula)",
            value=paciente["medicacoes"] if paciente else "",
            placeholder="Ex: Insulina, Metformina"
        )

    if st.button("Salvar Alterações"):

        if not nome.strip():
            st.warning("O nome não pode ficar em branco.")
        elif not email.strip():
            st.warning("O email não pode ficar em branco.")
        else:
            foto_bytes = nova_foto.read() if nova_foto is not None else None

            salvar_paciente(
                usuario["id"],
                nome.strip(),
                data_nascimento.strip(),
                numero_sus.strip(),
                medicacoes.strip(),
                foto_bytes
            )

            if email.strip().lower() != usuario["email"]:
                ok = atualizar_email_usuario(usuario["id"], email.strip().lower())

                if not ok:
                    st.error("Este email já está em uso por outra conta. As demais alterações foram salvas.")
                else:
                    usuario["email"] = email.strip().lower()
                    st.session_state["usuario_logado"] = usuario
                    st.success("Perfil atualizado com sucesso.")
                    st.rerun()
            else:
                st.success("Perfil atualizado com sucesso.")
                st.rerun()
