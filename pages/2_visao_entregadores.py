#======================================================================================================================
# VISÃO - ENTREGADORES
#======================================================================================================================

#======================================================================================================================
# Bibliotecas Necessárias
#======================================================================================================================

import pandas as pd
import re
import plotly.express as px
from haversine import haversine
import folium
from PIL import Image
import streamlit as st
from streamlit_folium import folium_static
import datetime

#======================================================================================================================
# Importando Dataframe
#======================================================================================================================

df1 = pd.read_csv(r'dataset/train.csv')
df = df1.copy()     # Cópia do Dataframe

#======================================================================================================================
# Funções de Limpeza do Dataframe
#======================================================================================================================

def clean_code(df):

    df = df.astype(str)                                                              # Transformando Dataframe em String
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)               # Remover espaço de todo Dataframe

    # Excluindo as palavras 'conditions ' e '(min)  '.
    df['Weatherconditions'] = df['Weatherconditions'].str.replace('conditions ', '')
    df['Time_taken(min)'] = df['Time_taken(min)'].apply(lambda x: x.replace('(min) ', '') if isinstance(x, str) and '(min) ' in x else x)

    # Excluindo linhas que tenham 'NaN'
    df = df.loc[(df['Delivery_person_Age'] != 'NaN'), :]
    df = df.loc[(df['multiple_deliveries'] != 'NaN'), :]
    df = df.loc[(df['Road_traffic_density'] != 'NaN'), :]
    df = df.loc[(df['City'] != 'NaN'), :]
    df = df.loc[(df['Festival'] != 'NaN'), :]

    # Convertendo colunas para int
    df['Delivery_person_Age'] = df['Delivery_person_Age'].astype( int )
    df['Vehicle_condition'] = df['Vehicle_condition'].astype( int )
    df['multiple_deliveries'] = df['multiple_deliveries'].astype( int )
    df['Time_taken(min)'] = df['Time_taken(min)'].astype( int )

    # Convertendo colunas para float
    df['Delivery_person_Ratings'] = df['Delivery_person_Ratings'].astype( float )
    df['Restaurant_latitude'] = df['Restaurant_latitude'].astype( float )
    df['Restaurant_longitude'] = df['Restaurant_longitude'].astype( float )
    df['Delivery_location_latitude'] = df['Delivery_location_latitude'].astype( float )
    df['Delivery_location_longitude'] = df['Delivery_location_longitude'].astype( float )

    # Conversão de texto para data
    df['Order_Date'] = pd.to_datetime( df['Order_Date'], format='%d-%m-%Y' )

    return (df)

#======================================================================================================================
# Limpeza do Dataframe
#======================================================================================================================

df = clean_code(df)

#======================================================================================================================
# Funções de Análise de Dados
#======================================================================================================================

# 1. Maior Idade 
def idade (df):
    maior_idade = df.loc[:, 'Delivery_person_Age'].max()
    menor_idade = df.loc[:, 'Delivery_person_Age'].min()
    col1.metric('Maior Idade', maior_idade)
    col2.metric('Menor Idade', menor_idade)

# 2. Melhor e Pior condição de veículo
def condicao_veiculo (df):
    melhor_condicao = df.loc[:, 'Vehicle_condition'].max()
    pior_condicao = df.loc[:, 'Vehicle_condition'].min()
    col3.metric('Melhor Condição de Veículo', melhor_condicao)
    col4.metric('Pior Condição de Veículo', pior_condicao)

# 3. A avaliação média por entregador
def avaliacao_media_entregador(df, col1):
    col1.markdown('##### Avaliações Médias Por Entregador')
    a = df.loc[:, ['Delivery_person_ID', 'Delivery_person_Ratings']].groupby(['Delivery_person_ID']).mean().reset_index()
    a = a.rename(columns={'Delivery_person_ID': 'ID Entregador', 'Delivery_person_Ratings': 'Avaliação Média'})
    a['Avaliação Média'] = a['Avaliação Média'].round(2)
    col1.dataframe(a, height=500, width=400)

