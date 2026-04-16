# -*- coding: utf-8 -*-
"""
Created on Mon Apr 14 10:56:08 2025

Este script sera utilizado para o tratamento dos dados e quantifcação das emissoes atmosféricas de Fontes Residenciais,
do qual sera utilizado para integrar o inventário nacional de fontes fixas.


@author: Marcos.Perrude
"""

import pandas as pd
def emissionEstimateWoodCoal(WoodCoalDf,DataPath,OutPath, fonte):
    # fonte = 'UE'
    ############# Fatores de emissões e classifIcações
    
    # Classificação de acordo com o tipo do setor censitário
    classificacao = pd.read_csv(DataPath + '/classificacaoSetores/setor_classificacao.csv' , index_col='Codigo')
    
    # Fator nacional de residencias que utilizam  de acordo com o tipo de combustível e classificação do setor censitário
    fatores = pd.read_csv(DataPath + '/fatorConsumoNac_LenhaCarvao.csv', index_col = 'Categoria')
    fatores_pnad = pd.read_csv(DataPath + '/fatorConsumoReg_LenhaCarvao.csv', encoding = 'latin1')

    #Consumo de lenha (ton/dia) por regiao de acordo com https://www.epe.gov.br/sites-pt/publicacoes-dados-abertos/publicacoes/PublicacoesArquivos/publicacao-578/Nota%20T%C3%A9cnica%20Consumo%20de%20lenhaCV%20-%20Residencial%20final%202021.pdf
    consumo_regional = pd.read_csv(DataPath + '/consumoLenCarRegiao.csv')


    fator_consumo = pd.read_csv(DataPath + '/fator_consumo.csv', encoding = 'latin1')
    fator_consumo = fator_consumo.set_index('Regiao')
    # -----------------------------------------------------------------------------------
    ############ Quantificação de acordo com a AP42
    
    # # Fator de Emissao Fonte: https://www.epa.gov/sites/default/files/2020-09/documents/1.10_residential_wood_stoves.pdf
    # # lb/ton
    if fonte == 'AP42':
        emissionFactor = pd.read_csv(DataPath + '/fatores_emissao_residencial.csv')

    
    # -----------------------------------------------------------------------------------
    ############ Quantificação de acordo com a UE
    
    
    # Fator de eissao da UE : https://www.eea.europa.eu/en/analysis/publications/emep-eea-guidebook-2023
    # Tier 1 - NFR source category 1.A.4.b.i Residential plant - Solid biomass e Gaseous fuels
    # Unidade : Kg/Gj
    if fonte == 'UE':
        emissionFactor_UE = pd.read_csv(DataPath + '/fatores_emissao_residenciais_UE.csv')
    
        # Unidade conversão lenha  e Carvão vegetal
        # ton - Gj : https://www.mme.gov.br/SIEBRASIL/App_Content_User/archivos-publicos/nz3ggqk0.mrp20180831000000.pdf?or=30148&ss=1&v=1
        Unid_Conversao_lenha = 12.93
        Unid_Conversao_carvao = 27.05 
        poluentesWoodCoal = ['PM10' ,'PM2.5','NMVOC','CO','SOx','NOx'] 
    
    
    #-----------------------------------------------------------------------------------
    # Processamento
    
    # Verficar se cabe o uso
    # uso_lenha_agrupado = pd.read_csv(DataPath + '/uso_lenha_agrupado.csv', index_col = 0)

    # Remove massas de água
    WoodCoalDf = WoodCoalDf[(WoodCoalDf["CD_SIT"] != 9) & (WoodCoalDf['v0002'] != 0)]  
    

    #Classificando os setores
    WoodCoalDf["Classificacao"] = WoodCoalDf["CD_SIT"].map(classificacao['Descricao'])

    # # Mapear a quantidade de residencias que utilizam lenha (%)
    # WoodCoalDf["Fator_Lenha"] = WoodCoalDf["Classificacao"].map(fatores_pnad["Lenha"].to_dict())
    WoodCoalDf = WoodCoalDf.merge(
        fatores_pnad[["NM_UF", "Classificacao", "Fator"]],
        on=["NM_UF", "Classificacao"],
        how="left"
    )
    WoodCoalDf["Fator"] = WoodCoalDf["Fator"].fillna(
        WoodCoalDf["Classificacao"].map(fatores.loc["Lenha"].to_dict())
        )
    
    # Quantidade de residenciais que utilizam lenha/carvão

    WoodCoalDf["Residencias_Ajustadas"] = WoodCoalDf["v0007"] * WoodCoalDf["Fator"]

    WoodCoalDf["Resid_lenha"] = (
    WoodCoalDf["Residencias_Ajustadas"].values *
    fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Lenha"].values) + (
    WoodCoalDf["Residencias_Ajustadas"].values *
    fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Lenha e Carvao"].values * (
        fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Lenha"].values / (
            fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Lenha"].values +
            fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Carvao"].values)))
            
    WoodCoalDf["Resid_carvao"] = (WoodCoalDf["Residencias_Ajustadas"].values *
    fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Carvao"].values) + (
    WoodCoalDf["Residencias_Ajustadas"].values * fator_consumo.loc[
        WoodCoalDf["NM_REGIAO"], "Lenha e Carvao"].values * (
        fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Carvao"].values / (
            fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Lenha"].values +
            fator_consumo.loc[WoodCoalDf["NM_REGIAO"], "Carvao"].values)))     
    
             
    #Calculo do consumo anual de lenha e carvao de acordo com a quantidade de residenciais em ton
    WoodCoalDf['Consumo_lenha[ton/ano]'] = WoodCoalDf['Resid_lenha'] * WoodCoalDf['NM_REGIAO'].map(
        consumo_regional.set_index('Regiao')['Lenha']) * 365
    WoodCoalDf['Consumo_Carvao[ton/ano]'] = WoodCoalDf['Resid_carvao'] * WoodCoalDf['NM_REGIAO'].map(
        consumo_regional.set_index('Regiao')['Carvao']) * 365
    

    woodEmission = pd.DataFrame({'CD_SETOR': WoodCoalDf['CD_SETOR'].astype(str),
                                   'CD_UF' : WoodCoalDf['CD_UF']
                                   })
    
    coalEmission = pd.DataFrame({'CD_SETOR': WoodCoalDf['CD_SETOR'].astype(str),
                                    'CD_UF' : WoodCoalDf['CD_UF']
                                    })
    
    
    ############# AP42
    if fonte == 'AP42':
        # emissões em toneladas de poluentes de acordo com a
        # Fator de conversão (0.5) de lb/ton --> kg/ton --> ton/ton
        for i, pol in enumerate(emissionFactor['Poluentes']):
             woodEmission[pol] = ((WoodCoalDf['Consumo_lenha[ton/ano]'] * emissionFactor['Lenha'][i] * 0.5) / 1000)
             coalEmission[pol] = ((WoodCoalDf['Consumo_Carvao[ton/ano]'] * emissionFactor['Lenha'][i] * 0.5) / 1000)
        
        # Nome dos poluentes
        poluentesWoodCoal = emissionFactor['Poluentes']
    
    
    ############# UE
    if fonte == 'UE':
        # Selecionar os poluente que devem ser analisados
        # emissões em toneladas de poluentes de acordo com a UE
        for i, pol in enumerate(poluentesWoodCoal):
             woodEmission[pol] = ((WoodCoalDf['Consumo_lenha[ton/ano]']* Unid_Conversao_lenha) * (emissionFactor_UE.loc[
                 emissionFactor_UE['Poluente'] == pol, 'Biomassa'].values[0]/1000))
             
             coalEmission[pol] = ((WoodCoalDf['Consumo_Carvao[ton/ano]']*Unid_Conversao_carvao) * (emissionFactor_UE.loc[
                 emissionFactor_UE['Poluente'] == pol, 'Biomassa'].values[0]/1000))
    
 
    return woodEmission, coalEmission, poluentesWoodCoal

