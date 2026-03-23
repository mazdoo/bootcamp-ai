from sentence_transformers import SentenceTransformer
import chromadb
import anthropic
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="C:/Users/kilia/Desktop/Bootcamp IA/Jour 5/.env")
llm = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Étape 1 — Charger le modèle d'embeddings
print("Chargement du modèle...")
modele = SentenceTransformer("all-MiniLM-L6-v2")
print("Modèle prêt !\n")

# Étape 2 — Nos documents
documents = [
    "Le projet Azure OpenAI pour SCC a un budget de 50 000 euros.",
    "La livraison du projet est prévue pour le 15 juin 2026.",
    "L'équipe est composée de Marie Dupont et Jean Martin.",
    "Le client principal est la Société Générale.",
    "La migration vers Azure OpenAI commencera en avril 2026.",
]

# Étape 3 — Transformer en vecteurs
print("Création des embeddings...")
vecteurs = modele.encode(documents)
print(f"Chaque document = vecteur de {len(vecteurs[0])} dimensions\n")

# Étape 4 — Stocker dans ChromaDB
client = chromadb.Client()
collection = client.create_collection("documents_scc")
collection.add(
    documents=documents,
    embeddings=vecteurs.tolist(),
    ids=[f"doc_{i}" for i in range(len(documents))]
)
print(f"{len(documents)} documents stockés dans ChromaDB\n")

# Étape 5 — Recherche sémantique simple
question = "Quel est le budget du projet ?"
print(f"Question : {question}")
vecteur_question = modele.encode([question])
resultats = collection.query(
    query_embeddings=vecteur_question.tolist(),
    n_results=2
)
print("\nPassages les plus pertinents trouvés :")
for doc in resultats["documents"][0]:
    print(f"  → {doc}")

# Étape 6 — RAG complet avec Claude
def rag(question):
    vecteur_q = modele.encode([question])
    resultats = collection.query(
        query_embeddings=vecteur_q.tolist(),
        n_results=2
    )
    contexte = "\n".join(resultats["documents"][0])

    reponse = llm.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        system=f"""Tu es un assistant.
Réponds uniquement en te basant sur ce contexte :
{contexte}
Si la réponse n'est pas dans le contexte, dis-le clairement.""",
        messages=[{"role": "user", "content": question}]
    )
    return reponse.content[0].text

print("\n--- RAG COMPLET ---")
print(rag("Quel est le budget du projet ?"))
print(rag("Qui sont les membres de l'équipe ?"))
print(rag("Quelle est la capitale de l'Australie ?"))