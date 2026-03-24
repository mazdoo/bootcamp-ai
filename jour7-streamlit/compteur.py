import streamlit as st

st.title("🔢 Compteur persistant")

if "count" not in st.session_state:
    st.session_state.count = 0

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("➕"):
        st.session_state.count += 1
with col2:
    if st.button("➖"):
        st.session_state.count -= 1
with col3:
    if st.button("🔄 Reset"):
        st.session_state.count = 0

st.metric("Total", st.session_state.count)