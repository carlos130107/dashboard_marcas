import streamlit as st
import pandas as pd
import altair as alt

# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Análise das Marcas", layout="wide")

# --- CSS PARA DARK MODE COMPLETO ---
st.markdown("""
    <style>
        /* Fundo geral da página */
        .stApp {
            background-color: #0e1117 !important;
            color: white !important;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #1a1d23 !important;
            color: white !important;
        }

        /* Widgets - selectbox, inputs, filtros */
        div[data-baseweb="select"] > div, div[data-baseweb="input"], div.stSelectbox {
            background-color: #1a1d23 !important;
            color: white !important;
        }
        div[data-baseweb="select"] span {
            color: white !important;
        }

        /* Labels */
        label, .stSelectbox label {
            color: white !important;
        }

        /* DataFrame */
        .dataframe {
            color: white !important;
            background-color: #1a1d23 !important;
        }

        /* Cabeçalhos */
        h1, h2, h3, h4, h5, h6 {
            color: white !important;
        }

        /* Tooltips dos gráficos */
        div[role="tooltip"] {
            background-color: #1a1d23 !important;
            color: white !important;
        }

        /* Scrollbars */
        ::-webkit-scrollbar {
            background: #0e1117;
        }
        ::-webkit-scrollbar-thumb {
            background: #555;
        }
    </style>
""", unsafe_allow_html=True)

# Dicionário de usuários e senhas (exemplo)
usuarios = {
    "15843": "15843!claudinei",
    "18182": "18182!enio",
    "19399": "19399!roger",
    "15972": "15972!gilberto",
    "18519": "18519!lobo",
    "15810": "18519!lobo"
}

# Login na sidebar
st.sidebar.header("Login do Gerente")
usuario_input = st.sidebar.text_input("Usuário")
senha_input = st.sidebar.text_input("Senha", type="password")
botao_login = st.sidebar.button("Entrar")

# Variável para controlar autenticação
autenticado = False

if botao_login:
    if usuario_input in usuarios and senha_input == usuarios[usuario_input]:
        autenticado = True
        st.sidebar.success(f"Bem-vindo, {usuario_input}!")
    else:
        st.sidebar.error("Usuário ou senha incorretos.")

if not autenticado:
    st.warning("Por favor, faça login para acessar os dados.")
    st.stop()  # Para não mostrar o restante da aplicação sem login

# TÍTULO
st.title("📊 Análise das Marcas")

# LISTA DE ABAS DISPONÍVEIS NO ARQUIVO
arquivo = "dados.xlsx"
abas = pd.ExcelFile(arquivo).sheet_names

# SELEÇÃO DE MARCA
st.sidebar.header("Selecione a Marca")
marca_selecionada = st.sidebar.selectbox("Marca", abas, index=0)

# CARREGAMENTO DE DADOS
df = pd.read_excel(arquivo, sheet_name=marca_selecionada)

df.rename(columns={
    df.columns[0]: "Gerente",
    df.columns[2]: "Representante",
    df.columns[3]: "Periodo",
    df.columns[5]: "Peso",
    df.columns[6]: "Faturamento",
    df.columns[7]: "Supervisor"
}, inplace=True)

# Filtrar dados para mostrar só o gerente autenticado
df = df[df["Gerente"] == usuario_input]

df["Periodo"] = pd.to_datetime(df["Periodo"], errors="coerce")
df["MesAnoOrd"] = df["Periodo"].dt.to_period("M").dt.to_timestamp()
df["MesAno"] = df["Periodo"].dt.strftime("%b/%Y")

# SIDEBAR DE FILTROS
st.sidebar.header("Filtros")

def filtro_selectbox(coluna, df_input):
    opcoes = ["Todos"] + df_input[coluna].dropna().unique().tolist()
    selecao = st.sidebar.selectbox(coluna, opcoes)
    return df_input if selecao == "Todos" else df_input[df_input[coluna] == selecao]

df_filtrado = filtro_selectbox("Gerente", df)  # Só terá o gerente autenticado
df_filtrado = filtro_selectbox("Supervisor", df_filtrado)
df_filtrado = filtro_selectbox("Representante", df_filtrado)

meses = df[["MesAnoOrd", "MesAno"]].drop_duplicates().sort_values("MesAnoOrd")
mes_inicio = st.sidebar.selectbox("Mês inicial", meses["MesAno"].tolist(), index=0)
mes_fim = st.sidebar.selectbox("Mês final", meses["MesAno"].tolist(), index=len(meses)-1)

inicio_ord = meses.loc[meses["MesAno"] == mes_inicio, "MesAnoOrd"].iloc[0]
fim_ord = meses.loc[meses["MesAno"] == mes_fim, "MesAnoOrd"].iloc[0]

df_filtrado = df_filtrado[(df_filtrado["MesAnoOrd"] >= inicio_ord) & (df_filtrado["MesAnoOrd"] <= fim_ord)]

df_grouped = df_filtrado.groupby(["MesAnoOrd", "MesAno"], as_index=False).agg({
    "Peso": "sum",
    "Faturamento": "sum"
}).sort_values("MesAnoOrd")

# FUNÇÃO PARA CONFIGURAÇÃO DE GRÁFICOS ALT (fundo fixo escuro)
def configure_black_background(chart):
    return chart.configure_axis(
                labelColor='white',
                titleColor='white'
            )\
            .configure_legend(
                labelColor='white',
                titleColor='white'
            )\
            .configure_title(color='white')\
            .configure_view(
                strokeWidth=0,
                fill='#0e1117'  # Fundo escuro fixo
            )

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

# GRÁFICO DE PESO
st.subheader("📈 Evolução do Peso")
if not df_grouped.empty:
    base_peso = alt.Chart(df_grouped).encode(
        x=alt.X(
            "MesAno:N",
            title="Mês/Ano",
            sort=df_grouped["MesAnoOrd"].tolist(),
            axis=alt.Axis(labelAngle=0, labelColor="white", titleColor="white")
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

# GRÁFICO DE FATURAMENTO
st.subheader("💰 Evolução do Faturamento")
if not df_grouped.empty:
    base_fat = alt.Chart(df_grouped).encode(
        x=alt.X(
            "MesAno:N",
            title="Mês/Ano",
            sort=df_grouped["MesAnoOrd"].tolist(),
            axis=alt.Axis(labelAngle=0, labelColor="white", titleColor="white")
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

# TABELA RESUMO
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
