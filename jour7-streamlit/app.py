import streamlit as st

st.set_page_config(page_title="Jour 7", page_icon="🚀")
st.title("🚀 Mon premier Streamlit")

nom = st.text_input("Ton prénom ?")
if nom:
    st.write(f"Salut **{nom}** ! Bienvenue dans le bootcamp.")

# Sidebar
st.sidebar.header("Options")
niveau = st.sidebar.selectbox("Niveau", ["Débutant", "Intermédiaire", "Avancé"])
st.sidebar.write(f"Niveau sélectionné : {niveau}")