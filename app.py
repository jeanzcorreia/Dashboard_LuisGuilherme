import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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
        return "LUIS"
    if isinstance(nome_completo, str):
        if nome_completo.upper() == "ALVARO":
            return "Alvaro"
        return nome_completo.split()[0]
    return nome_completo

# <-- NOVO: Função para abreviar nomes de produtos -->
def abreviar_produto(nome_produto, max_len=45):
    """Abrevia o nome do produto se for muito longo para caber no gráfico."""
    if isinstance(nome_produto, str) and len(nome_produto) > max_len:
        return nome_produto[:max_len - 3] + "..."
    return nome_produto

def limpar_valor(valor):
    if pd.isna(valor):
        return 0
    s_valor = str(valor).strip()
    if ',' in s_valor:
        s_valor = s_valor.replace('R$', '').strip().replace('.', '').replace(',', '.')
    return pd.to_numeric(s_valor, errors='coerce')

# --- FUNÇÃO PRINCIPAL DE CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    caminho_arquivo = 'Faturamento_Grillo.xlsx'
    try:
        df = pd.read_excel(caminho_arquivo, skiprows=2, engine='openpyxl')
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}")
        return pd.DataFrame()

    df = df.dropna(axis=1, how='all')
    coluna_faturamento = 'Valor'
    coluna_razao_social = 'Razão Social'
    coluna_nome_vendedor = 'Nome'
    coluna_data_emissao = 'Emissão'

    if coluna_faturamento in df.columns:
        df['Faturamento_Limpo'] = df[coluna_faturamento].apply(limpar_valor).fillna(0)
    else:
        st.error(f"A coluna de faturamento '{coluna_faturamento}' não foi encontrada.")
        return pd.DataFrame()

    if coluna_data_emissao in df.columns:
        df[coluna_data_emissao] = pd.to_datetime(df[coluna_data_emissao], errors='coerce')
        df.dropna(subset=[coluna_data_emissao], inplace=True)
    else:
        st.error(f"A coluna de data '{coluna_data_emissao}' não foi encontrada.")
        df[coluna_data_emissao] = pd.NaT

    if coluna_razao_social not in df.columns:
        df[coluna_razao_social] = "Não informado"
    if coluna_nome_vendedor not in df.columns:
        df[coluna_nome_vendedor] = "Vendedor não informado"
        
    return df

df = carregar_dados()

if df.empty:
    st.warning("Não foi possível carregar os dados. O dashboard não pode ser exibido.")
    st.stop()

# --- DEFINIÇÃO GLOBAL DOS NOMES DAS COLUNAS ---
coluna_cliente_id = 'Cliente'
coluna_vendedor_id = 'Vendedor'
coluna_razao_social = 'Razão Social'
coluna_nome_vendedor = 'Nome'
coluna_data_emissao = 'Emissão'
# <-- NOVO: Definição da coluna de produto -->
coluna_produto = 'Descrição' 

# --- TÍTULO E MÉTRICAS ---
st.title("📊 Dashboard de Análise de Faturamento da Safra 24/25")
st.markdown("---")
col1, col2, col3 = st.columns(3)
faturamento_total = df['Faturamento_Limpo'].sum()
total_clientes = df[coluna_cliente_id].nunique()
total_vendedores = df[coluna_vendedor_id].nunique()
col1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
col2.metric("Total de Clientes", f"{total_clientes}")
col3.metric("Total de Vendedores", f"{total_vendedores}")
st.markdown("---")

