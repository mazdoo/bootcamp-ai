import json
import os

# --------------------------------------------------
# 1. LIRE UN FICHIER TXT
# --------------------------------------------------
def lire_fichier_txt(nom_fichier):
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    chemin_complet = os.path.join(dossier_script, nom_fichier)

    with open(chemin_complet, "r", encoding="utf-8") as fichier:
        contenu = fichier.read()
    return contenu


# --------------------------------------------------
# 2. LIRE UN FICHIER JSON
# --------------------------------------------------
def lire_fichier_json(nom_fichier):
    dossier_script = os.path.dirname(os.path.abspath(__file__))
    chemin_complet = os.path.join(dossier_script, nom_fichier)

    with open(chemin_complet, "r", encoding="utf-8") as fichier:
        donnees = json.load(fichier)
    return donnees


# --------------------------------------------------
# 3. NETTOYER LE TEXTE
# --------------------------------------------------
def nettoyer_texte(texte):
    texte = texte.lower()

    ponctuation = ".,;:!?()[]{}\"'_-"

    for caractere in ponctuation:
        texte = texte.replace(caractere, " ")

    mots = texte.split()
    return mots


# --------------------------------------------------
# 4. COMPTER LES MOTS AVEC UN DICT
# --------------------------------------------------
def compter_frequence(mots):
    frequences = {}

    for mot in mots:
        if mot in frequences:
            frequences[mot] += 1
        else:
            frequences[mot] = 1

    return frequences


# --------------------------------------------------
# 5. TROUVER LES 10 MOTS LES PLUS FREQUENTS
# --------------------------------------------------
def top_10_mots(frequences):
    liste_frequences = list(frequences.items())
    liste_frequences.sort(key=lambda element: element[1], reverse=True)
    return liste_frequences[:10]


# --------------------------------------------------
# 6. AFFICHER LE RESULTAT
# --------------------------------------------------
def afficher_top_10(top10):
    print("\n--- TOP 10 DES MOTS LES PLUS FREQUENTS ---")

    for index, (mot, nombre) in enumerate(top10, start=1):
        print(f"{index}. {mot} -> {nombre}")


# --------------------------------------------------
# 7. EXEMPLE DE TUPLE
# --------------------------------------------------
def exemple_tuple():
    informations = ("analyse", "terminée", 10)
    return informations


# --------------------------------------------------
# 8. EXEMPLE DE WHILE
# --------------------------------------------------
def demander_fichier():
    nom_fichier = ""

    while nom_fichier == "":
        nom_fichier = input("Entre le nom du fichier txt à lire : ").strip()

        if nom_fichier == "":
            print("Tu dois entrer un nom de fichier.")

    return nom_fichier


# --------------------------------------------------
# 9. PROGRAMME PRINCIPAL
# --------------------------------------------------
def main():
    print("Programme d'analyse de texte")
    print("Ce script lit un fichier .txt et affiche les 10 mots les plus fréquents.")

    # WHILE : on demande le nom du fichier tant qu'il est vide
    nom_fichier_txt = demander_fichier()

    # Lecture du TXT
    try:
        texte = lire_fichier_txt(nom_fichier_txt)
    except FileNotFoundError:
        print(f"\nErreur : le fichier '{nom_fichier_txt}' est introuvable.")
        print("Vérifie qu'il est dans le même dossier que ton script.")
        return

    # Nettoyage
    mots = nettoyer_texte(texte)

    # LIST : mots est une liste
    print(f"\nNombre total de mots : {len(mots)}")

    # DICT : dictionnaire des fréquences
    frequences = compter_frequence(mots)

    # TOP 10
    top10 = top_10_mots(frequences)

    # FOR : affichage du top 10
    afficher_top_10(top10)

    # Lecture d'un JSON
    try:
        donnees_json = lire_fichier_json("infos.json")
        print("\n--- DONNEES DU FICHIER JSON ---")
        print(donnees_json)

        if "nom" in donnees_json:
            print("Nom trouvé dans le JSON :", donnees_json["nom"])

    except FileNotFoundError:
        print("\nAucun fichier infos.json trouvé, on passe cette partie.")

    # TUPLE
    resultat_tuple = exemple_tuple()
    print("\n--- EXEMPLE DE TUPLE ---")
    print(resultat_tuple)
    print("Premier élément du tuple :", resultat_tuple[0])


# --------------------------------------------------
# 10. LANCEMENT DU SCRIPT
# --------------------------------------------------
if __name__ == "__main__":
    main()