import folium
import geopandas as gpd
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_folium import folium_static

# Carregar os dados processados
df_acidentes = pd.read_csv('acidentes_processados.csv', sep=';')
gdf_mapa = gpd.read_file('mapa_processado.json')

# Verificar se as colunas 'mes_acidente' e 'ano_acidente' estão presentes
if 'mes_acidente' not in df_acidentes.columns or 'ano_acidente' not in df_acidentes.columns:
    raise KeyError("As colunas 'mes_acidente' e/ou 'ano_acidente' não estão presentes no CSV processado.")

# Obter a lista de anos e meses disponíveis nos dados
anos_disponiveis = df_acidentes['ano_acidente'].unique()
anos_disponiveis.sort()
meses_disponiveis = df_acidentes['mes_acidente'].unique()
meses_disponiveis.sort()

# Configurar o Streamlit para posicionar a caixa de seleção à esquerda
st.title('Análise de Acidentes em Mato Grosso do Sul')
st.sidebar.title('Opções de Visualização')

# Criar seleções de ano e mês interativas
ano_selecionado = st.sidebar.selectbox('Selecione o Ano', ['Todos os Anos'] + list(anos_disponiveis))
mes_selecionado = st.sidebar.selectbox('Selecione o Mês', ['Todos os Meses'] + list(meses_disponiveis))

# Filtrar os dados com base nas seleções
if ano_selecionado == 'Todos os Anos' and mes_selecionado == 'Todos os Meses':
    df_filtrado = df_acidentes
elif ano_selecionado == 'Todos os Anos':
    df_filtrado = df_acidentes[df_acidentes['mes_acidente'] == mes_selecionado]
elif mes_selecionado == 'Todos os Meses':
    df_filtrado = df_acidentes[df_acidentes['ano_acidente'] == ano_selecionado]
else:
    df_filtrado = df_acidentes[(df_acidentes['ano_acidente'] == ano_selecionado) & (df_acidentes['mes_acidente'] == mes_selecionado)]

# Verificar se a coluna 'dia_semana' está presente no DataFrame filtrado
if 'dia_semana' not in df_filtrado.columns:
    raise KeyError("A coluna 'dia_semana' não está presente no DataFrame filtrado.")

# Agrupar os dados de acidentes pela coluna 'codigo_ibge' após filtragem
acidentes_por_cidade = df_filtrado.groupby('codigo_ibge').size().reset_index(name='qtd_acidente')

# Converter 'codigo_ibge' para tipo objeto (string)
acidentes_por_cidade['codigo_ibge'] = acidentes_por_cidade['codigo_ibge'].astype(str)

# Unir os dados de acidentes do CSV com o mapa JSON usando a coluna 'id' no JSON e 'codigo_ibge' no CSV
gdf_mapa = gdf_mapa.merge(acidentes_por_cidade, left_on='id', right_on='codigo_ibge', how='left')
gdf_mapa['qtd_acidente'] = gdf_mapa['qtd_acidente'].fillna(0)

# Criar o mapa interativo usando Folium
m = folium.Map(location=[-20.4428, -54.6468], zoom_start=6)

folium.Choropleth(
    geo_data=gdf_mapa,
    name='choropleth',
    data=gdf_mapa,
    columns=['id', 'qtd_acidente'],
    key_on='feature.properties.id',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name='Quantidade de Acidentes por Cidade'
).add_to(m)

# Adicionar popups para exibir a quantidade de acidentes ao clicar na cidade
for _, row in gdf_mapa.iterrows():
    folium.Marker(
        location=[row['geometry'].centroid.y, row['geometry'].centroid.x],
        popup=folium.Popup(
            f"<b>{row['name']}</b><br>"
            f"<table>"
            f"<tr><td>Quantidade de Acidentes:</td><td>{int(row['qtd_acidente'])}</td></tr>"
            f"</table>",
            max_width=300
        )
    ).add_to(m)

# Adicionar controle de camadas
folium.LayerControl().add_to(m)

