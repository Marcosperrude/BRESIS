# -*- coding: utf-8 -*-
"""
Created on Thu Mar  6 11:00:27 2025

@author: marcos perrude
"""

import pandas as pd

def emissionEstimateGLP(DataPath, OutPath, glpDf, fonte):
    
    
    # Somar as colunas p12 e outros
    glpDf['TOTAL (Kg)'] = glpDf['P13'] + glpDf['OUTROS']
    
    # Converter para m³
    # Densidade 552 kg/m³ (tabela 17 - https://static.portaldaindustria.com.br/media/filer_public/ee/78/ee78f794-84fc-4b8b-8aec-5ce5be3c74f0/estudo_especificacao_do_gas_natural_new.pdf)
    glpDf['TOTAL (m³)'] = glpDf['TOTAL (Kg)']/(552)
    
        
    # -----------------------------------------------------------------------------------
    ############ Quantificação de acordo com a AP42
    
    
    # #https://www.epa.gov/sites/default/files/2020-09/documents/1.5_liquefied_petroleum_gas_combustion.pdf
    # emiFac  = pd.read_csv(DataPath + '/fatorEmissao_Prop_But.csv' , index_col=[0])
    
    if fonte == 'AP42':
        emiFac  = pd.read_csv(DataPath + '/fatorEmissao_Prop_But.csv' , index_col=[0])
    
        # # Para Enxofre
        # # Teor max de enxofre no glp em mg S/kg de acordo com https://www.sindigas.org.br/Download/PUBLICACOES_SINDIGAS/glp-energetico-de-transicao-estudo-fernando-corner.pdf?utm_source=chatgpt.com
        # # COnverter a concentração de enxofre de mg/kg para gr/ft³
        MAxGLPN = (140 * 2.3)/(1000*0.353147*0.0647989)
    
        emiFac['SO2'] =  emiFac['SO2']*MAxGLPN
        # #Conversao lb/10³gal --> Kg/m³ -->Ton/m³
        emiFac  = (emiFac * 0.12)/1000
        poluentesGLP = emiFac.columns
    
    # -----------------------------------------------------------------------------------
    ############ Quantificação de acordo com a UE


    # Fator de eissao da UE : https://www.eea.europa.eu/en/analysis/publications/emep-eea-guidebook-2023
    # Tier 1 - NFR source category 1.A.4.b.i Residential plant - Solid biomass e Gaseous fuels
    # Unidade : Kg/Gj
    if fonte == 'UE':
        emissionFactor_UE = pd.read_csv(DataPath + '/fatores_emissao_residenciais_UE.csv')
        
        # Unidade conversão lenha  e Carvão vegetal
        # ton - Gj : https://www.mme.gov.br/SIEBRASIL/App_Content_User/archivos-publicos/nz3ggqk0.mrp20180831000000.pdf?or=30148&ss=1&v=1
        Unid_Conversao_glp = 25.58 
        poluentesGLP = ['PM10' ,'PM2.5','NMVOC','CO','SOx','NOx']
    
    #-----------------------------------------------------------------------------------
    # Processamento
    
    
    ############# AP42
    if fonte == 'AP42':
        emiCidDict = {}
        # Loop pelos combustíveis disponíveis em emiFac (assume que o índice são os nomes)
        for nome in emiFac.index:
            # nome= 'Propano'
            emiCid = glpDf[['CODIGO IBGE', 'ANO', 'UF', 'MUNICIPIO']].copy()
        
            for pol in emiFac.columns:
                # pol = 'PM'
                emiCid[pol] = emiFac.loc[nome, pol] * (glpDf['TOTAL (m³)'] / 2)
        
            emiCidDict[nome] = emiCid.copy()  # Armazena o resultado com a chave do nome do combustível
    
    ############# UE
    if fonte == 'UE':
        # Selecionar os poluente que devem ser analisados
        # Emissões em toneladas de poluentes de acordo com a UE
        emiCidDict = {}
        for nome in ['Propano','Butano']:
            # nome= 'Propano'
            emiCid = glpDf[['CODIGO IBGE', 'ANO', 'UF', 'MUNICIPIO']].copy()
        
            for pol in poluentesGLP:
                # pol = 'PM10'
                emiCid[pol] = (((glpDf['TOTAL (m³)']/2)* Unid_Conversao_glp) * (emissionFactor_UE.loc[
                    emissionFactor_UE['Poluente'] == pol, 'Gas'].values[0]/1000))

            emiCidDict[nome] = emiCid.copy()  # Armazena o resultado com a chave do nome do combustível
    
    
    # Acessando os resultados
    propEmiCid = emiCidDict['Propano']
    butEmiCid  = emiCidDict['Butano']
    
    return propEmiCid, butEmiCid, poluentesGLP