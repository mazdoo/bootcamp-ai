import streamlit as st
import anthropic
import chromadb
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="RAG Chat", page_icon="📄", layout="wide")
st.title("📄 Chat avec ton document")

client = anthropic.Anthropic()

# ---- SIDEBAR : Upload + Indexation ----
st.sidebar.header("📁 Document")
uploaded_file = st.sidebar.file_uploader("Upload un .txt", type=["txt"])

if uploaded_file and "vectorstore_ready" not in st.session_state:
    with st.sidebar:
        with st.spinner("Indexation en cours..."):
            text = uploaded_file.read().decode("utf-8")

            chunk_size = 500
            overlap = 50
            chunks = []
            for i in range(0, len(text), chunk_size - overlap):
                chunk = text[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk)

            chroma_client = chromadb.Client()
            collection = chroma_client.create_collection(
                name="document",
                metadata={"hnsw:space": "cosine"}
            )

            collection.add(
                documents=chunks,
                ids=[f"chunk_{i}" for i in range(len(chunks))]
            )

            st.session_state.collection = collection
            st.session_state.vectorstore_ready = True
            st.session_state.num_chunks = len(chunks)

        st.success(f"✅ {st.session_state.num_chunks} chunks indexés !")

# ---- ZONE PRINCIPALE : Chat ----
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Pose ta question sur le document..."):
    if not st.session_state.get("vectorstore_ready"):
        st.warning("⬅️ Upload un document d'abord !")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Recherche + génération..."):
                results = st.session_state.collection.query(
                    query_texts=[prompt],
                    n_results=3
                )
                context = "\n\n---\n\n".join(results["documents"][0])

                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=f"""Tu es un assistant qui répond aux questions 
en te basant UNIQUEMENT sur le contexte fourni.
Si l'info n'est pas dans le contexte, dis-le.

CONTEXTE :
{context}""",
                    messages=[{"role": "user", "content": prompt}]
                )
                reply = response.content[0].text
                st.write(reply)

                with st.expander("📎 Sources utilisées"):
                    for i, doc in enumerate(results["documents"][0]):
                        st.caption(f"Chunk {i+1}")
                        st.text(doc[:200] + "...")

        st.session_state.messages.append({"role": "assistant", "content": reply})