# --- GRÁFICO DE TOP 10 CLIENTES ---
st.header("🏆 Top 10 Clientes por Faturamento")
faturamento_por_cliente = df.groupby(coluna_razao_social).agg(
    Faturamento=('Faturamento_Limpo', 'sum'),
    IDs_Cliente=(coluna_cliente_id, lambda ids: ', '.join(ids.astype(str).unique())),
    Nome_Vendedor=(coluna_nome_vendedor, 'first')
).sort_values(by='Faturamento', ascending=False).head(10).reset_index()
faturamento_por_cliente['Nome_Abreviado'] = faturamento_por_cliente[coluna_razao_social].apply(abreviar_nome)
faturamento_por_cliente['Vendedor_Abreviado'] = faturamento_por_cliente['Nome_Vendedor'].apply(abreviar_vendedor)
fig_clientes = px.bar(faturamento_por_cliente, x='Faturamento', y='Nome_Abreviado', orientation='h', labels={'Faturamento': 'Faturamento (R$)', 'Nome_Abreviado': 'Cliente'}, height=500, hover_data=['IDs_Cliente', 'Razão Social'], color='Faturamento', color_continuous_scale='Greens')
f_max = faturamento_por_cliente['Faturamento'].max() if not faturamento_por_cliente.empty else 0
fig_clientes.update_traces(hovertemplate='<b>%{customdata[1]}</b><br>IDs Cliente: %{customdata[0]}<br>Faturamento: R$ %{x:,.2f}<extra></extra>')
fig_clientes.update_layout(bargap=0.2, coloraxis_showscale=False, coloraxis=dict(cmin=0, cmax=f_max * 1.5))
for index, row in faturamento_por_cliente.iterrows():
    fig_clientes.add_annotation(y=row['Nome_Abreviado'], x=f_max * 0.02, text=row['Vendedor_Abreviado'], showarrow=False, xanchor='left', font=dict(color="rgba(0, 0, 0, 0.7)", size=12))
fig_clientes.update_xaxes(title_text="<b>Faturamento (R$)</b>", title_font=dict(size=16), tickprefix="R$ ", showgrid=True, gridwidth=1, gridcolor='#dddddd')
fig_clientes.update_yaxes(title_text="<b>Cliente</b>", title_font=dict(size=16), tickfont=dict(size=12), categoryorder='total ascending')
st.plotly_chart(fig_clientes, use_container_width=True)
st.markdown("---")


# <-- NOVO: GRÁFICO DE TOP 5 PRODUTOS MAIS VENDIDOS -->
st.header("📦 Top 10 Produtos Mais Vendidos")
if coluna_produto in df.columns:
    vendas_por_produto = df.groupby(coluna_produto).agg(
        Faturamento=('Faturamento_Limpo', 'sum')
    ).sort_values(by='Faturamento', ascending=False).head(10).reset_index()

    vendas_por_produto['Produto_Abreviado'] = vendas_por_produto[coluna_produto].apply(abreviar_produto)

    fig_produtos = px.bar(
        vendas_por_produto,
        x='Faturamento',
        y='Produto_Abreviado',
        orientation='h',
        title='Top 10 Produtos por Faturamento',
        labels={'Faturamento': 'Faturamento (R$)', 'Produto_Abreviado': 'Produto'},
        color='Faturamento',
        color_continuous_scale='Greens',
        hover_data=[coluna_produto] 
    )

    fig_produtos.update_layout(coloraxis_showscale=False)
    fig_produtos.update_xaxes(title_text="<b>Faturamento (R$)</b>", title_font=dict(size=16), tickprefix="R$ ")
    fig_produtos.update_yaxes(title_text="<b>Produto</b>", title_font=dict(size=16), categoryorder='total ascending')
    fig_produtos.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Faturamento: R$ %{x:,.2f}<extra></extra>')
    
    st.plotly_chart(fig_produtos, use_container_width=True)
else:
    st.warning(f"A coluna '{coluna_produto}' não foi encontrada. O gráfico de produtos não pode ser gerado.")
st.markdown("---")
# <-- FIM DO NOVO GRÁFICO -->


# --- GRÁFICO DE FATURAMENTO MENSAL ---
st.header("📈 Faturamento Mensal ao Longo da Safra")
df_temp = df.copy()
df_temp['Mes_Emissao'] = df_temp[coluna_data_emissao].dt.to_period('M').dt.to_timestamp()
vendas_por_mes = df_temp.groupby('Mes_Emissao').agg(Faturamento=('Faturamento_Limpo', 'sum')).reset_index()
vendas_por_mes = vendas_por_mes.sort_values(by='Mes_Emissao')
fig_faturamento_mes = px.line(vendas_por_mes, x='Mes_Emissao', y='Faturamento', title='Evolução do Faturamento Mensal', labels={'Mes_Emissao': 'Mês da Emissão', 'Faturamento': 'Faturamento Mensal (R$)'}, markers=True)
fig_faturamento_mes.update_layout(xaxis=dict(tickformat="%b %Y", dtick="M1"))
fig_faturamento_mes.update_xaxes(title_text="<b>Mês da Emissão</b>", title_font=dict(size=16))
fig_faturamento_mes.update_yaxes(title_text="<b>Faturamento (R$)</b>", title_font=dict(size=16), tickprefix="R$ ")
fig_faturamento_mes.update_traces(hovertemplate='Mês: %{x|%B de %Y}<br>Faturamento: R$ %{y:,.2f}<extra></extra>')
st.plotly_chart(fig_faturamento_mes, use_container_width=True)
st.markdown("---")