# 4. A avaliação média e o desvio padrão por tipo de tráfego ou condições climáticas
def avaliacao_media_e_std(df, categoria):
    if categoria == 'tráfego':
        st.markdown('##### Avaliações Médias Por Trânsito')
        a = df.loc[:,['Delivery_person_Ratings', 'Road_traffic_density']].groupby('Road_traffic_density').agg({'Delivery_person_Ratings':['mean', 'std']})
        a.columns = ['Avaliação Média', 'Desvio Padrão']
        a = a.reset_index()
        a = a.rename(columns={'Road_traffic_density': 'Trânsito'})
        a['Avaliação Média'] = a['Avaliação Média'].round(2)
        st.dataframe(a, width=400)
    elif categoria == 'clima':
        st.markdown('##### Avaliações Médias Por Clima')
        a = df.loc[:,['Delivery_person_Ratings', 'Weatherconditions']].groupby('Weatherconditions').agg({'Delivery_person_Ratings':['mean', 'std']})
        a.columns = ['Avaliação Média', 'Desvio Padrão']
        a = a.reset_index()
        a = a.rename(columns={'Weatherconditions': 'Clima'})
        a['Avaliação Média'] = a['Avaliação Média'].round(2)
        st.dataframe(a, width=400)

# 5. Os 10 entregadores mais rápidos e mais lentos por cidade
def top_entregadores(df, tipo):
    if tipo == 'rapidos':
        st.markdown('##### Top Entregadores Mais Rápidos')
        col = 'min'
    else:
        st.markdown('##### Top Entregadores Mais Lentos')
        col = 'max'
    a = df.groupby(['City', 'Delivery_person_ID'])['Time_taken(min)'].agg(col).reset_index() \
            .groupby('City').apply(lambda x: x.nsmallest(10, 'Time_taken(min)')).reset_index(drop=True)
    a = a.rename(columns={'City': 'Cidade', 'Delivery_person_ID': 'ID Entregador', 'Time_taken(min)': 'Tempo (min)'})
    st.dataframe(a, height=500, width=500)

#======================================================================================================================
# Barra Lateral Streamlit
#======================================================================================================================

# 1. Criando e configurando a página
st.set_page_config(layout="wide")

# 2. Adicionando logomarca
imagem = Image.open('logo.png')
st.sidebar.image(imagem, width=250)
st.sidebar.markdown("""---""")

# 3. Adicionando filtro de datas
datas = st.sidebar.slider( 
        'Até qual valor?',
        value=pd.datetime( 2022, 4, 6 ),
        min_value=pd.datetime(2022, 2, 11 ),
        max_value=pd.datetime( 2022, 4, 6 ),
        format='DD-MM-YYYY' )
# Filtro de data
linhas_selecionadas = df['Order_Date'] <  datas 
df = df.loc[linhas_selecionadas, :]

st.sidebar.markdown( """---""" )

# 4. Adicionando filtro de tráfego
trafego = st.sidebar.multiselect('Condições de Trânsito', ['Low', 'Medium', 'High', 'Jam'], default=['Low', 'Medium', 'High', 'Jam'])
# Filtro de trânsito
linhas_selecionadas = df['Road_traffic_density'].isin( trafego )
df = df.loc[linhas_selecionadas, :]

# 5. Adicionando autor
st.sidebar.markdown('#### Created by Thiago Fantin')

#======================================================================================================================
# Layout Streamlit
#======================================================================================================================
st.markdown('### ENTREGADORES')
st.markdown("---")
st.markdown('### Métricas')
with st.container():
    col1, col2, col3, col4 = st.columns(4, gap='large')
    
    # 1. Maior e Menor Idade
    with col1, col2:
        idade(df)
        
    # 2. Melhor e Pior condição de veículo
    with col3, col4:
        condicao_veiculo(df)
    
st.markdown("---")
st.markdown("### Avaliações")

with st.container():
    col1, col2 = st.columns(2)

    # 3. A avaliação média por entregador
    with col1:
        avaliacao_media_entregador(df, col1)

    # 4. A avaliação média e o desvio padrão por tipo de tráfego
    with col2:
        avaliacao_media_e_std(df, 'tráfego')

        # 5. A avaliação média e o desvio padrão por condições climáticas
        with st.container():
           avaliacao_media_e_std(df, 'clima')

st.markdown('---')
st.markdown("### Velocidade de Entrega")

with st.container():
    col1, col2 = st.columns(2)

    # 6. Os 10 entregadores mais rápidos por cidade
    with col1:
        top_entregadores(df, 'rapidos')

    # 7. Os 10 entregadores mais lentos por cidade     
    with col2:
        top_entregadores(df, 'lentos') 
