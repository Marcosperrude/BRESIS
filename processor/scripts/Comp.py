#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 17:39:39 2026

@author: marcos
"""
import os 
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
#Pasta do repositório
DataDir = '/home/marcos/Documents/LCQAR/emiResidenciais'
DataPath = os.path.join(DataDir,'inputs')
OutPath = os.path.join(DataDir, 'outputs')

EDGARPath = '/home/marcos/Documents/LCQAR/emiResidenciais/inputs/bkl_BUILDINGS_emi_nc'

BR_UF = gpd.read_file(os.path.join(DataPath, 'BR_UF_2023', 'BR_UF_2023.shp'))
BR_UF = BR_UF.to_crs("EPSG:4326")#%%
#%%
# import xarray as xr
# import os

# # =========================
# # CONFIGURAÇÕES
# # =========================

# ano = '2023'
# meses = [1]  # pode expandir depois
# combustiveis = ['Lenha','Carvao','Butano','Propano']

# # período desejado (5 primeiros dias)
# time_slice = slice('2023-01-01', '2023-01-02 23:00:00')

# # =========================
# # PROCESSAMENTO
# # =========================
# lista_mensal = []

# for mes in meses:
    
#     lista_comb = []
    
#     for combustivel in combustiveis:
        
#         pasta = os.path.join(
#             OutPath, 'emissoes', 'UE', combustivel, ano, f'{ano}_{mes}.nc'
#         )
        
#         print(f'Lendo: {combustivel} mês {mes}')
        
#         # abre lazy (sem carregar tudo)
#         ds = xr.open_dataset(pasta, chunks={'time': 24})
        
#         # seleciona apenas os 5 primeiros dias
#         ds_sel = ds.sel(time=time_slice)
        
#         lista_comb.append(ds_sel)
    
#     # soma combustíveis (mantém todos poluentes)
#     soma_mes = xr.concat(lista_comb, dim='combustivel').sum(dim='combustivel')
    
#     lista_mensal.append(soma_mes)

# # concatenar no tempo (caso tenha vários meses)
# EMISSOES_total = xr.concat(lista_mensal, dim='time')

# # =========================
# # CONVERSÃO DE UNIDADE
# # ton/h → g/s
# # =========================
# EMISSOES_total = (EMISSOES_total * 1e6) / 3600

# # =========================
# # FILTRO (opcional)
# # remove zeros (melhora compressão)
# # =========================
# EMISSOES_total = EMISSOES_total.where(EMISSOES_total > 0)

# # =========================
# # COMPRESSÃO E SALVAMENTO
# # =========================
# encoding = {
#     var: {
#         "zlib": True,
#         "complevel": 5
#     }
#     for var in EMISSOES_total.data_vars
# }

# arquivo_saida = os.path.join(
#     '/home/marcos/Documents/LCQAR/emiResidenciais/outputs/emissoes_teste', f'emissoes_5dias_{ano}.nc'
# )

# os.makedirs(os.path.dirname(arquivo_saida), exist_ok=True)

# print('Salvando arquivo...')
# EMISSOES_total.to_netcdf(arquivo_saida, encoding=encoding)

# print('✔ Finalizado com sucesso!')
#%%
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

a= xr.open_dataset(
    '/home/marcos/Documents/LCQAR/emiResidenciais/outputs/emissoes_teste/emissoes_5dias_2023.nc')

plt.figure(figsize=(6,5))

a['CO'][0].plot(
    norm=LogNorm(vmin=0.001, vmax=30),
    cmap='inferno'
)



plt.title('Emissões (log)')
plt.show()


#%%
lista = []
# pasta = os.path.join(OutPath, 'emissoes','AP42', 'Lenha', '2023', '2023_1.nc')
# a = xr.open_dataset(pasta)['CO']
for combustivel in ['Lenha','Carvao','Butano','Propano']:
    for mes in [1]:
        pasta = os.path.join(OutPath, 'emissoes','UE', combustivel, '2023', f'2023_{mes}.nc')
        lista.append(xr.open_dataset(pasta)['CO'])
        
EMISSOES_total = sum(lista)
EMISSOES_total = (EMISSOES_total * 1000000)/(60*60)
#%% Emissoes AP42
# lista_mensal = []

# for mes in range(1, 13):
    
#     lista_comb = []
#     for combustivel in ['Lenha','Carvao', 'Butano', 'Propano']:
#         pasta = os.path.join(
#             OutPath, 'emissoes','UE', combustivel, '2023', f'2023_{mes}.nc'
#         )
#         lista_comb.append(xr.open_dataset(pasta)['CO'])
#     lista_mensal.append(sum(lista_comb))

EMISSOES_total = xr.concat(lista_mensal, dim='time')

EMISSOES_marcos_jan_ap42 = EMISSOES_marcos_ap42.sum(dim='time')
EMISSOES_marcos_jan_g_ap42 = (EMISSOES_marcos_jan_ap42*1000000)/(30*24*60*60)
EMISSOES_marcos_jan_g_ap42 = EMISSOES_marcos_jan_g_ap42.rio.set_spatial_dims( 
    x_dim="lon", y_dim="lat" )
EMISSOES_marcos_jan_g_ap42 = EMISSOES_marcos_jan_g_ap42.rio.write_crs("EPSG:4326") 
EMISSOES_marcos_jan_g_ap42 = EMISSOES_marcos_jan_g_ap42.rio.clip(
    BR_UF.geometry, BR_UF.crs, drop=True, all_touched=True )
#%%

import os
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd


# ========================
# 2. EDGAR
# ========================

EDGAR_Emission = xr.open_dataset(os.path.join(DataPath,
            'bkl_BUILDINGS_emi_nc','v8.1_FT2022_AP_CO_2022_bkl_BUILDINGS_emi.nc'))

EDGAR_Emission_jan = EDGAR_Emission['emissions'].isel(time=0)

EDGAR_Emission_jan = EDGAR_Emission_jan.rio.write_crs("EPSG:4326")

EDGAR_Emission_jan = EDGAR_Emission_jan.rio.clip(
    BR_UF.geometry,
    BR_UF.crs,
    drop=True,
    all_touched=True
)
EDGAR_Emission_jan_g = (EDGAR_Emission_jan * 1000000)/(30*24*60*60)

# ========================
# 3. AP42 (SEU)
# ========================
lista = []
for combustivel in ['Lenha','Carvao','Butano','Propano']:
    pasta = os.path.join(
        OutPath, 'emissoes','UE',
        combustivel, '2023', '2023_1.nc'
    )
    lista.append(xr.open_dataset(pasta)['CO'])

EMISSOES_marcos_ap42 = sum(lista)

EMISSOES_marcos_jan_ap42 = EMISSOES_marcos_ap42.sum(dim='time')

EMISSOES_marcos_jan_g_ap42 = (EMISSOES_marcos_jan_ap42 * 1e6) / (30 * 24 * 60 * 60)

EMISSOES_marcos_jan_g_ap42 = EMISSOES_marcos_jan_g_ap42.rio.set_spatial_dims(
    x_dim="lon", y_dim="lat"
)
EMISSOES_marcos_jan_g_ap42 = EMISSOES_marcos_jan_g_ap42.rio.write_crs("EPSG:4326")

EMISSOES_marcos_jan_g_ap42 = EMISSOES_marcos_jan_g_ap42.rio.clip(
    BR_UF.geometry,
    BR_UF.crs,
    drop=True,
    all_touched=True
)

# ========================
# 4. FUNÇÃO DE ESTATÍSTICA
# ========================
def calc_stats(data_array):
    valores = data_array.values.flatten()
    valores = valores[~np.isnan(valores)]

    if len(valores) == 0:
        return None

    return {
        'p25': np.percentile(valores, 25),
        'p50': np.percentile(valores, 50),
        'p75': np.percentile(valores, 75),
        'p98': np.percentile(valores, 98),
        'mean': np.mean(valores),
        'median': np.median(valores),
        'min': np.min(valores),
        'max': np.max(valores),
        'sum': np.sum(valores)
    }

# ========================
# 5. LOOP POR UF
# ========================
resultados = []

for _, uf in BR_UF.iterrows():
    
    nome_uf = uf['SIGLA_UF'] if 'SIGLA_UF' in uf else uf['NM_UF']
    geom = [uf.geometry]

    try:
        edgar_clip = EDGAR_Emission_jan_g.rio.clip(
            geom, BR_UF.crs, drop=True, all_touched=True
        )

        ap42_clip = EMISSOES_marcos_jan_g_ap42.rio.clip(
            geom, BR_UF.crs, drop=True, all_touched=True
        )

        stats_edgar = calc_stats(edgar_clip)
        stats_ap42 = calc_stats(ap42_clip)

        if stats_edgar and stats_ap42:
            linha = {'UF': nome_uf}

            for k in stats_edgar:
                linha[f'EDGAR_{k}'] = stats_edgar[k]
                linha[f'AP42_{k}'] = stats_ap42[k]

            resultados.append(linha)

    except Exception as e:
        print(f'Erro na UF {nome_uf}: {e}')

# ========================
# 6. CSV FINAL
# ========================
df = pd.DataFrame(resultados)

out_csv = os.path.join(OutPath, 'comparacao_regional_EDGAR_AP42.csv')
df.to_csv(out_csv, index=False)

print('Salvo em:', out_csv)
#%%
# import matplotlib.pyplot as plt

# combustiveis = ['Lenha','Carvao','Butano','Propano']

# fig, axes = plt.subplots(2, 2, figsize=(10,8))

# for i, ax in enumerate(axes.flat):
    
#     da = lista[i]
    
#     # soma no tempo
#     da_time = da.sum(dim='time')
    
#     # plot espacial
#     da_time.plot(ax=ax)
    
#     ax.set_title(combustiveis[i])

# plt.suptitle('Soma temporal de CO (mapa por combustível)')
# plt.tight_layout()
# plt.show()
#%%


pasta_uf = [f for f in os.listdir(setores) if f.startswith('CE')][0]
shapefile_path = os.path.join(setores, pasta_uf)
shp_file = [f for f in os.listdir(shapefile_path) if f.endswith(".shp")][0]
gdf_uf = gpd.read_file(os.path.join(shapefile_path, shp_file))
gdf_uf['CD_SETOR'] = gdf_uf['CD_SETOR'].astype(str)


import xarray as xr
import geopandas as gpd
import os
from shapely.geometry import box

# ================================
# 1. Encontrar o ponto de máximo
# ================================
where_max = EMISSOES_marcos_ap42.where(
    EMISSOES_marcos_ap42 == EMISSOES_marcos_ap42.max(),
    drop=True
)

# pegar o primeiro (caso haja mais de um)
time_max = where_max['time'].values[0]
lat_max  = float(where_max['lat'].values[0])
lon_max  = float(where_max['lon'].values[0])

print("Máximo encontrado em:")
print("Tempo:", time_max)
print("Lat:", lat_max)
print("Lon:", lon_max)

# ================================
# 2. Criar polígono do pixel
# ================================
res_lat = float(abs(EMISSOES_marcos_ap42.lat[1] - EMISSOES_marcos_ap42.lat[0]))
res_lon = float(abs(EMISSOES_marcos_ap42.lon[1] - EMISSOES_marcos_ap42.lon[0]))

pixel_poly = box(
    lon_max - res_lon/2,
    lat_max - res_lat/2,
    lon_max + res_lon/2,
    lat_max + res_lat/2
)

gdf_pixel = gpd.GeoDataFrame(geometry=[pixel_poly], crs="EPSG:4326")

# ================================
# 3. Ler setores censitários (IBGE)
# ================================
setores_path = os.path.join(DataPath, 'Setores')

setores = gpd.read_file(setores_path)

# garantir mesmo CRS
setores = setores.to_crs("EPSG:4326")

# ================================
# 4. Interseção espacial
# ================================
setores_intersect = gpd.sjoin(
    gdf_uf,
    gdf_pixel,
    how='inner',
    predicate='intersects'
)

#%%

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(8,8))

# todos os setores (fundo)
gdf_uf.plot(ax=ax, linewidth=0.2)

# setores que intersectam
setores_intersect.plot(ax=ax)

# pixel
gdf_pixel.boundary.plot(ax=ax, linewidth=2)

# ponto do máximo
ax.scatter(lon_max, lat_max, s=100)

# zoom na área do pixel
ax.set_xlim(lon_max - res_lon*5, lon_max + res_lon*5)
ax.set_ylim(lat_max - res_lat*5, lat_max + res_lat*5)

ax.set_title('Interseção: Setores Censitários x Pixel de Máxima Emissão')

plt.show()
#%%

WoodCoalDf['CD_SETOR'] = WoodCoalDf['CD_SETOR'].astype(str)
A = A.astype(str)


subset = WoodCoalDf[
    WoodCoalDf['CD_SETOR'].isin(A)

#%%



EDGAR_Emission = xr.open_dataset(os.path.join(DataPath,
            'bkl_BUILDINGS_emi_nc','v8.1_FT2022_AP_CO_2022_bkl_BUILDINGS_emi.nc'))

EDGAR_Emission_jan = EDGAR_Emission['emissions'].isel(time=0)

EDGAR_Emission_jan = EDGAR_Emission_jan.rio.write_crs("EPSG:4326")

EDGAR_Emission_jan = EDGAR_Emission_jan.rio.clip(
    BR_UF.geometry,
    BR_UF.crs,
    drop=True,
    all_touched=True
)
EDGAR_Emission_jan_g = (EDGAR_Emission_jan * 1000000)/(30*24*60*60)

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

# remover zeros
EDGAR_plot = EDGAR_Emission_jan_g.where(EDGAR_Emission_jan_g > 0)
MARCOS_plot = EMISSOES_marcos_jan_g_ap42.where(EMISSOES_marcos_jan_g_ap42 > 0)

# escala log fixa
norm = LogNorm(vmin=0.001, vmax=70)

fig, ax = plt.subplots(1, 2, figsize=(14,6))

EDGAR_plot.plot(ax=ax[0], norm=norm)
MARCOS_plot.plot(ax=ax[1], norm=norm)

plt.show()
#%%

lista = []

for combustivel in ['Lenha','Carvao','Butano','Propano']:
    for mes in [1,2]:
        pasta = os.path.join(OutPath, 'emissoes','UE', combustivel, '2023', f'2023_{mes}.nc')
    
        ds = xr.open_dataset(pasta)
        lista.append(ds)

# somar emissões de todos combustíveis para todos poluentes
EMISSOES_marcos_ap42 = sum(lista)
#%%
import os
import xarray as xr

combustiveis = ['Lenha','Carvao','Butano','Propano']
lista_combustiveis = []

for combustivel in combustiveis:
    
    lista_meses = []
    
    for mes in [1, 2]:
        pasta = os.path.join(
            OutPath, 'emissoes','UE', combustivel, '2023', f'2023_{mes}.nc'
        )
        
        print(f"Lendo: {combustivel} - mês {mes}")
        
        ds = xr.open_dataset(pasta, chunks={"lat": 100, "lon": 100})
        
        # reduzir peso
        ds = ds.astype("float32")
        
        lista_meses.append(ds)
    
    # 🔥 concatena meses corretamente (agora time não quebra)
    ds_comb = xr.concat(lista_meses, dim="time")
    
    lista_combustiveis.append(ds_comb)

# 🔥 agora soma entre combustíveis
EMISSOES_marcos_ap42 = sum(lista_combustiveis)

# compressão
encoding = {
    var: {"zlib": True, "complevel": 5}
    for var in EMISSOES_marcos_ap42.data_vars
}

output_file = os.path.join(OutPath, "emissoes_total_2023_jan_fev.nc")

EMISSOES_marcos_ap42.to_netcdf(output_file, encoding=encoding)

#%%
import xarray as xr
import os

lista = []
poluentes = ['PM10' ,'PM2.5','NMVOC','CO','SOx','NOx'] 

for combustivel in ['Lenha','Carvao','Butano','Propano']:
    
    pasta = os.path.join(OutPath, 'emissoes_teste',
                         f'{combustivel}_2023_01_01_2023_01_06.nc')
    
    ds = xr.open_dataset(pasta, chunks={'time':24})

    vars_existentes = [p for p in poluentes if p in ds.data_vars]

    lista.append(ds[vars_existentes])

# concatena e soma
ds_total = xr.concat(lista, dim='combustivel').sum('combustivel')

# salva
ds_total.to_netcdf(
    "/home/marcos/Documents/LCQAR/emiResidenciais/outputs/emissoes_teste/residencias_camilo.nc"
)


camilo = xr.open_dataset('/home/marcos/Documents/LCQAR/emiResidenciais/outputs/emissoes_teste/residencias_camilo.nc')

#%%

import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np

# separar datasets
ds_lenha   = lista[0]
ds_carvao  = lista[1]
ds_butano  = lista[2]
ds_propano = lista[3]


# calcular limites globais (>0 obrigatório pro log)
valores = []
for ds in [ds_lenha, ds_carvao, ds_butano, ds_propano]:
    v = ds.isel(time=0).values
    v = v[v > 0]
    valores.append(v)

vmin = min(v.min() for v in valores)
vmax = max(v.max() for v in valores)

fig, ax = plt.subplots(2, 2, figsize=(12, 8))

for axi, (ds, nome) in zip(ax.flatten(), [
    (ds_lenha, 'Lenha'),
    (ds_carvao, 'Carvão'),
    (ds_butano, 'Butano'),
    (ds_propano, 'Propano')
]):
    
    da = ds.isel(time=0)
    
    da.plot(
        ax=axi,
        norm=LogNorm(vmin=vmin, vmax=vmax)
    )
    
    axi.set_title(nome)

plt.tight_layout()
plt.show()