# Gráfico de barras para acidentes por mês e ano
def criar_grafico_barras(df, titulo):
    fig = px.bar(
        df.groupby('mes_acidente').size().reset_index(name='qtd_acidente'),
        x='mes_acidente',
        y='qtd_acidente',
        labels={'mes_acidente': 'Mês', 'qtd_acidente': 'Quantidade de Acidentes'},
        title=titulo
    )
    return fig
# Gráfico de barras para acidentes com óbitos por mês
def criar_grafico_obitos(df, titulo):
    fig = px.bar(
        df.groupby('mes_acidente')['qtde_acid_com_obitos'].sum().reset_index(),
        x='mes_acidente',
        y='qtde_acid_com_obitos',
        labels={'mes_acidente': 'Mês', 'qtde_acid_com_obitos': 'Quantidade de Acidentes com Óbitos'},
        title=titulo
    )
    return fig


# Gráfico das cidades com maiores índices de mortalidade
def criar_grafico_mortalidade(df, titulo):
    df_mortalidade = df.groupby('codigo_ibge').agg(
        {'qtde_acid_com_obitos': 'sum', 'num_acidente': 'count'}).reset_index()
    df_mortalidade['indice_mortalidade'] = df_mortalidade['qtde_acid_com_obitos'] / df_mortalidade['num_acidente']
    df_mortalidade = df_mortalidade.sort_values(by='indice_mortalidade', ascending=False).head(10)
    df_mortalidade['codigo_ibge'] = df_mortalidade['codigo_ibge'].astype(str)  # Converter para string
    df_mortalidade = df_mortalidade.merge(gdf_mapa[['id', 'name']], left_on='codigo_ibge', right_on='id', how='left')

    fig = px.line(
        df_mortalidade,
        x='name',
        y='indice_mortalidade',
        labels={'name': 'Cidade', 'indice_mortalidade': 'Índice de Mortalidade'},
        title=titulo
    )
    return fig
# Gráfico de barras para acidentes por condições meteorológicas
def criar_grafico_condicoes_meteorologicas(df, titulo):
    condicoes_meteorologicas = df['cond_meteorologica'].value_counts().reset_index()
    condicoes_meteorologicas.columns = ['cond_meteorologica', 'count']  # Renomear as colunas
    fig = px.bar(
        condicoes_meteorologicas,
        x='cond_meteorologica',
        y='count',
        labels={'cond_meteorologica': 'Condição Meteorológica', 'count': 'Quantidade de Acidentes'},
        title=titulo
    )
    return fig

# Gráfico de acidentes por fase do dia
def criar_grafico_fase_dia(df, titulo):
    fase_dia = df['fase_dia'].value_counts().reset_index()
    fase_dia.columns = ['fase_dia', 'count']
    fig = px.pie(
        fase_dia,
        names='fase_dia',
        values='count',
        title=titulo,
        hole=0.4
    )
    return fig


# Função para criar gráfico combinado
def criar_grafico_tipo_acidente(df, titulo):
    fase_dia = df['tp_acidente'].value_counts().reset_index()
    fase_dia.columns = ['tp_acidente', 'count']
    fig = px.pie(
        fase_dia,
        names='tp_acidente',
        values='count',
        title=titulo,
        hole=0.4
    )
    return fig.update_layout(width=800, height=600)

meses = {
    1: 'Janeiro',
    2: 'Fevereiro',
    3: 'Março',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro'
}
numero_mes = mes_selecionado.astype(int)
nome_mes = meses[numero_mes]

# Definir o título do gráfico com base nas seleções
if ano_selecionado == 'Todos os Anos' and mes_selecionado == 'Todos os Meses':
    titulo_grafico = 'Quantidade de Acidentes por Mês (Todos os Anos)'
    titulo_grafico_obitos = 'Quantidade de Acidentes com Óbitos por Mês (Todos os Anos)'
    titulo_grafico_mortalidade = 'Cidades com Maiores Índices de Mortalidade (Todos os Anos)'
    titulo_grafico_condicoes = 'Quantidade de Acidentes por Condições Meteorológicas (Todos os Anos)'
    titulo_grafico_fase_dia = 'Quantidade de Acidentes por Fase do Dia (Todos os Anos)'
    titulo_grafico_combinado = 'Quantidade de Acidentes  (Todos os Anos)'

