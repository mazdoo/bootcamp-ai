from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import anthropic
import os
import json

load_dotenv(dotenv_path="C:/Users/kilia/Desktop/Bootcamp IA/Jour 6/.env")

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Étape 1 — Charger le document
print("Chargement du document...")
loader = TextLoader(
    "C:/Users/kilia/Desktop/Bootcamp IA/Jour 6/document.txt",
    encoding="utf-8"
)
pages = loader.load()
print(f"Document chargé !\n")

# Étape 2 — Découper en chunks
print("Découpage en chunks...")
splitter = CharacterTextSplitter(chunk_size=200, chunk_overlap=20)
chunks = splitter.split_documents(pages)
print(f"{len(chunks)} chunks créés\n")

# Étape 3 — Créer les embeddings avec Anthropic
print("Création des embeddings...")
def get_embedding(text):
    response = client.beta.messages.count_tokens(
        model="claude-haiku-4-5",
        messages=[{"role": "user", "content": text}]
    )
    # Utiliser un embedding simple basé sur les mots
    words = text.lower().split()
    return words

# Recherche simple par mots-clés
def chercher(question, chunks, n=3):
    mots_question = set(question.lower().split())
    scores = []
    for chunk in chunks:
        mots_chunk = set(chunk.page_content.lower().split())
        score = len(mots_question & mots_chunk)
        scores.append((score, chunk.page_content))
    scores.sort(reverse=True)
    return [s[1] for s in scores[:n]]

print("Prêt !\n")

# Étape 4 — LLM
llm = ChatAnthropic(
    model="claude-haiku-4-5",
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

def rag(question):
    passages = chercher(question, chunks)
    contexte = "\n\n".join(passages)

    prompt = f"""Tu es un assistant. Réponds uniquement en te basant sur ce contexte :
{contexte}

Si la réponse n'est pas dans le contexte, dis-le clairement.

Question : {question}"""

    reponse = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return reponse.content[0].text

# Étape 5 — Questions
print("--- RAG LANGCHAIN ---\n")
questions = [
    "Qu'est-ce que SCC ?",
    "Quel est le chiffre d'affaires de SCC ?",
    "Quels services propose SCC ?",
]

for question in questions:
    print(f"Q: {question}")
    reponse = rag(question)
    print(f"R: {reponse}\n")