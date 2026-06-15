import streamlit as st


def aplicar_tema():
    """Aplica o tema visual dark/azul do Glicuidado em toda a aplicação."""

    st.markdown("""
    <style>

    :root {
        --gc-bg: #0E1117;
        --gc-card: #181D29;
        --gc-card-border: #262C3B;
        --gc-primary: #2F6FED;
        --gc-primary-light: #5B9BFF;
        --gc-text: #E8EBF0;
        --gc-text-muted: #9AA4B5;
    }

    /* Fundo geral */
    .stApp {
        background-color: var(--gc-bg);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #11141D;
        border-right: 1px solid var(--gc-card-border);
    }

    /* Cartão de autenticação */
    .gc-auth-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding-top: 2.5rem;
    }

    .gc-auth-icon {
        width: 64px;
        height: 64px;
        border-radius: 16px;
        background: linear-gradient(135deg, var(--gc-primary), var(--gc-primary-light));
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        margin-bottom: 1.25rem;
        box-shadow: 0 8px 24px rgba(47, 111, 237, 0.35);
    }

    .gc-auth-title {
        color: var(--gc-text);
        font-size: 1.75rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.25rem;
    }

    .gc-auth-subtitle {
        color: var(--gc-text-muted);
        font-size: 0.95rem;
        text-align: center;
        margin-bottom: 1.75rem;
    }

    .gc-auth-card {
        background-color: var(--gc-card);
        border: 1px solid var(--gc-card-border);
        border-radius: 16px;
        padding: 2rem;
        width: 100%;
        max-width: 420px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.35);
    }

    .gc-field-label {
        color: var(--gc-text);
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        margin-bottom: 0.35rem;
    }

    .gc-optional {
        color: var(--gc-text-muted);
        font-weight: 400;
        text-transform: none;
        font-size: 0.8rem;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        background-color: #11141D !important;
        border: 1px solid var(--gc-card-border) !important;
        color: var(--gc-text) !important;
        border-radius: 10px !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: var(--gc-primary) !important;
        box-shadow: 0 0 0 1px var(--gc-primary) !important;
    }

    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #5C6577 !important;
    }

    /* Botão primário (gradiente azul) */
    .stButton > button[kind="primary"], .stButton > button {
        background: linear-gradient(135deg, var(--gc-primary), var(--gc-primary-light));
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1rem;
        transition: opacity 0.15s ease;
    }

    .stButton > button:hover {
        opacity: 0.9;
        color: #FFFFFF;
    }

    /* Links de troca entre login/cadastro */
    .gc-switch-text {
        color: var(--gc-text-muted);
        text-align: center;
        margin-top: 1.25rem;
        font-size: 0.9rem;
    }

    /* Cabeçalhos de seção do menu lateral */
    .gc-menu-section {
        color: var(--gc-text-muted);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin: 1rem 0 0.35rem 0.25rem;
    }

    /* Rodapé da tela de login */
    .gc-auth-footer {
        color: var(--gc-text-muted);
        text-align: center;
        margin-top: 1.5rem;
        font-size: 0.85rem;
    }

    /* Avatar do usuário na sidebar */
    .gc-avatar-img {
        border-radius: 50%;
        object-fit: cover;
        width: 56px;
        height: 56px;
        border: 2px solid var(--gc-primary);
    }

    .gc-welcome-text {
        color: var(--gc-text);
        font-weight: 600;
        font-size: 1rem;
        margin-top: 0.5rem;
    }

    /* Faz o conteúdo da sidebar ocupar a altura toda em coluna,
       permitindo empurrar o botão "Sair" para o final via spacer flex-grow. */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        min-height: calc(100vh - 2rem);
    }

    .gc-sidebar-spacer {
        flex-grow: 1;
    }

    </style>
    """, unsafe_allow_html=True)
