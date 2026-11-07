
from pathlib import Path
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(
    page_title="SNCF | Análise Ferroviária",
    page_icon="📊",
    layout="wide"
)

CORES = {
    "A": "#EAB308",
    "B": "#DC2626",
    "C": "#F97316",
    "D": "#16A34A",
    "E": "#64748B",
    "F": "#9333EA",
    "G": "#2563EB"
}

ORDEM = list(CORES.keys())


# =====================================================
# 2. ESTILO VISUAL
# =====================================================

st.markdown("""
<style>

.stApp {
    background: #0B1220;
    color: #E7EDF7;
}

.block-container {
    padding-top: 2rem;
    max-width: 1350px;
}

[data-testid="stMetric"] {
    background: #172235;
    border: 1px solid #2B3A50;
    border-radius: 14px;
    padding: 16px 18px;
}

[data-testid="stMetricLabel"] {
    color: #A9B8CD;
}

[data-testid="stMetricValue"] {
    font-size: clamp(1.15rem, 2vw, 2rem);
    white-space: normal;
    overflow-wrap: break-word;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. FUNÇÕES AUXILIARES
# =====================================================

def numero(valor, casas=0):
    """Formata números no padrão brasileiro."""
    return (
        f"{valor:,.{casas}f}"
        .replace(",", "TEMP")
        .replace(".", ",")
        .replace("TEMP", ".")
    )


def formatar_km(valor):
    """Formata extensões ferroviárias."""

    if pd.isna(valor):
        return "Não informado"

    if abs(valor) >= 10000:
        return f"{numero(valor / 1000, 1)} mil km"

    return f"{numero(valor, 1)} km"


def estilo_grafico(fig, altura=430):
    """Aplica o tema escuro aos gráficos."""

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E7EDF7"),
        margin=dict(l=15, r=30, t=25, b=20),
        height=altura
    )

    return fig


# =====================================================
# 4. CARREGAMENTO DOS DADOS
# =====================================================

@st.cache_data
def carregar_dados():

    # A página está dentro da pasta pages.
    # parent.parent retorna à raiz do projeto.
    raiz = Path(__file__).resolve().parent.parent

    caminho = raiz / "dados" / "sncf_dados_agrupados.csv"

    if not caminho.exists():
        st.error(f"Arquivo não encontrado: {caminho}")
        st.stop()

    dados = pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8-sig",
        low_memory=False,
        dtype={"codigo_linha": "string"}
    )

    dados["extensao_km"] = pd.to_numeric(
        dados["extensao_km"],
        errors="coerce"
    )

    dados["grupo"] = (
        dados["grupo"]
        .astype("string")
        .str.strip()
    )

    dados["codigo_linha"] = (
        dados["codigo_linha"]
        .astype("string")
        .str.strip()
    )

    return dados


df = carregar_dados()


# =====================================================
# 5. PREPARAÇÃO DA BASE
# =====================================================

# Selecionamos os registros com códigos válidos
# e grupos tecnológicos reconhecidos.
dados_linhas = df[
    df["codigo_linha"].notna()
    & (df["codigo_linha"] != "")
    & df["grupo"].isin(ORDEM)
].copy()

# Extensões negativas ou ausentes não entram
# nas somas, mas os trechos continuam contados.
dados_linhas["extensao_valida"] = (
    dados_linhas["extensao_km"].where(
        dados_linhas["extensao_km"] >= 0
    )
)

if dados_linhas.empty:
    st.warning("Não existem linhas válidas para analisar.")
    st.stop()


# =====================================================
# 6. CABEÇALHO
# =====================================================

st.title("📊 SNCF | Análise Ferroviária")

st.caption(
    "Página 2 • Ranking, diversidade tecnológica "
    "e exploração das linhas ferroviárias"
)

st.write(
    "Explore as características das linhas ferroviárias "
    "da SNCF, compare sua diversidade tecnológica e "
    "investigue os sistemas de cantonamento presentes "
    "em cada linha."
)

st.divider()


# =====================================================
# 7. RANKING DE LINHAS FERROVIÁRIAS
# =====================================================

st.subheader("Ranking de linhas ferroviárias")

st.write(
    "Identifique as linhas com maior extensão somada, "
    "maior quantidade de trechos ou maior diversidade "
    "de famílias tecnológicas."
)

ranking = (
    dados_linhas.groupby(
        "codigo_linha",
        as_index=False
    )
    .agg(
        trechos=("grupo", "size"),
        extensao=("extensao_valida", "sum"),
        familias=("grupo", "nunique")
    )
)

opcoes_ranking = {
    "Maior extensão somada": "extensao",
    "Maior quantidade de trechos": "trechos",
    "Maior diversidade tecnológica": "familias"
}

col_tipo, col_top = st.columns([2, 1])

with col_tipo:

    criterio = st.selectbox(
        "Critério de classificação",
        options=list(opcoes_ranking.keys())
    )

with col_top:

    top_n = st.selectbox(
        "Quantidade de linhas",
        options=[5, 10, 15, 20],
        index=1
    )

coluna_ranking = opcoes_ranking[criterio]

top_linhas = (
    ranking.sort_values(
        [coluna_ranking, "codigo_linha"],
        ascending=[False, True]
    )
    .head(top_n)
    .sort_values(
        coluna_ranking,
        ascending=True
    )
    .copy()
)

top_linhas["rotulo"] = top_linhas[
    coluna_ranking
].apply(
    lambda valor: (
        formatar_km(valor)
        if coluna_ranking == "extensao"
        else numero(valor)
    )
)

fig_rank = px.bar(
    top_linhas,
    x=coluna_ranking,
    y="codigo_linha",
    orientation="h",
    text="rotulo",
    labels={
        "codigo_linha": "Código da linha",
        "extensao": "Extensão somada (km)",
        "trechos": "Quantidade de trechos",
        "familias": "Famílias tecnológicas"
    },
    color_discrete_sequence=["#38BDF8"]
)

fig_rank.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "Linha: %{y}<br>"
        "Valor: %{text}"
        "<extra></extra>"
    )
)

fig_rank.update_layout(
    showlegend=False,
    margin=dict(l=15, r=110, t=25, b=20)
)

estilo_grafico(fig_rank, 480)

st.plotly_chart(
    fig_rank,
    use_container_width=True,
    config={"displayModeBar": False}
)

st.caption(
    "A extensão corresponde à soma dos comprimentos "
    "registrados para cada código de linha, não "
    "necessariamente ao comprimento físico único."
)


# =====================================================
# 8. DIVERSIDADE TECNOLÓGICA DAS LINHAS
# =====================================================

st.divider()

st.subheader("Diversidade tecnológica das linhas")

st.write(
    "Uma mesma linha pode apresentar diferentes "
    "famílias de cantonamento ao longo de seus trechos. "
    "Esta análise mostra quantas famílias tecnológicas "
    "estão presentes em cada linha."
)

# Quantidade de famílias diferentes por código de linha
diversidade_linhas = (
    dados_linhas.groupby("codigo_linha")["grupo"]
    .nunique()
    .reset_index(name="quantidade_familias")
)

# Distribuição da quantidade de famílias
distribuicao_diversidade = (
    diversidade_linhas["quantidade_familias"]
    .value_counts()
    .sort_index()
    .reset_index()
)

distribuicao_diversidade.columns = [
    "quantidade_familias",
    "quantidade_linhas"
]

# Indicadores
total_linhas = len(diversidade_linhas)

linhas_unicas = int(
    (diversidade_linhas["quantidade_familias"] == 1).sum()
)

linhas_multiplas = int(
    (diversidade_linhas["quantidade_familias"] >= 2).sum()
)

percentual_multiplas = (
    linhas_multiplas / total_linhas * 100
    if total_linhas > 0
    else 0
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Linhas com uma família",
    numero(linhas_unicas)
)

c2.metric(
    "Linhas com múltiplas famílias",
    numero(linhas_multiplas)
)

c3.metric(
    "Linhas com múltiplas famílias (%)",
    f"{numero(percentual_multiplas, 1)}%"
)

# Gráfico de diversidade
fig_diversidade = px.bar(
    distribuicao_diversidade,
    x="quantidade_familias",
    y="quantidade_linhas",
    text="quantidade_linhas",
    labels={
        "quantidade_familias": "Famílias tecnológicas por linha",
        "quantidade_linhas": "Quantidade de linhas"
    },
    color_discrete_sequence=["#38BDF8"]
)

fig_diversidade.update_traces(
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "Famílias por linha: %{x}<br>"
        "Quantidade de linhas: %{y}"
        "<extra></extra>"
    )
)

fig_diversidade.update_xaxes(
    type="category"
)

fig_diversidade.update_layout(
    showlegend=False,
    yaxis_title="Quantidade de linhas"
)

estilo_grafico(fig_diversidade, 400)

st.plotly_chart(
    fig_diversidade,
    use_container_width=True,
    config={"displayModeBar": False}
)

st.caption(
    "Cada código de linha é contado uma vez. "
    "Por exemplo, uma linha que apresenta três "
    "famílias diferentes pertence à categoria 3."
)


# =====================================================
# 9. FAMÍLIAS TECNOLÓGICAS QUE APARECEM JUNTAS
# =====================================================

st.markdown("#### Quais tecnologias aparecem juntas?")

st.write(
    "O gráfico mostra os pares de famílias tecnológicas "
    "identificados em uma mesma linha ferroviária."
)

# Reúne as famílias presentes em cada linha
familias_por_linha = (
    dados_linhas.groupby("codigo_linha")["grupo"]
    .apply(
        lambda valores: sorted(
            set(valores.dropna().tolist())
        )
    )
)

# Conta as combinações de duas famílias
contagem_pares = {}

for familias in familias_por_linha:

    if len(familias) < 2:
        continue

    for par in combinations(familias, 2):

        contagem_pares[par] = (
            contagem_pares.get(par, 0) + 1
        )

# Organiza os resultados em uma tabela
pares_df = pd.DataFrame(
    [
        {
            "familia_1": par[0],
            "familia_2": par[1],
            "quantidade_linhas": quantidade
        }
        for par, quantidade in contagem_pares.items()
    ]
)

if pares_df.empty:

    st.info(
        "Não foram identificadas linhas com duas "
        "ou mais famílias tecnológicas diferentes."
    )

else:

    pares_df = pares_df.sort_values(
        "quantidade_linhas",
        ascending=False
    )

    pares_df["par"] = (
        pares_df["familia_1"]
        + " + "
        + pares_df["familia_2"]
    )

    top_pares = (
        pares_df.head(10)
        .sort_values(
            "quantidade_linhas",
            ascending=True
        )
        .copy()
    )

    fig_pares = px.bar(
        top_pares,
        x="quantidade_linhas",
        y="par",
        orientation="h",
        text="quantidade_linhas",
        labels={
            "quantidade_linhas": "Quantidade de linhas",
            "par": "Famílias tecnológicas"
        },
        color_discrete_sequence=["#A78BFA"]
    )

    fig_pares.update_traces(
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "Famílias: %{y}<br>"
            "Linhas em comum: %{x}"
            "<extra></extra>"
        )
    )

    fig_pares.update_layout(
        showlegend=False,
        margin=dict(l=15, r=80, t=25, b=20)
    )

    estilo_grafico(fig_pares, 430)

    st.plotly_chart(
        fig_pares,
        use_container_width=True,
        config={"displayModeBar": False}
    )

    st.caption(
        "Um par como A + D indica que uma mesma linha "
        "possui trechos registrados nas famílias A e D. "
        "Isso não significa que ambas operem "
        "simultaneamente no mesmo trecho."
    )


# =====================================================
# 10. EXPLORAR UMA LINHA FERROVIÁRIA
# =====================================================

st.divider()

st.subheader("Explorar uma linha ferroviária")

st.write(
    "Agora que você conhece as características gerais "
    "das linhas, selecione uma delas para investigar "
    "seus trechos e as tecnologias utilizadas."
)

# Lista de códigos disponíveis
linhas_disponiveis = sorted(
    dados_linhas["codigo_linha"].unique().tolist()
)

linha_escolhida = st.selectbox(
    "Código da linha",
    options=linhas_disponiveis
)

# Filtra os registros da linha selecionada
detalhe = dados_linhas[
    dados_linhas["codigo_linha"] == linha_escolhida
].copy()


# =====================================================
# 11. INDICADORES DA LINHA SELECIONADA
# =====================================================

m1, m2, m3 = st.columns(3)

m1.metric(
    "Trechos registrados",
    numero(len(detalhe))
)

m2.metric(
    "Extensão somada",
    formatar_km(
        detalhe["extensao_valida"].sum()
    )
)

m3.metric(
    "Famílias presentes",
    numero(
        detalhe["grupo"].nunique()
    )
)


# =====================================================
# 12. COMPOSIÇÃO TECNOLÓGICA DA LINHA
# =====================================================

st.markdown("#### Composição tecnológica")

st.write(
    "O gráfico apresenta a quantidade de trechos "
    "associados a cada família tecnológica "
    "da linha selecionada."
)

# Agrupamento dos registros por família
composicao = (
    detalhe.groupby(
        ["grupo", "familia_tecnologica"],
        as_index=False
    )
    .agg(
        trechos=("grupo", "size"),
        km=("extensao_valida", "sum")
    )
)

# Rótulos das famílias
composicao["familia_label"] = (
    composicao["grupo"].astype(str)
    + " · "
    + composicao["familia_tecnologica"].astype(str)
)

# Cores correspondentes a cada família
cores_label = {
    r["familia_label"]: CORES[str(r["grupo"])]
    for _, r in composicao.iterrows()
}

fig_linha = px.bar(
    composicao,
    x="familia_label",
    y="trechos",
    color="familia_label",
    color_discrete_map=cores_label,
    text="trechos",
    labels={
        "familia_label": "Família tecnológica",
        "trechos": "Quantidade de trechos"
    }
)

fig_linha.update_layout(
    showlegend=False,
    xaxis_tickangle=-20
)

fig_linha.update_traces(
    textposition="outside",
    cliponaxis=False
)

estilo_grafico(fig_linha, 380)

st.plotly_chart(
    fig_linha,
    use_container_width=True,
    config={"displayModeBar": False}
)


# =====================================================
# 13. TABELA DETALHADA DA LINHA
# =====================================================

st.markdown("#### Registros da linha selecionada")

st.write(
    "Consulte os registros associados à linha "
    "escolhida, incluindo a família tecnológica, "
    "o modo de cantonamento e a extensão."
)

colunas_detalhe = [
    "codigo_linha",
    "grupo",
    "familia_tecnologica",
    "modo_cantonamento",
    "extensao_km"
]

tabela_detalhe = detalhe[
    colunas_detalhe
].copy()

tabela_detalhe.columns = [
    "Código da linha",
    "Grupo",
    "Família tecnológica",
    "Modo de cantonamento",
    "Extensão (km)"
]

st.dataframe(
    tabela_detalhe,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Extensão (km)": st.column_config.NumberColumn(
            format="%.2f"
        )
    }
)


# =====================================================
# 14. RODAPÉ
# =====================================================

st.divider()

st.caption(
    "Fonte: dados SNCF fornecidos para o projeto. "
    "Análise descritiva das linhas e das famílias "
    "tecnológicas de cantonamento ferroviário."
)
