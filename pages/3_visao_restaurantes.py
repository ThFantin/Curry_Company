#======================================================================================================================
# VISÃO - RESTAURANTES
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
import plotly.graph_objects as go
import numpy as np

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

# 1. A quantidade de entregadores únicos
def entregadores_unicos(df):
    a = len(df['Delivery_person_ID'].unique())
    col1.metric('Qtd. de Entregadores', a)

# 2. A distância média dos resturantes e dos locais de entrega
def distancia_media(df):
    df['distance'] = df.apply(lambda x: haversine((x['Restaurant_latitude'], x['Restaurant_longitude']), (x['Delivery_location_latitude'], x['Delivery_location_longitude'])), axis=1)
    a = df['distance'].mean().round(2)
    col2.metric('Distância Média (km)', a)

# 3. O tempo médio de entrega com e sem os Festivais
def tempo_medio_festival(df, considerar_festivais):
    if considerar_festivais:
        festivais = 'Yes'
        nome_metrica = 'Tempo Médio c/ Festivais (min)'
    else:
        festivais = 'No'
        nome_metrica = 'Tempo Médio s/ Festivais (min)'
        
    entrega = df[df['Festival'] == festivais]
    tempo_medio = entrega['Time_taken(min)'].mean().round(2)
    st.metric(nome_metrica, tempo_medio)

# 4. Tempo médio por cidade (min)
def tempo_medio_por_cidade(df):   
    st.markdown("### Tempo Médio Por Cidade")
    a = df.loc[:, ['City', 'Time_taken(min)']].groupby( 'City' ).agg( {'Time_taken(min)': ['mean', 'std']}).round(2)
    a.columns = ['Tempo Médio', 'Desvio Padrão']
    a = a.reset_index()
    # Gráfico
    fig = go.Figure() 
    fig.add_trace( go.Bar( name='Control', x=a['City'], y=a['Tempo Médio'], error_y=dict(type='data', array=a['Desvio Padrão'])))
    fig.update_traces(marker_color='#9B0000')
    fig.update_layout(barmode='group', xaxis_title='Cidade', yaxis_title='Tempo Médio (min)') 
    st.plotly_chart(fig)

# 5. Tempo Médio Por Tipo de Pedido e Cidade
def tempo_media_por_pedido_cidade(df):
    st.markdown("### Tempo Médio Por Tipo de Pedido e Cidade")
    a = (df.loc[:, ['City', 'Time_taken(min)', 'Type_of_order']].groupby( ['City', 'Type_of_order'] ).agg( {'Time_taken(min)': ['mean', 'std']})).round(2)
    a.columns = ['Tempo Médio', 'Desvio Padrão']
    a = a.reset_index()
    a = a.rename(columns={'City': 'Cidade', 'Type_of_order': 'Tipo de Pedido'})
    st.dataframe(a, height=457, width=500)

# 6. Tempo médio por cidade (%)
def tempo_medio_cidade_perc(df):
    cols = ['Delivery_location_latitude', 'Delivery_location_longitude', 'Restaurant_latitude', 'Restaurant_longitude']
    df['distance'] = df.loc[:, cols].apply( lambda x: haversine(  (x['Restaurant_latitude'], x['Restaurant_longitude']), (x['Delivery_location_latitude'], x['Delivery_location_longitude']) ), axis=1 )
    # Gráfico
    a = df.loc[:, ['City', 'distance']].groupby( 'City' ).mean().reset_index()
    fig = go.Figure( data=[ go.Pie( labels=a['City'], values=a['distance'], pull=[0.01, 0.01, 0.01])])
    fig.update_layout(title={'text': 'Tempo Médio Por Cidade', 'y':0.95,'x':0.48, 'xanchor': 'center', 'yanchor': 'top'}, width=700, height=500, legend=dict(font=dict(size=15), orientation='h',x=0.25))
    fig.update_traces(textinfo='percent', textfont=dict(size=18), hovertemplate='%{label}<br>%{value:.2f} km<br>%{percent}')
    st.plotly_chart(fig)

# 7. Desvio Padrão Por Cidade e Tráfego
def std_cidade_trafego(df):
    a = df.loc[:, ['City', 'Time_taken(min)', 'Road_traffic_density']].groupby(['City', 'Road_traffic_density']).agg({'Time_taken(min)': ['mean', 'std']})
    a.columns = ['Tempo Médio', 'Desvio Padrão']
    a = a.reset_index()
    # Gráfico
    fig = px.sunburst(a, path=['City', 'Road_traffic_density'], values='Tempo Médio', color='Desvio Padrão', color_continuous_scale='RdBu', color_continuous_midpoint=np.average(a['Desvio Padrão']))
    fig.update_layout(title={'text': 'Desvio Padrão Por Cidade e Tráfego', 'y':0.95,'x':0.4, 'xanchor': 'center', 'yanchor': 'top'}, width=700, height=500)
    st.plotly_chart(fig)

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
    col1, col2, col3, col4 = st.columns(4, gap='small')

    # 1. A quantidade de entregadores únicos
    with col1:
        entregadores_unicos(df)

    # 2. A distância média dos resturantes e dos locais de entrega
    with col2:
        distancia_media(df)

    # 3. O tempo médio de entrega durantes os Festivais
    with col3:
        tempo_medio_festival(df, True)

    # 4. O tempo médio de entrega sem Festivais
    with col4:
        tempo_medio_festival(df, False)

st.markdown("---")

with st.container():
    col1, _, col2 = st.columns([1, 0.5, 1, ], gap='small')      # Adicionando espaçamento no eixo x entre o gráfico # 5 e a tabela # 6
    col1.width = 100
    col2.width = 100
    
    # 5. Tempo médio por cidade (min)
    with col1:
        tempo_medio_por_cidade(df)

    # 6. Tempo Médio Por Tipo de Pedido e Cidade
    with col2:
        tempo_media_por_pedido_cidade(df)
 
st.markdown('---')
with st.container():
    st.markdown('### Distribuição do Tempo')
    col1, col2 = st.columns(2)
    
    # 7. Tempo médio por cidade (%)
    with col1:
        tempo_medio_cidade_perc(df)
     
    # 8. Desvio Padrão Por Cidade e Tráfego
    with col2:
        std_cidade_trafego(df)
