import streamlit as st
from PIL import Image

# 1. Configurando página
st.set_page_config(page_title='Home', layout="wide")

# 2. Adicionando logomarca
imagem = Image.open('logo.png')
st.sidebar.image(imagem, width=250)

# 3. Adicionando autor
st.sidebar.markdown('#### Created by Thiago Fantin')

st.write('# Curry Company Dashboard')

st.markdown(
    """
    ##### Dashboard contruído para acompanhar as métricas de crescimento dos entregadores e restaurantes.
    ### Como utilizar o Dashboard?
    - Visão Empresa:
        - Visão Gerencial: Métricas gerais de crescimento.
        - Visão Tática: Indicadores semanais de crescimento.
        - Visão Geográfica: Insights de geolocalização.

    - Visão Entregadores:
        - Acompanhamento dos indicadores semanais de crescimento.
    
    - Visão Restaurantes:
        - Indicadores semanais de crescimento dos restaurantes.

    ### Ask for Help
    - @ThFantin
    """)
