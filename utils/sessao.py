"""
Camada de compatibilidade para parâmetros de URL (query params) no Streamlit.

A API estável `st.query_params` só existe a partir do Streamlit 1.30. Em versões
anteriores usa-se `st.experimental_get_query_params` / `set`. Estas funções
escolhem automaticamente a API disponível, evitando `AttributeError`.
"""

import streamlit as st


def obter_param(chave):
    """Retorna o valor de um query param (ou None)."""
    if hasattr(st, "query_params"):
        return st.query_params.get(chave)

    valores = st.experimental_get_query_params().get(chave)
    return valores[0] if valores else None


def definir_param(chave, valor):
    """Define um query param na URL."""
    if hasattr(st, "query_params"):
        st.query_params[chave] = valor
    else:
        # experimental_set_query_params substitui todos os params; preservamos os existentes.
        atuais = st.experimental_get_query_params()
        atuais[chave] = valor
        st.experimental_set_query_params(**atuais)


def limpar_params():
    """Remove todos os query params da URL."""
    if hasattr(st, "query_params"):
        st.query_params.clear()
    else:
        st.experimental_set_query_params()
