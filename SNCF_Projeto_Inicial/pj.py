
"""
SNCF — Dashboard de Inteligência Ferroviária
Página 1: Visão Geral

Tecnologias:
- Python
- Streamlit
- Pandas
- Plotly
"""

from pathlib import Path
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(
    page_title="SNCF | Visão Geral",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Cores das sete famílias tecnológicas
CORES = {
    "A": "#EAB308",  # Bloco automático
    "B": "#DC2626",  # Cantonamento telefônico
    "C": "#F97316",  # Bloco manual
    "D": "#16A34A",  # Sinalização de cabine
    "E": "#64748B",  # Sem cantonamento
    "F": "#9333EA",  # Bonde / tram
    "G": "#2563EB"   # Outro / não especificado
}

ORDEM = list(CORES.keys())


# =====================================================
# 2. ESTILO VISUAL
# =====================================================

st.markdown("""
<style>

/* Fundo principal */
.stApp {
    background: #0B1220;
    color: #E7EDF7;
}

/* Área central */
.block-container {
    padding-top: 2rem;
    max-width: 1350px;
}

/* Indicadores */
[data-testid="stMetric"] {
    background: #172235;
    border: 1px solid #2B3A50;
    border-radius: 14px;
    padding: 16px 18px;
    min-width: 0;
}

[data-testid="stMetricLabel"] {
    color: #A9B8CD;
}

[data-testid="stMetricValue"] {
    font-size: clamp(1.15rem, 2vw, 2rem);
    white-space: normal;
    overflow-wrap: break-word;
}

/* Cartões das famílias */
.familia {
    background: #172235;
    border: 1px solid #2B3A50;
    border-left: 5px solid var(--cor);
    border-radius: 12px;
    padding: 13px 16px;
    margin-bottom: 10px;
    min-height: 110px;
}

.familia small {
    color: #A9B8CD;
}

.familia strong {
    font-size: 1.05rem;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. FUNÇÕES DE FORMATAÇÃO
# =====================================================

def numero(valor, casas=0):
    """
    Formata números no padrão brasileiro.

    Exemplo:
    1631 -> 1.631
    3175.5 -> 3.175,5
    """

    return (
        f"{valor:,.{casas}f}"
        .replace(",", "TEMP")
        .replace(".", ",")
        .replace("TEMP", ".")
    )


def formatar_extensao(valor):
    """
    Formata quilômetros para facilitar a leitura.

    Exemplos:
    30599.9 -> 30,6 mil km
    17913.4 -> 17,9 mil km
    3175.5 -> 3.175,5 km
    """

    if pd.isna(valor):
        return "Não informado"

    if abs(valor) >= 10000:
        return f"{numero(valor / 1000, 1)} mil km"

    return f"{numero(valor, 1)} km"


# =====================================================
# 4. CARREGAMENTO DOS DADOS
# =====================================================

@st.cache_data
def carregar_dados():

    caminho = (
        Path(__file__).resolve().parent
        / "dados"
        / "sncf_dados_agrupados.csv"
    )

    if not caminho.exists():
        st.error(f"Arquivo não encontrado: {caminho}")
        st.stop()

    # Leitura do CSV com ponto e vírgula
    dados = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig",
        low_memory=False,
        dtype={"codigo_linha": "string"}
    )

    # Conversão das colunas numéricas
    dados["extensao_km"] = pd.to_numeric(
        dados["extensao_km"],
        errors="coerce"
    )

    dados["nivel_automacao"] = pd.to_numeric(
        dados["nivel_automacao"],
        errors="coerce"
    )

    dados["grupo"] = (
        dados["grupo"]
        .astype("string")
        .str.strip()
    )

    return dados


df = carregar_dados()


# =====================================================
# 5. CABEÇALHO
# =====================================================

st.title("🚆 SNCF | Inteligência Ferroviária")

st.caption(
    "Visão Geral • Tecnologias de cantonamento "
    "da rede ferroviária francesa"
)

st.markdown(
    "Explore a distribuição das tecnologias de controle "
    "de circulação ferroviária, por quantidade de trechos "
    "e extensão registrada."
)


# =====================================================
# 6. BASE COMPLETA — SEM FILTROS
# =====================================================

# Todos os registros são utilizados.
# Não há seleção de famílias na barra lateral.
filtrado = df.copy()


# =====================================================
# 7. RESUMO DAS FAMÍLIAS
# =====================================================

resumo = (
    filtrado.groupby(
        ["grupo", "familia_tecnologica"],
        as_index=False
    )
    .agg(
        trechos=("grupo", "size"),
        km=("extensao_km", "sum")
    )
)

# Ordenação de A até G
resumo["grupo"] = pd.Categorical(
    resumo["grupo"],
    categories=ORDEM,
    ordered=True
)

resumo = resumo.sort_values("grupo").copy()

# Participação de cada família em relação ao total
resumo["percentual"] = (
    resumo["trechos"] / len(filtrado) * 100
)

resumo["nome"] = (
    resumo["grupo"].astype(str)
    + " · "
    + resumo["familia_tecnologica"]
)

# Associação entre família e cor
cores_nomes = {
    r["nome"]: CORES[str(r["grupo"])]
    for _, r in resumo.iterrows()
}


# =====================================================
# 8. INDICADORES GERAIS
# =====================================================

st.subheader("Panorama da base")

a, b, c, d, e = st.columns(5)

a.metric(
    "Trechos",
    numero(len(filtrado))
)

b.metric(
    "Linhas distintas",
    numero(filtrado["codigo_linha"].nunique())
)

c.metric(
    "Extensão somada",
    formatar_extensao(
        filtrado["extensao_km"].sum()
    )
)

d.metric(
    "Modos identificados",
    numero(
        filtrado["modo_cantonamento"].nunique()
    )
)

e.metric(
    "Famílias tecnológicas",
    numero(filtrado["grupo"].nunique())
)

st.caption(
    "A extensão é a soma dos trechos registrados, "
    "não necessariamente a extensão física única da rede."
)

st.divider()


# =====================================================
# 9. AS SETE FAMÍLIAS TECNOLÓGICAS
# =====================================================

st.subheader("As sete famílias tecnológicas")

st.write(
    "Distribuição percentual dos trechos ferroviários "
    "entre as sete famílias de cantonamento."
)

# Gráfico à esquerda, cartões à direita
esq, direita = st.columns(
    [1.1, 1],
    gap="large"
)


# =====================================================
# 10. GRÁFICO DE ROSCA COM PORCENTAGENS
# =====================================================

with esq:

    # Cópia do resumo para os dados do gráfico
    dados_grafico = resumo.copy()

    # Percentuais já formatados em português.
    # Fatias muito pequenas não recebem texto,
    # evitando sobreposição de valores.
    dados_grafico["rotulo_percentual"] = (
        dados_grafico["percentual"].apply(
            lambda p: f"{numero(p, 1)}%" if p >= 4 else ""
        )
    )

    fig = px.pie(
        dados_grafico,
        names="nome",
        values="trechos",
        hole=0.65,
        color="nome",
        color_discrete_map=cores_nomes,
        custom_data=["rotulo_percentual"]
    )

    fig.update_traces(

        # Exibe apenas os percentuais formatados
        text=dados_grafico["rotulo_percentual"].tolist(),
        textinfo="text",

        # Percentuais dentro das fatias
        textposition="inside",

        textfont=dict(
            size=14,
            color="white"
        ),

        # Desativa as informações ao passar o mouse
        hoverinfo="skip",
        hovertemplate=None,

        # Separação visual das fatias
        marker=dict(
            line=dict(
                color="#0B1220",
                width=2
            )
        )
    )

    # Número central
    fig.add_annotation(
        text=(
            f"<b>{numero(len(filtrado))}</b>"
            "<br><span style='font-size:15px'>trechos</span>"
        ),
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(
            size=27,
            color="white"
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(
            l=15,
            r=15,
            t=15,
            b=15
        ),
        height=440,
        uniformtext=dict(
            minsize=12,
            mode="hide"
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )

    st.caption(
        "Percentuais calculados pela quantidade de trechos. "
        "A família F possui participação inferior a 4% "
        "e aparece detalhada no cartão correspondente."
    )


# =====================================================
# 11. CARTÕES DAS SETE FAMÍLIAS
# =====================================================

with direita:

    for _, r in resumo.iterrows():

        grupo = str(r["grupo"])

        nome_familia = escape(
            str(r["familia_tecnologica"])
        )

        quantidade = numero(r["trechos"])
        extensao = formatar_extensao(r["km"])
        percentual = numero(r["percentual"], 1)

        # HTML em uma única estrutura para evitar
        # exibição das tags como texto.
        cartao = (
            f'<div class="familia" style="--cor:{CORES[grupo]}">'
            f'<strong>{grupo} — {nome_familia}</strong><br>'
            f'<small>{quantidade} trechos · '
            f'{extensao} · '
            f'{percentual}% dos trechos</small>'
            f'</div>'
        )

        st.markdown(
            cartao,
            unsafe_allow_html=True
        )


# =====================================================
# 12. COMPARAÇÃO ENTRE FAMÍLIAS
# =====================================================

st.divider()

st.subheader("Comparação entre famílias")

st.write(
    "Compare as famílias tecnológicas pela extensão "
    "registrada ou pela quantidade de trechos."
)

metrica = st.radio(
    "Comparar por",
    [
        "Extensão (km)",
        "Quantidade de trechos"
    ],
    horizontal=True
)

coluna = (
    "km"
    if metrica == "Extensão (km)"
    else "trechos"
)

ordenado = resumo.sort_values(
    coluna,
    ascending=True
).copy()

# Formatação dos rótulos das barras
if coluna == "km":

    ordenado["rotulo_valor"] = (
        ordenado["km"].apply(formatar_extensao)
    )

else:

    ordenado["rotulo_valor"] = (
        ordenado["trechos"].apply(numero)
    )

fig_barras = px.bar(
    ordenado,
    x=coluna,
    y="nome",
    orientation="h",
    color="nome",
    color_discrete_map=cores_nomes,
    text="rotulo_valor",
    labels={
        "nome": "Família",
        coluna: metrica
    }
)

fig_barras.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "<b>%{y}</b>"
        "<br>Valor: %{text}"
        "<extra></extra>"
    )
)

fig_barras.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False,
    margin=dict(
        l=15,
        r=110,
        t=20,
        b=15
    ),
    height=440
)

st.plotly_chart(
    fig_barras,
    use_container_width=True
)


# =====================================================
# 13. TABELA DE APOIO
# =====================================================

st.subheader("Tabela de apoio")

tabela = resumo[
    [
        "grupo",
        "familia_tecnologica",
        "trechos",
        "km",
        "percentual"
    ]
].copy()

tabela.columns = [
    "Grupo",
    "Família",
    "Trechos",
    "Extensão (km)",
    "% dos trechos"
]

st.dataframe(
    tabela,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Extensão (km)": st.column_config.NumberColumn(
            format="%.1f"
        ),
        "% dos trechos": st.column_config.NumberColumn(
            format="%.1f%%"
        )
    }
)

st.caption(
    "Fonte: base SNCF fornecida para o projeto. "
    "Análise descritiva dos modos de cantonamento "
    "da rede ferroviária francesa."
)
