import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Faturamento",
    page_icon="💰",
    layout="wide"
)

# --- FUNÇÕES AUXILIARES ---
def abreviar_nome(nome_completo):
    palavras = nome_completo.split()
    if len(palavras) > 2:
        return ' '.join(palavras[:2])
    return nome_completo

def abreviar_vendedor(nome_completo):
    if nome_completo == "P L GRILLO REPRESENTACOES LTDA":
        return "Luis"
    if isinstance(nome_completo, str):
        return nome_completo.split()[0]
    return nome_completo

# --- FUNÇÃO PRINCIPAL DE CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    caminho_arquivo = 'Faturamento_Grillo - Detalhes1.csv'
    df = pd.read_csv(
        caminho_arquivo
    )
    df = df.dropna(axis=1, how='all')

    coluna_faturamento = 'Valor'
    coluna_razao_social = 'Razão Social'
    coluna_nome_vendedor = 'Nome'

    df['Faturamento_Limpo'] = df[coluna_faturamento].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
    df['Faturamento_Limpo'] = pd.to_numeric(df['Faturamento_Limpo'], errors='coerce').fillna(0)

    if coluna_razao_social not in df.columns:
        df[coluna_razao_social] = "Não informado"
    if coluna_nome_vendedor not in df.columns:
        df[coluna_nome_vendedor] = "Vendedor não informado"
        
    return df

df = carregar_dados()

# --- TÍTULO E MÉTRICAS ---
st.title("📊 Dashboard de Análise de Faturamento")
st.markdown("---")
col1, col2, col3 = st.columns(3)
coluna_cliente_id = 'Cliente'
coluna_vendedor_id = 'Vendedor'
faturamento_total = df['Faturamento_Limpo'].sum()
total_clientes = df[coluna_cliente_id].nunique()
total_vendedores = df[coluna_vendedor_id].nunique()
col1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
col2.metric("Total de Clientes", f"{total_clientes}")
col3.metric("Total de Vendedores", f"{total_vendedores}")
st.markdown("---")

# --- GRÁFICO DE TOP 10 CLIENTES ---
st.header("🏆 Top 10 Clientes por Faturamento")
coluna_razao_social = 'Razão Social'
faturamento_por_cliente = df.groupby(coluna_cliente_id).agg(
    Faturamento=('Faturamento_Limpo', 'sum'),
    Razao_Social=(coluna_razao_social, 'first')
).sort_values(by='Faturamento', ascending=False).head(10).reset_index()
faturamento_por_cliente['Nome_Abreviado'] = faturamento_por_cliente['Razao_Social'].apply(abreviar_nome)
fig_clientes = px.bar(
    faturamento_por_cliente, x='Faturamento', y='Nome_Abreviado', orientation='h',
    labels={'Faturamento': 'Faturamento (R$)', 'Nome_Abreviado': 'Cliente'}, height=500,
    hover_data={'Cliente': True, 'Razao_Social': True, 'Faturamento': ':.2f', 'Nome_Abreviado': False}
)
fig_clientes.update_traces(hovertemplate='<b>%{customdata[1]}</b><br>ID Cliente: %{customdata[0]}<br>Faturamento: R$ %{x:,.2f}<extra></extra>')
fig_clientes.update_layout(bargap=0.2)
fig_clientes.update_xaxes(title_text="<b>Faturamento (R$)</b>", title_font=dict(size=16), tickprefix="R$ ", showgrid=True, gridwidth=1, gridcolor='#dddddd')
fig_clientes.update_yaxes(title_text="<b>Cliente</b>", title_font=dict(size=16), tickfont=dict(size=12), categoryorder='total ascending')
st.plotly_chart(fig_clientes, use_container_width=True)
st.markdown("---")

# --- SEÇÃO INFERIOR COM DUAS COLUNAS ---
col_esquerda, col_direita = st.columns(2)

with col_esquerda:
    st.header("🏆 Performance dos Vendedores")
    
    coluna_nome_vendedor = 'Nome'
    vendas_por_vendedor = df.groupby(coluna_vendedor_id).agg(
        Faturamento=('Faturamento_Limpo', 'sum'),
        Nome=(coluna_nome_vendedor, 'first')
    ).sort_values(by='Faturamento', ascending=False).reset_index()

    vendas_por_vendedor['Nome_Abreviado'] = vendas_por_vendedor['Nome'].apply(abreviar_vendedor)

    fig_vendedores = px.bar(
        vendas_por_vendedor,
        x='Nome_Abreviado',
        y='Faturamento',
        title='Vendas por Vendedor',
        text_auto='.2s',
        labels={'Faturamento': 'Total de Vendas (R$)', 'Nome_Abreviado': 'Vendedor'},
        # Para garantir a ordem, passamos uma lista em vez de um dicionário
        hover_data=['Vendedor', 'Nome']
    )
    
    # <-- MUDANÇA: Template do hover corrigido e simplificado
    fig_vendedores.update_traces(
        hovertemplate='<b>%{customdata[1]}</b><br>ID: %{customdata[0]}<br>Vendas: R$ %{y:,.2f}<extra></extra>'
    )
    
    fig_vendedores.update_xaxes(
        title_text="<b>Vendedor</b>",
        title_font=dict(size=14)
    )
    fig_vendedores.update_yaxes(
        title_text="<b>Total de Vendas (R$)</b>",
        title_font=dict(size=14),
        tickprefix="R$ "
    )
    
    st.plotly_chart(fig_vendedores, use_container_width=True)

with col_direita:
    st.info("Espaço reservado para um futuro gráfico.")

# --- EXIBINDO OS DADOS BRUTOS ---
with st.expander("Visualizar dados brutos"):
    st.dataframe(df)