elif ano_selecionado == 'Todos os Anos':
    titulo_grafico = f'Quantidade de Acidentes em {nome_mes} (Todos os Anos)'
    titulo_grafico_obitos = f'Quantidade de Acidentes com Óbitos em {nome_mes} (Todos os Anos)'
    titulo_grafico_mortalidade = f'Cidades com Maiores Índices de Mortalidade em {nome_mes} (Todos os Anos)'
    titulo_grafico_condicoes = f'Quantidade de Acidentes por Condições Meteorológicas em {nome_mes} (Todos os Anos)'
    titulo_grafico_fase_dia = f'Quantidade de Acidentes por Fase do Dia em {nome_mes} (Todos os Anos)'
    titulo_grafico_combinado = f'Quantidade de Acidentes {nome_mes} (Todos os Anos)'

elif mes_selecionado == 'Todos os Meses':
    titulo_grafico = f'Quantidade de Acidentes por Mês em {ano_selecionado}'
    titulo_grafico_obitos = f'Quantidade de Acidentes com Óbitos por Mês em {ano_selecionado}'
    titulo_grafico_mortalidade = f'Cidades com Maiores Índices de Mortalidade em {ano_selecionado}'
    titulo_grafico_condicoes = f'Quantidade de Acidentes por Condições Meteorológicas em {ano_selecionado}'
    titulo_grafico_fase_dia = f'Quantidade de Acidentes por Fase do Dia em {ano_selecionado}'
    titulo_grafico_combinado = f'Quantidade de Acidentes {ano_selecionado}'

else:
    titulo_grafico = f'Quantidade de Acidentes em {nome_mes} de {ano_selecionado}'
    titulo_grafico_obitos = f'Quantidade de Acidentes com Óbitos em {nome_mes} de {ano_selecionado}'
    titulo_grafico_mortalidade = f'Cidades com Maiores Índices de Mortalidade em {nome_mes} de {ano_selecionado}'
    titulo_grafico_condicoes = f'Quantidade de Acidentes por Condições Meteorológicas em {nome_mes} de {ano_selecionado}'
    titulo_grafico_fase_dia = f'Quantidade de Acidentes por Fase do Dia em {nome_mes} de {ano_selecionado}'
    titulo_grafico_combinado = f'Quantidade de Acidentes por  {nome_mes} de {ano_selecionado}'



# Exibir o mapa no dashboard
st.header('Mapa de Acidentes por Cidade')
folium_static(m)

# Exibir o gráfico de barras no dashboard
st.header(titulo_grafico)
st.plotly_chart(criar_grafico_barras(df_filtrado, titulo_grafico))

# Exibir o gráfico de acidentes com óbitos no dashboard
st.header(titulo_grafico_obitos)
st.plotly_chart(criar_grafico_obitos(df_filtrado, titulo_grafico_obitos))

# Exibir o gráfico das cidades com maiores índices de mortalidade no dashboard
st.header(titulo_grafico_mortalidade)
st.plotly_chart(criar_grafico_mortalidade(df_filtrado, titulo_grafico_mortalidade))

st.header(titulo_grafico_condicoes)
st.plotly_chart(criar_grafico_condicoes_meteorologicas(df_filtrado, titulo_grafico_condicoes))

st.header(titulo_grafico_fase_dia)
st.plotly_chart(criar_grafico_fase_dia(df_filtrado, titulo_grafico_fase_dia))

st.header(titulo_grafico_combinado)
st.plotly_chart(criar_grafico_tipo_acidente(df_filtrado, titulo_grafico_combinado))