# --- SEÇÃO INFERIOR COM DUAS COLUNAS ---
col_esquerda, col_direita = st.columns(2)
with col_esquerda:
    st.header("🏆 Performance dos Vendedores")
    vendas_por_vendedor = df.groupby(coluna_vendedor_id).agg(Faturamento=('Faturamento_Limpo', 'sum'), Nome=(coluna_nome_vendedor, 'first')).sort_values(by='Faturamento', ascending=False).reset_index()
    vendas_por_vendedor['Nome_Abreviado'] = vendas_por_vendedor['Nome'].apply(abreviar_vendedor)
    fig_vendedores = px.bar(vendas_por_vendedor, x='Nome_Abreviado', y='Faturamento', title='Vendas por Vendedor', text_auto='.2s', labels={'Faturamento': 'Total de Vendas (R$)', 'Nome_Abreviado': 'Vendedor'}, hover_data=['Vendedor', 'Nome'], color='Faturamento', color_continuous_scale='Blues')
    v_max = vendas_por_vendedor['Faturamento'].max() if not vendas_por_vendedor.empty else 0
    fig_vendedores.update_traces(hovertemplate='<b>%{customdata[1]}</b><br>ID: %{customdata[0]}<br>Vendas: R$ %{y:,.2f}<extra></extra>')
    fig_vendedores.update_layout(coloraxis_showscale=False, coloraxis=dict(cmin=0, cmax=v_max * 1.5))
    fig_vendedores.update_xaxes(title_text="<b>Vendedor</b>", title_font=dict(size=14))
    fig_vendedores.update_yaxes(title_text="<b>Total de Vendas (R$)</b>", title_font=dict(size=14), tickprefix="R$ ")
    st.plotly_chart(fig_vendedores, use_container_width=True)

with col_direita:
    st.header("📈 Crescimento Acumulativo de Vendas")
    if pd.notna(df[coluna_data_emissao]).all():
        df_safra = df[df[coluna_data_emissao].dt.year.isin([2024, 2025])].copy()
        if not df_safra.empty:
            df_safra.sort_values(by=[coluna_nome_vendedor, coluna_data_emissao], inplace=True)
            df_safra['Faturamento_Acumulado'] = df_safra.groupby(coluna_nome_vendedor)['Faturamento_Limpo'].cumsum()
            fig_acumulativo = px.line(df_safra, x=coluna_data_emissao, y='Faturamento_Acumulado', color=coluna_nome_vendedor, title='Crescimento Acumulativo de Vendas por Vendedor', labels={coluna_data_emissao: 'Data da Emissão', 'Faturamento_Acumulado': 'Faturamento Acumulado (R$)', coluna_nome_vendedor: 'Vendedor'}, markers=True)
            fig_acumulativo.update_traces(line=dict(width=3))
            fig_acumulativo.update_layout(xaxis_title="<b>Data da Emissão</b>", yaxis_title="<b>Faturamento Acumulado (R$)</b>", legend_title="<b>Vendedor</b>", yaxis_tickprefix="R$ ")
            fig_acumulativo.update_traces(hovertemplate='<b>%{full_name}</b><br>Data: %{x|%d/%m/%Y}<br>Acumulado: R$ %{y:,.2f}<extra></extra>')
            st.plotly_chart(fig_acumulativo, use_container_width=True)
        else:
            st.info("Não há dados de faturamento para a safra 24/25 para exibir.")
    else:
        st.warning("A coluna de data não pôde ser processada.")

st.markdown("---")

# --- EXIBINDO OS DADOS BRUTOS ---
with st.expander("Visualizar dados brutos"):
    st.dataframe(df)
