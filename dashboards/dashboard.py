import streamlit as st
import pandas as pd
import plotly.express as px

from database.db import conectar, criar_tabela
from utils.relatorio import gerar_estatisticas


def render_dashboard(usuario_id=None):

    criar_tabela()

    conn = conectar()

    if usuario_id is not None:
        df = pd.read_sql(
            "SELECT * FROM glicemia WHERE usuario_id = ? ORDER BY id ASC",
            conn,
            params=(usuario_id,)
        )
    else:
        df = pd.read_sql(
            "SELECT * FROM glicemia ORDER BY id ASC",
            conn
        )

    conn.close()

    if len(df) > 0:

        st.subheader("Histórico de Registros")
        # Oculta colunas internas (chaves) na visualização do histórico.
        colunas_internas = [c for c in ["id", "usuario_id"] if c in df.columns]
        st.dataframe(df.drop(columns=colunas_internas))

        st.subheader("Estatísticas Gerais")

        stats = gerar_estatisticas(df)

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Média", f"{stats['media']:.1f}")
        col2.metric("Mediana", f"{stats['mediana']:.1f}")
        col3.metric("Desvio Padrão", f"{stats['desvio']:.1f}")
        col4.metric("Máximo", f"{stats['maximo']:.1f}")
        col5.metric("Mínimo", f"{stats['minimo']:.1f}")

        st.subheader("Histórico de Glicemia")
        st.caption("Use o scroll do mouse ou arraste para dar zoom no gráfico.")

        fig = px.line(
            df,
            x="data_registro",
            y="glicemia",
            markers=True,
            labels={"data_registro": "Data do Registro", "glicemia": "Glicemia (mg/dL)"}
        )

        fig.update_layout(dragmode="zoom")

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Distribuição Glicêmica")
        st.caption("Use o scroll do mouse ou arraste para dar zoom no gráfico.")

        # Define a cor do gráfico com base nas medições mais recentes:
        # - Se as 3 últimas medições estiverem acima de 180 -> vermelho
        # - Senão, se a última medição estiver entre 170 e 180 -> laranja
        # - Caso contrário -> azul (padrão)
        df_ordenado = df.sort_values("id")
        ultimas = df_ordenado["glicemia"].tail(3).tolist()
        ultima_glicemia = df_ordenado["glicemia"].iloc[-1]

        if len(ultimas) == 3 and all(v > 180 for v in ultimas):
            cor_grafico = "#E0444B"  # vermelho
        elif 170 <= ultima_glicemia <= 180:
            cor_grafico = "#F2994A"  # laranja
        else:
            cor_grafico = "#2F6FED"  # azul (padrão)

        fig2 = px.histogram(
            df,
            x="glicemia",
            nbins=10,
            marginal="box",
            labels={"glicemia": "Glicemia (mg/dL)"},
            color_discrete_sequence=[cor_grafico]
        )

        fig2.update_layout(dragmode="zoom")

        st.plotly_chart(fig2, use_container_width=True)

    else:

        st.warning("Nenhum dado cadastrado.")


# Permite executar este arquivo isoladamente também:
# streamlit run dashboards/dashboard.py
if __name__ == "__main__":
    st.title("Dashboard Glicuidado")
    render_dashboard()
