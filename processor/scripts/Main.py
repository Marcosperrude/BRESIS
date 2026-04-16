# -*- coding: utf-8 -*-
"""
Created on Tue Apr 15 14:43:17 2025

@author: Marcos.Perrude
"""
import pandas as pd 
import geopandas as gpd
import numpy as np
from EmissionsEstimateWoodCoal_novo import emissionEstimateWoodCoal
import os
from EmissionsPixels import EmissionsPixelsWoodCoal,GridMat5D , EmissionsPixelsGLP , GridMat7D
from CreateGrid import CreateGrid
import matplotlib.pyplot as plt
import xarray as xr
from temporalDisagg import temporalDisagg
from EmissionsEstimateGLP import emissionEstimateGLP 
from local2UTC import local2UTC

#%% ############### VARIAVEIS

# Caminho geral
tablePath = os.path.dirname(os.getcwd())

# Caminho das pastas
DataPath = tablePath + '/inputs'
OutPath = tablePath + '/outputs'
OutPathInter = tablePath + '/outputs_intermediarios'

# SHP limites territoriais IBGE
shp_uf = DataPath + '/BR_UF_2023/BR_UF_2023.shp'
shp_mun = DataPath + '/BR_Municipios_2022/BR_Municipios_2022.shp'

# Fonte dos dados setores censitários
#Fonte dos dados : https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/Agregados_por_Setores_Censitarios/malha_com_atributos/setores/csv/
setoresPath = DataPath + '/Setores'

# Fatores de desagregação
weekdis_sul_csv = DataPath + '/factorsDesagregation/desagDailySul.csv'
weekdis_norte_csv = DataPath + '/factorsDesagregation/desagDailyNorte.csv'
hourdis_csv = DataPath + '/factorsDesagregation/desagHourly.csv'

# Determinar referência de quantificação (UE ou AP42)
fonte = 'UE'

# Grade espacial (OPCIONAL)
meshPath = DataPath + '/mesh_12km.gpkg'

# Fuso horário
lc2utc_csv = DataPath + '/lc2utc.csv'

# Base complementar
woodcoal_csv = DataPath + '/BR_setores_CD2022.csv'
#%% ################### CARREGAMENTO

# SHP estados IBGE
BR_UF = gpd.read_file(shp_uf).to_crs("EPSG:4326")

# SHP municípios IBGE
BR_MUN = gpd.read_file(shp_mun).to_crs("EPSG:4326")
BR_MUN['CD_MUN'] = BR_MUN['CD_MUN'].astype(int)

# Fatores de desagregação diária e horária
weekdis_sul = pd.read_csv(weekdis_sul_csv, index_col='day')
weekdis_norte = pd.read_csv(weekdis_norte_csv, index_col='day')
hourdis = pd.read_csv(hourdis_csv, index_col='hour')

# Grade espacial
shp_cells = gpd.read_file(meshPath)
gridGerado = shp_cells.copy()
gridGerado = gridGerado.to_crs("EPSG:4674")

# Carregar fuso horário (Se ja rodado o local2UTC na etapa abaixo)
lc2utc = np.loadtxt(lc2utc_csv, delimiter=',')

# Base complementar
WoodCoalDf = pd.read_csv(woodcoal_csv)


#%% ################### DEFINIÇÃO DO GRID

#### Se necessário a geração do grid
# # Compatível EDGAR
# Tam_pixel = 0.1  # ~1 km
# minx = -74.1   # longitude mínima (oeste)
# maxx = -28.9   # longitude máxima (leste)
# miny = -33.8   # latitude mínima (sul)
# maxy = 5.4   # latitude máxima (norte)
# # minx, miny, maxx, maxy = BR_UF.total_bounds
# gridGerado, xx, yy = CreateGrid(Tam_pixel,minx,maxx,miny,maxy)
# yy = yy[::-1]

# Plot dpo Grid para verificação
# fig, ax = plt.subplots(figsize=(10, 10))
# gridGerado.boundary.plot(ax=ax, color='gray')
# BR_UF.boundary.plot(ax=ax, color='black')

# Criação das coordenadas
gridGerado['lon'] = gridGerado.geometry.centroid.x.round(6)
gridGerado['lat'] =  gridGerado.geometry.centroid.y.round(6)
gridGerado = gridGerado.drop_duplicates(subset=['lon', 'lat'])

# Criação dataframe com as coordenadas
xx, yy = np.meshgrid(np.sort(np.unique(gridGerado.lon)),
                       np.sort(np.unique(gridGerado.lat)))
yy = yy[::-1]

# Identifcando osestados dentro do grid
estados_intersectados = BR_UF[BR_UF.intersects(gridGerado.unary_union)]
ufs = list(estados_intersectados['SIGLA_UF'])

