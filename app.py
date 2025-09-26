import streamlit as st  # Biblioteca para criar dashboards interativos
import pandas as pd  # Biblioteca para manipulação de dados
import altair as alt  # Biblioteca para visualização de dados

# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Análise das Marcas", layout="wide")
# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Análise das Marcas", layout="wide")

# --- CSS PARA FUNDO ESCURO ---
st.markdown("""
    <style>
        /* Fundo geral */
        .stApp {
            background-color: #0e1117;
            color: white;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1a1d23;
            color: white;
        }

        /* Inputs e selectbox */
        div[data-baseweb="select"] > div {
            background-color: #1a1d23;
            color: white;
        }
        div[data-baseweb="input"] {
            background-color: #1a1d23;
            color: white;
        }
        div[data-baseweb="select"] span {
            color: white !important;
        }

        /* DataFrame */
        .dataframe {
            color: white !important;
            background-color: #1a1d23 !important;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: white;
        }

        /* Labels */
        label, .stSelectbox label {
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# TÍTULO
st.title("📊 Análise das Marcas")

# LISTA DE ABAS DISPONÍVEIS NO ARQUIVO
arquivo = "dados.xlsx"
abas = pd.ExcelFile(arquivo).sheet_names  # Pega todos os nomes das abas

# SELECIONAR MARCA NA SIDEBAR
st.sidebar.header("Selecione a Marca")
marca_selecionada = st.sidebar.selectbox("Marca", abas, index=0)

# CARREGAMENTO E TRATAMENTO DE DADOS
df = pd.read_excel(arquivo, sheet_name=marca_selecionada)

# Renomear colunas para nomes mais legíveis
df.rename(columns={
    df.columns[0]: "Gerente",
    df.columns[2]: "Representante",
    df.columns[3]: "Periodo",
    df.columns[5]: "Peso",
    df.columns[6]: "Faturamento",
    df.columns[7]: "Supervisor"
}, inplace=True)

# Converte a coluna Periodo para datetime
df["Periodo"] = pd.to_datetime(df["Periodo"], errors="coerce")

# Cria coluna para ordenação por mês/ano
df["MesAnoOrd"] = df["Periodo"].dt.to_period("M").dt.to_timestamp()

# Cria coluna com mês/ano formatado como texto
df["MesAno"] = df["Periodo"].dt.strftime("%b/%Y")

# --- SIDEBAR DE FILTROS ---
st.sidebar.header("Filtros")

# Função para criar filtros do tipo selectbox
def filtro_selectbox(coluna, df_input):
    opcoes = ["Todos"] + df_input[coluna].dropna().unique().tolist()
    selecao = st.sidebar.selectbox(coluna, opcoes)
    return df_input if selecao == "Todos" else df_input[df_input[coluna] == selecao]

# Aplica filtros para Gerente, Supervisor e Representante
df_filtrado = filtro_selectbox("Gerente", df)
df_filtrado = filtro_selectbox("Supervisor", df_filtrado)
df_filtrado = filtro_selectbox("Representante", df_filtrado)

# Filtro de meses
meses = df[["MesAnoOrd", "MesAno"]].drop_duplicates().sort_values("MesAnoOrd")
mes_inicio = st.sidebar.selectbox("Mês inicial", meses["MesAno"].tolist(), index=0)
mes_fim = st.sidebar.selectbox("Mês final", meses["MesAno"].tolist(), index=len(meses)-1)

# Converte meses selecionados para timestamps
inicio_ord = meses.loc[meses["MesAno"] == mes_inicio, "MesAnoOrd"].iloc[0]
fim_ord = meses.loc[meses["MesAno"] == mes_fim, "MesAnoOrd"].iloc[0]

# Aplica filtro de intervalo de datas
df_filtrado = df_filtrado[(df_filtrado["MesAnoOrd"] >= inicio_ord) & (df_filtrado["MesAnoOrd"] <= fim_ord)]

# Agrupamento por mês, somando Peso e Faturamento
df_grouped = df_filtrado.groupby(["MesAnoOrd", "MesAno"], as_index=False).agg({
    "Peso": "sum",
    "Faturamento": "sum"
}).sort_values("MesAnoOrd")

# FUNÇÃO PARA CONFIGURAÇÃO DE GRÁFICOS ALT
def configure_black_background(chart):
    return chart.configure_axis(labelColor='white', titleColor='white')\
                .configure_legend(labelColor='white', titleColor='white')\
                .configure_title(color='white')\
                .configure_view(strokeWidth=0, fill='#0e1117')

# FUNÇÃO PARA ADICIONAR RÓTULOS
def adicionar_rotulos(chart, campo, formato="{:,}", cor="white", tamanho=14):
    return chart.mark_text(
        align='center',
        baseline='bottom',
        dy=-10,
        size=tamanho,
        color=cor
    ).encode(
        text=alt.Text(campo, format=formato)
    )

# --- GRÁFICO DE PESO ---
st.subheader("📈 Evolução do Peso")
if not df_grouped.empty:
    base_peso = alt.Chart(df_grouped).encode(
        x=alt.X(
            "MesAno:N",
            title="Mês/Ano",
            sort=df_grouped["MesAnoOrd"].tolist(),
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y(
            "Peso:Q",
            scale=alt.Scale(domain=[df_grouped["Peso"].min() * 0.95, df_grouped["Peso"].max() * 1.05])
        ),
        tooltip=["MesAno", "Peso"]
    )
    linha_peso = base_peso.mark_line(point=True, color='cyan').properties(height=500)
    rotulos_peso = adicionar_rotulos(base_peso, "Peso", formato=",.0f")
    st.altair_chart(configure_black_background(linha_peso + rotulos_peso), use_container_width=True)
else:
    st.warning("Nenhum dado disponível para o período selecionado.")

# --- GRÁFICO DE FATURAMENTO ---
st.subheader("💰 Evolução do Faturamento")
if not df_grouped.empty:
    base_fat = alt.Chart(df_grouped).encode(
        x=alt.X(
            "MesAno:N",
            title="Mês/Ano",
            sort=df_grouped["MesAnoOrd"].tolist(),
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y(
            "Faturamento:Q",
            scale=alt.Scale(domain=[df_grouped["Faturamento"].min() * 0.95,
                                    df_grouped["Faturamento"].max() * 1.05])
        ),
        tooltip=["MesAno", "Faturamento"]
    )
    linha_fat = base_fat.mark_line(point=True, color='lime').properties(height=500)
    rotulos_fat = adicionar_rotulos(base_fat, "Faturamento", formato="$,.0f", cor="white")
    st.altair_chart(configure_black_background(linha_fat + rotulos_fat), use_container_width=True)
else:
    st.warning("Nenhum dado disponível para o período selecionado.")

# --- TABELA RESUMO ---
st.subheader("📋 Resumo dos Dados")
if not df_grouped.empty:
    df_display = df_grouped.copy()
    df_display["Peso"] = df_display["Peso"].map(lambda x: f"{x:,.0f} kg")
    df_display["Faturamento"] = df_display["Faturamento"].map(lambda x: f"R$ {x:,.0f}")
    df_display = df_display[["MesAno", "Peso", "Faturamento"]]
    df_display.columns = ["Mês/Ano", "Peso Total", "Faturamento Total"]
    st.dataframe(df_display, use_container_width=True)
else:
    st.warning("Nenhum dado para exibir na tabela.")
