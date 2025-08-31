# %%
# 01_data_cleaning.py
# Notebook-esqueleto: limpeza e preparação espacial dos dados
# Ajuste caminhos e nomes de colunas conforme seus arquivos


import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')


# %%
# --- Configurações iniciais (caminhos) ---
DATA_RAW = "../data_raw"
DATA_CLEAN = "../data_clean"


# arquivos (ajuste estes nomes conforme seu repositório)
PROPS_FILE = f"{DATA_RAW}/propriedades.shp" # ou .gpkg/.csv com colunas lon/lat
ULES_FILE = f"{DATA_RAW}/ules.shp"


# CRS alvo (exemplo: SIRGAS 2000 / UTM zona 22S -> EPSG:31982 | ajuste conforme sua área)
TARGET_CRS = "EPSG:31983"


# %%
# --- Carregar dados ---
print('Carregando dados...')
props = gpd.read_file(PROPS_FILE)
ules = gpd.read_file(ULES_FILE)
print(f'Propriedades: {len(props)} registros | ULEs: {len(ules)} polígonos')


# %%
# --- Verificar e ajustar CRS ---
print('CRS originais:')
print('props.crs =', props.crs)
print('ules.crs =', ules.crs)


if props.crs is None:
raise ValueError('props sem CRS: defina manualmente a projeção ou carregue com crs correto')


# reprojetar para CRS objetivo
props = props.to_crs(TARGET_CRS)
ules = ules.to_crs(TARGET_CRS)
print('Reprojetado para', TARGET_CRS)

# %%
# --- Se as propriedades estiverem como pontos e não contiverem coluna de ULE: spatial join ---
if 'ule_id' not in props.columns:
print('Associando propriedades às ULEs por spatial join (centroides)')
# trabalhar com centroides para evitar problemas quando pontos são polígonos
if props.geometry.geom_type.isin(['Point']).all():
pts = props
else:
pts = props.copy()
pts['geometry'] = pts.geometry.centroid


pts = pts.set_geometry('geometry')
joined = gpd.sjoin(pts, ules[['ule_id', 'geometry']], how='left', predicate='within')
# garantir que volta à geometria original (se necessário)
# se props eram polígonos, restaurar a geometria original
if props.geometry.geom_type.isin(['Point']).all() is False:
joined = joined.drop(columns=['geometry']).merge(props.drop(columns=['geometry']), left_index=True, right_index=True)
props = joined.drop(columns=['index_right'])
print('Join completo. Colunas atuais:', props.columns.tolist())


# %%
# --- Estatísticas básicas e tratamento de missing ---
print('\nEstatísticas resumidas:')
if 'percepcao_escore' in props.columns:
display(props['percepcao_escore'].describe())
else:
print('A coluna "percepcao_escore" não foi encontrada — ajuste o nome da coluna no script')


# exemplo simples de imputação por grupo
if 'tipo_manejo' in props.columns and 'percepcao_escore' in props.columns:
props['percepcao_escore'] = props.groupby('tipo_manejo')['percepcao_escore'].transform(lambda x: x.fillna(x.median()))
print('Imputação por mediana por tipo_manejo concluída')


# %%
# --- Criar variáveis derivadas de exemplo ---
# Exemplo: normalizar intensidade de insumos para 0-1
if 'intensidade_insumos' in props.columns:
mi = props['intensidade_insumos'].min()
ma = props['intensidade_insumos'].max()
if mi != ma:
props['insumos_norm'] = (props['intensidade_insumos'] - mi) / (ma - mi)
print('Coluna insumos_norm criada')


# %%
# --- Salvar dados limpos ---
import os
os.makedirs(DATA_CLEAN, exist_ok=True)
CLEAN_PATH = f"{DATA_CLEAN}/propriedades_clean.gpkg"
props.to_file(CLEAN_PATH, layer='propriedades', driver='GPKG')
print('Dados limpos salvos em', CLEAN_PATH)


# %%
# --- Visualização rápida ---
try:
base = ules.plot(edgecolor='k', linewidth=0.4, alpha=0.5)
props.plot(ax=base, markersize=10)
plt.title('ULEs e pontos de propriedade (visualização rápida)')
plt.show()
except Exception as e:
print('Erro ao plotar:', e)


# %%
# Próximos passos sugeridos:
# - rodar notebooks/02_EDA.ipynb para análises descritivas
# - rodar notebooks/03_spatial_analysis.ipynb para Moran's I, LISA e regressões espaciais