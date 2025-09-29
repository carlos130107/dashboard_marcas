import streamlit as st
import pandas as pd
import altair as alt

# CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Análise das Marcas", layout="wide")

# --- CSS PARA DARK MODE COMPLETO ---
st.markdown("""
    <style>
        .stApp {
            background-color: #0e1117 !important;
            color: white !important;
        }
        section[data-testid="stSidebar"] {
            background-color: #1a1d23 !important;
            color: white !important;
        }
        div[data-baseweb="select"] > div, div[data-baseweb="input"], div.stSelectbox {
            background-color: #1a1d23 !important;
            color: white !important;
        }
        div[data-baseweb="select"] span {
            color: white !important;
        }
        label, .stSelectbox label {
            color: white !important;
        }
        .dataframe {
            color: white !important;
            background-color: #1a1d23 !important;
        }
        h1, h2, h3, h4, h5, h6 {
            color: white !important;
        }
        div[role="tooltip"] {
            background-color: #1a1d23 !important;
            color: white !important;
        }
        ::-webkit-scrollbar {
            background: #0e1117;
        }
        ::-webkit-scrollbar-thumb {
            background: #555;
        }
    </style>
""", unsafe_allow_html=True)

# Dicionário de usuários e senhas (exemplo) - ajuste conforme necessário
usuarios = {
    "15843": "15843!claudinei",
    "18182": "18182!enio",
    "19399": "19399!roger",
    "15972": "15972!gilberto",
    "18519": "18519!lobo",
    "15810": "15810!dennis"
}

# Usar session_state para manter login
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""

# Login na sidebar
st.sidebar.header("Login do Gerente")

if not st.session_state.autenticado:
    usuario_input = st.sidebar.text_input("Usuário")
    senha_input = st.sidebar.text_input("Senha", type="password")
    botao_login = st.sidebar.button("Entrar")

    if botao_login:
        if usuario_input in usuarios and senha_input == usuarios[usuario_input]:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario_input
            st.sidebar.success(f"Bem-vindo, {usuario_input}!")
        else:
            st.sidebar.error("Usuário ou senha incorretos.")
else:
    st.sidebar.success(f"Logado como: {st.session_state.usuario}")
    if st.sidebar.button("Sair"):
        st.session_state.autenticado = False
        st.session_state.usuario = ""
        st.experimental_rerun()

if not st.session_state.autenticado:
    st.warning("Por favor, faça login para acessar os dados.")
    st.stop()

usuario_input = st.session_state.usuario

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

# Função para encontrar colunas por palavras-chave (mais robusto)
def find_col(df, keywords):
    for col in df.columns:
        for k in keywords:
            if k.lower() in col.lower():
                return col
    return None

# Renomear colunas principais para nomes padrão
if 'Gerente' not in df.columns:
    candidate = find_col(df, ['gerente', 'ger/'])
    if candidate:
        df.rename(columns={candidate: 'Gerente'}, inplace=True)

if 'Gerente' not in df.columns:
    st.error("Coluna 'Gerente' não encontrada no arquivo. Verifique o Excel.")
    st.stop()

df['Gerente'] = df['Gerente'].astype(str).str.strip()

mappings = {}
rep_col = find_col(df, ['represent', 'representa', 'represen'])
if rep_col:
    mappings[rep_col] = 'Representante'
periodo_col = find_col(df, ['periodo', 'data', 'mês'])
if periodo_col:
    mappings[periodo_col] = 'Periodo'
peso_col = find_col(df, ['peso'])
if peso_col:
    mappings[peso_col] = 'Peso'
fat_col = find_col(df, ['fatur', 'faturamento', 'receita'])
if fat_col:
    mappings[fat_col] = 'Faturamento'
sup_col = find_col(df, ['supervisor', 'sup'])
if sup_col:
    mappings[sup_col] = 'Supervisor'

if mappings:
    df.rename(columns=mappings, inplace=True)

# Verificar colunas obrigatórias
for c in ['Periodo', 'Peso', 'Faturamento']:
    if c not in df.columns:
        st.error(f"Coluna obrigatória '{c}' não encontrada — colunas detectadas: {', '.join(df.columns)}")
        st.stop()

# Filtrar dados para o gerente autenticado
df = df[df["Gerente"] == usuario_input]

if df.empty:
    st.warning("Nenhum dado encontrado para o gerente autenticado.")
    st.stop()

df["Periodo"] = pd.to_datetime(df["Periodo"], errors="coerce")
df["MesAnoOrd"] = df["Periodo"].dt.to_period("M").dt.to_timestamp()
df["MesAno"] = df["Periodo"].dt.strftime("%b/%Y")

# SIDEBAR DE FILTROS
st.sidebar.header("Filtros")

def filtro_selectbox(coluna, df_input):
    opcoes = ["Todos"] + sorted(df_input[coluna].dropna().unique().tolist())
    selecao = st.sidebar.selectbox(coluna, opcoes)
    return df_input if selecao == "Todos" else df_input[df_input[coluna] == selecao]

df_filtrado = df
if "Gerente" in df.columns:
    df_filtrado = filtro_selectbox("Gerente", df_filtrado)
if "Supervisor" in df.columns:
    df_filtrado = filtro_selectbox("Supervisor", df_filtrado)
if "Representante" in df_filtrado.columns:
    df_filtrado = filtro_selectbox("Representante", df_filtrado)

meses = df_filtrado[["MesAnoOrd", "MesAno"]].drop_duplicates().sort_values("MesAnoOrd")

if meses.empty:
    st.warning("Nenhum dado disponível para os filtros selecionados.")
    st.stop()

mes_inicio = st.sidebar.selectbox("Mês inicial", meses["MesAno"].tolist(), index=0)
mes_fim = st.sidebar.selectbox("Mês final", meses["MesAno"].tolist(), index=len(meses)-1)

inicio_ord = meses.loc[meses["MesAno"] == mes_inicio, "MesAnoOrd"]
fim_ord = meses.loc[meses["MesAno"] == mes_fim, "MesAnoOrd"]

if inicio_ord.empty or fim_ord.empty:
    st.warning("Seleção de mês inválida.")
    st.stop()

inicio_ord = inicio_ord.iloc[0]
fim_ord = fim_ord.iloc[0]

df_filtrado = df_filtrado[(df_filtrado["MesAnoOrd"] >= inicio_ord) & (df_filtrado["MesAnoOrd"] <= fim_ord)]

df_grouped = df_filtrado.groupby(["MesAnoOrd", "MesAno"], as_index=False).agg({
    "Peso": "sum",
    "Faturamento": "sum"
}).sort_values("MesAnoOrd")

# Funções para gráficos Altair com fundo escuro
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
                fill='#0e1117'
            )

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

# Gráfico de Peso
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

# Gráfico de Faturamento
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

# Tabela Resumo
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
