import streamlit as st  # Biblioteca para criar dashboards interativos
import pandas as pd  # Biblioteca para manipulação de dados
import altair as alt  # Biblioteca para visualização de dados

# --- CONFIGURAÇÕES DA PÁGINA ---
st.set_page_config(page_title="Análise das Marcas", layout="wide")  # Define título e layout da página
st.title("📊 Análise das Marcas")  # Adiciona título principal ao dashboard

# --- CARREGAMENTO E TRATAMENTO DE DADOS ---
df = pd.read_excel("dados.xlsx", sheet_name="Bem Brasil")  # Carrega os dados do Excel

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
st.sidebar.header("Filtros")  # Cabeçalho da barra lateral

# Função para criar filtros do tipo selectbox
def filtro_selectbox(coluna, df_input):
    opcoes = ["Todos"] + df_input[coluna].dropna().unique().tolist()  # Adiciona opção "Todos"
    selecao = st.sidebar.selectbox(coluna, opcoes)  # Cria o selectbox no sidebar
    return df_input if selecao == "Todos" else df_input[df_input[coluna] == selecao]  # Filtra o dataframe

# Aplica filtros para Gerente, Supervisor e Representante
df_filtrado = filtro_selectbox("Gerente", df)
df_filtrado = filtro_selectbox("Supervisor", df_filtrado)
df_filtrado = filtro_selectbox("Representante", df_filtrado)

# Filtro de meses
meses = df[["MesAnoOrd", "MesAno"]].drop_duplicates().sort_values("MesAnoOrd")  # Lista de meses únicos
mes_inicio = st.sidebar.selectbox("Mês inicial", meses["MesAno"].tolist(), index=0)  # Seleção de mês inicial
mes_fim = st.sidebar.selectbox("Mês final", meses["MesAno"].tolist(), index=len(meses)-1)  # Seleção de mês final

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

# --- FUNÇÃO PARA CONFIGURAÇÃO DE GRÁFICOS ALT ---
def configure_black_background(chart):
    # Configura cores e estilo do gráfico para fundo preto
    return chart.configure_axis(labelColor='white', titleColor='white')\
                .configure_legend(labelColor='white', titleColor='white')\
                .configure_title(color='white')\
                .configure_view(strokeWidth=0, fill='black')

# --- FUNÇÃO PARA ADICIONAR RÓTULOS ---
def adicionar_rotulos(chart, campo, formato="{:,}", cor="white"):
    # Adiciona rótulos acima dos pontos do gráfico
    return chart.mark_text(
        align='center',
        baseline='bottom',  # evita que o texto saia do gráfico
        dy=-5,  # deslocamento vertical
        color=cor
    ).encode(
        text=alt.Text(campo, format=formato)
    )

# --- GRÁFICO DE PESO ---
st.subheader("📈 Evolução do Peso")  # Subtítulo do gráfico de peso
if not df_grouped.empty:  # Verifica se há dados
    base_peso = alt.Chart(df_grouped).encode(
        x=alt.X("MesAnoOrd:T", title="Mês/Ano", axis=alt.Axis(format="%b/%Y")),  # Eixo X
        y=alt.Y("Peso:Q", scale=alt.Scale(domain=[df_grouped["Peso"].min()*0.95, df_grouped["Peso"].max()*1.05])),  # Eixo Y
        tooltip=["MesAno", "Peso"]  # Tooltip ao passar o mouse
    )
    linha_peso = base_peso.mark_line(point=True, color='cyan').properties(height=500)  # Linha com pontos
    rotulos_peso = adicionar_rotulos(base_peso, "Peso", formato=",")  # Adiciona rótulos
    st.altair_chart(configure_black_background(linha_peso + rotulos_peso), use_container_width=True)  # Exibe gráfico
else:
    st.warning("Nenhum dado disponível para o período selecionado.")  # Aviso caso não haja dados

# --- GRÁFICO DE FATURAMENTO ---
st.subheader("💰 Evolução do Faturamento")  # Subtítulo do gráfico de faturamento
if not df_grouped.empty:
    base_fat = alt.Chart(df_grouped).encode(
        x=alt.X("MesAnoOrd:T", title="Mês/Ano", axis=alt.Axis(format="%b/%Y")),  # Eixo X
        y=alt.Y("Faturamento:Q", scale=alt.Scale(domain=[df_grouped["Faturamento"].min()*0.95, df_grouped["Faturamento"].max()*1.05])),  # Eixo Y
        tooltip=["MesAno", "Faturamento"]  # Tooltip
    )
    linha_fat = base_fat.mark_line(point=True, color='lime').properties(height=500)  # Linha com pontos
    rotulos_fat = adicionar_rotulos(base_fat, "Faturamento", formato="$,.2f", cor="white")  # Rótulos formatados como moeda
    st.altair_chart(configure_black_background(linha_fat + rotulos_fat), use_container_width=True)  # Exibe gráfico
else:
    st.warning("Nenhum dado disponível para o período selecionado.")  # Aviso caso não haja dados

# --- TABELA RESUMO ---
st.subheader("📋 Resumo dos Dados")  # Subtítulo da tabela
if not df_grouped.empty:
    df_display = df_grouped.copy()  # Copia dataframe para exibição
    df_display["Peso"] = df_display["Peso"].map(lambda x: f"{x:,.0f} kg")  # Formata Peso
    df_display["Faturamento"] = df_display["Faturamento"].map(lambda x: f"R$ {x:,.2f}")  # Formata Faturamento
    df_display = df_display[["MesAno", "Peso", "Faturamento"]]  # Seleciona colunas para exibição
    df_display.columns = ["Mês/Ano", "Peso Total", "Faturamento Total"]  # Renomeia colunas
    st.dataframe(df_display, use_container_width=True)  # Exibe tabela interativa