# Extrair fuso horário e salvar (Rodar apenas 1 vez)
# Necessário apenas se tiver abilitado a agregação do fuso em GridMat7D
# lc2utc, tag = local2UTC(xx, yy)

#%% ################### PROCESSAMENTO PARA LENHA E CARVÃO
 
#Calcular as emissões de lenha e carvão (ton)/2023
woodEmission, coalEmission, poluentesWoodCoal = emissionEstimateWoodCoal(
    WoodCoalDf,DataPath,OutPath, fonte)

# Numero de anos analisados (ano 1 referente a 2023)
anos = 1

# lc2utc = lc2utc.T

datasets = {}
# Criando loop para lenha e carvao
for Combustivel, dt in zip(['Lenha','Carvao'], [woodEmission, coalEmission ]):
    # uf='CE'
    # Combustivel = 'Carvao'
    # dt  = coalEmission
    # poluentes = poluentesWoodCoal
    # poluentes = ['CO']
    # Loop para ler cada UF separadamente
    for ii, uf in enumerate(ufs):
        
        #Criando matriz vazia
        if ii == 0:
            # Transformando em uma matriz x por y

            # gridMat5D = np.zeros((len(poluentesWoodCoal),54, 12, np.shape(np.unique(gridGerado.lat))[0],
            #                       np.shape(np.unique(gridGerado.lon))[0]
            #                       ))
            gridMat5D = np.zeros((len(poluentesWoodCoal),anos, 12, np.shape(np.unique(gridGerado.lat))[0],
                                  np.shape(np.unique(gridGerado.lon))[0]
                                  ))
            
        # Colocando emissões de cada estado na grade
        emiGrid = EmissionsPixelsWoodCoal(Combustivel, dt
                               , gridGerado, DataPath, OutPath,uf, BR_UF ,
                               poluentesWoodCoal, setoresPath)

        
        # transforma em matriz e soma as emissões de cada estado
        gridMat5D = GridMat5D(Combustivel, emiGrid, gridMat5D, poluentesWoodCoal, 
                              DataPath, uf, anos)
        
    #Fazendo a desagregação anual e mensal
    GridMat7D(weekdis_sul,weekdis_norte,hourdis,gridMat5D,poluentesWoodCoal,DataPath, Combustivel,
                   xx,yy , OutPath , lc2utc,fonte)
    
    # ds = temporalDisagg(gridMat7D, poluentesWoodCoal, Combustivel, xx, yy)
    # datasets[Combustivel] = ds

# emiCoal = datasets['Carvao'].copy()
# emiWood = datasets['Lenha'].copy()

#%% ################### PROCESSAMENTO PARA GLP

#Fonte dos dados: https://dados.gov.br/dados/conjuntos-dados/vendas-de-derivados-de-petroleo-e-biocombustiveis
glpDf = pd.read_csv(DataPath + '/vendas-anuais-de-glp-por-municipio_1.csv',encoding ='utf-8',  sep=';')

# Tratamento
glpDf.rename(columns={'CÓDIGO IBGE': 'CODIGO IBGE','MUNICÍPIO': 'MUNICIPIO'}, inplace=True)
glpDf = glpDf[glpDf['ANO'] >= 2000]
glpDf =  glpDf[glpDf['P13'] > 0]

# Emissoes propano e butano em ton
propEmiCid, butEmiCid, poluentesGLP = emissionEstimateGLP(DataPath, OutPath, glpDf, fonte)

datasetsglp = {}
for Combustivel, dt in zip(['Propano', 'Butano'], [propEmiCid, butEmiCid]):
    print(f"Processando {Combustivel}...")
    
    # Combustivel = 'Propano'
    # dt = propEmiCid
   
    # Adaptação para rodar apenas 2021,2022 e 2023
    anos = 1
    dt = dt[dt['ANO'] >= 2024 - anos]
    
    gridMat5Dglp = EmissionsPixelsGLP(dt, BR_MUN, 
                gridGerado, poluentesGLP, DataPath, Combustivel , ufs)


    
    # Filtrar para os anos 2021,2022,2023
    GridMat7D(weekdis_sul,weekdis_norte,hourdis
                          , gridMat5Dglp, poluentesGLP, DataPath, 
                     Combustivel, xx, yy, OutPath , lc2utc,fonte)
            
#%%
for combustivel in ['Lenha','Carvao','Butano','Propano']:
    
    pasta = os.path.join(OutPath, 'emissoes', combustivel, '2023', '2023_1.nc')
    ds = xr.open_dataset(pasta)
    ds_6dias = ds.sel(time=slice('2023-01-01','2023-01-06'))
    
    # salvar
    ds_6dias.to_netcdf(os.path.join('/home/marcos/Documents/LCQAR/emiResidenciais/outputs/emissoes_teste', 
                                    f"{combustivel}_2023_01_01_2023_01_06.nc"))
    













