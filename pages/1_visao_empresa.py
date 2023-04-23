#======================================================================================================================
# VISÃO - EMPRESA
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

# 1. Quantidade de pedidos por dia
def pedidos_por_dia(df):
    st.markdown('### Pedidos Por Dia')
    a = df.loc[:,['ID', 'Order_Date']].groupby(['Order_Date']).count().reset_index()
    a = a.sort_values('Order_Date')
    a.columns = ['Data de Entrega', 'Qtd. de Pedidos']
    # Gráfico
    fig = px.bar( a, x='Data de Entrega', y='Qtd. de Pedidos', category_orders={'Order_Date': df['Order_Date']} )
    fig.update_traces(marker_color='#9B0000')
    st.plotly_chart(fig, use_container_width=True)

# 2. Pedidos por tipo de tráfego
def pedidos_por_trafego(df):
    st.markdown('### Pedidos por Tráfego (%)')
    a = df.loc[:,['ID', 'Road_traffic_density']].groupby(['Road_traffic_density']).count().reset_index()
    a['perc_ID'] = 100 * ( a['ID'] / a['ID'].sum() )  
    # Gráfico
    fig = px.pie(a, values='ID', names='Road_traffic_density', labels={'ID':'Quantidade de Pedidos', 'Road_traffic_density':'Tipo de Tráfego'}, hover_data={'perc_ID': ':.2f'})
    fig.update_layout(width=700, height=500, legend=dict(font=dict(size=15), orientation='h',x=0.27))
    fig.update_traces(textposition='inside', textinfo='percent+label', textfont=dict(size=16))
    st.plotly_chart(fig, use_container_width=True)

# 3. Volume de pedidos por cidade e tipo de tráfego
def volume_de_pedidos(df):
    st.markdown('### Pedidos por Cidade e Tráfego')
    a = df.groupby(['City', 'Road_traffic_density'])['ID'].count().reset_index()
    a.columns = ['Cidade', 'Tráfego', 'ID']
    # Gráfico
    fig = px.bar(a, x='Cidade', y='ID', color='Tráfego', barmode='group')
    fig.update_layout(xaxis_title='Cidade', yaxis_title='Qtd. de Pedidos', width=700, height=500, legend=dict(title='', font=dict(size=15), orientation='h', x=0.25, y=1.10))
    st.plotly_chart(fig, use_container_width=True)

# 4. Pedidos por semana
def pedidos_semana(df):
    st.markdown('### Pedidos Por Semana')
    df['Week_of_Year'] = pd.to_datetime(df['Order_Date']).apply(lambda x: x.isocalendar()[1])
    df_aux = df.loc[:, ['ID', 'Week_of_Year']].groupby( 'Week_of_Year' ).count().reset_index()
    df_aux.columns = ['Semana do Ano', 'Número de Pedidos']
    # Gráfico
    fig = px.line( df_aux, x='Semana do Ano', y='Número de Pedidos')
    st.plotly_chart(fig, use_container_width=True)

# 5. Entregas por entregador
def entregas_por_entregador(df):   
    st.markdown('### Pedidos Por Entregador')
    a = df.loc[:,['ID', 'Week_of_Year']].groupby(['Week_of_Year']).count().reset_index()
    b = df.loc[:,['Delivery_person_ID', 'Week_of_Year']].groupby(['Week_of_Year']).nunique().reset_index()
    # Qtd. de pedidos por semana / Número único de entregadores por semana
    c = pd.merge(a, b, how='inner')
    c['order_by_deliver'] = c['ID'] / c['Delivery_person_ID']
    # Gráfico
    c.columns = ['Semana do Ano', 'Pedidos', 'Entregadores', 'Pedidos por Entregador']
    fig = px.line(c, x='Semana do Ano', y='Pedidos por Entregador')
    st.plotly_chart(fig, use_container_width=True)

# 6. Mapa de cidades
def mapa_cidades(df):
    st.markdown('### Mapa de Cidades')
    
    # 6. Agrupar os dados por 'City' e 'Road_traffic_density'
    data_plot = df.groupby(['City', 'Road_traffic_density'])

    # Criar o mapa
    map = folium.Map(zoom_start=11)

    # Iterar sobre os grupos
    for group_name, group_data in data_plot:
        # Obter a latitude e longitude média do grupo
        lat = group_data['Delivery_location_latitude'].mean()
        long = group_data['Delivery_location_longitude'].mean()

        # Adicionar um marcador para o grupo
        popup_text = f"City: {group_name[0]}, Road traffic density: {group_name[1]}"
        folium.Marker([lat, long], popup = popup_text).add_to(map)
    folium_static (map, width=1400 ,height=600)

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
st.markdown('### EMPRESA')

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tática', 'Visão Geográfica'])

with tab1:
    # 1. Quantidade de pedidos por dia
    with st.container():
        pedidos_por_dia(df)

    with st.container():
        st.markdown('---')
        col1, col2 = st.columns(2)

        # 2. Pedidos por tipo de tráfego
        with col1:
            pedidos_por_trafego(df)
            
        # 3. Volume de pedidos por cidade e tipo de tráfego
        with col2:
            volume_de_pedidos(df)

with tab2:
    # 4. Pedidos por semana
    with st.container():
        pedidos_semana(df)

    st.markdown('---')
    
    # 5. Entregas por entregador
    with st.container():
        entregas_por_entregador(df)

with tab3:
    # 6. Mapa de cidades
    mapa_cidades(df)
