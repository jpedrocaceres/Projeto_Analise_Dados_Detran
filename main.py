import pandas as pd
import geopandas as gpd

# Carregar a base de dados de acidentes
df_acidentes = pd.read_csv('DADOS_ACIDENTES.csv', sep=';')

# Converter a coluna 'data_acidente' para o formato datetime
df_acidentes['data_acidente'] = pd.to_datetime(df_acidentes['data_acidente'], format='%d/%m/%Y', errors='coerce')

# Verificar se a conversão foi bem-sucedida
print("Valores na coluna 'data_acidente' após conversão:")
print(df_acidentes['data_acidente'].head())

# Extrair o mês e ano da coluna 'data_acidente'
df_acidentes['mes_acidente'] = df_acidentes['data_acidente'].dt.month
df_acidentes['ano_acidente'] = df_acidentes['data_acidente'].dt.year

# Verificar se as novas colunas foram adicionadas corretamente
print("Colunas 'mes_acidente' e 'ano_acidente':")
print(df_acidentes[['mes_acidente', 'ano_acidente']].head())

# Carregar o mapa em JSON
gdf_mapa = gpd.read_file('geojs-50-mun.json')

# Verificar as colunas do JSON
print("Colunas no JSON de mapa:", gdf_mapa.columns)

# Converter as colunas 'id' e 'codigo_ibge' para string para garantir a compatibilidade durante a junção
gdf_mapa['id'] = gdf_mapa['id'].astype(str)
df_acidentes['codigo_ibge'] = df_acidentes['codigo_ibge'].astype(str)

# Salvar os dados processados para uso no dashboard
df_acidentes.to_csv('acidentes_processados.csv', index=False, sep=";")
gdf_mapa.to_file('mapa_processado.json', driver='GeoJSON')

# Verificar as colunas do CSV salvo
df_verificacao = pd.read_csv('acidentes_processados.csv', sep=";")
print("Colunas no CSV processado:", df_verificacao.columns)

