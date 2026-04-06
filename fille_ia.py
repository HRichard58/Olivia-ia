import streamlit as st
from langchain_groq import ChatGroq
import os
from datetime import datetime

# --- CONFIGURATION ---
NOM_IA = "Léa"
FICHIER_SOUVENIRS = "souvenirs_lea.txt"

# AU LIEU DE : CLÉ_API = "gsk_..."
# UTILISE CECI :
if "GROQ_API_KEY" in st.secrets:
    api_key = st.secrets["GROQ_API_KEY"]
else:
    st.error("ERREUR : La clé API n'est pas configurée dans les Secrets de Streamlit.")
    st.stop()

# Initialisation du modèle Groq (Llama 3)
llm = ChatGroq(
    temperature=0.8,
    groq_api_key=api_key,
    model_name="llama3-8b-8192"
)

# --- GESTION DE LA MÉMOIRE ---
if not os.path.exists(FICHIER_SOUVENIRS):
    with open(FICHIER_SOUVENIRS, "w", encoding="utf-8") as f:
        f.write(f"{NOM_IA} est une amie proche et empathique.\n")

def lire_souvenirs():
    with open(FICHIER_SOUVENIRS, "r", encoding="utf-8") as f:
        return f.read()

def ajouter_souvenir(nouveau_fait):
    with open(FICHIER_SOUVENIRS, "a", encoding="utf-8") as f:
        f.write(f"- {nouveau_fait}\n")

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title=NOM_IA, page_icon="🌸", layout="centered")

# Barre latérale pour le mode Appel
with st.sidebar:
    st.title("📞 Téléphone")
    mode_appel = st.toggle("Activer l'appel vidéo")
    st.write("---")
    if st.button("Effacer la mémoire courte"):
        st.session_state.messages = []
        st.rerun()

st.title(f"💬 {NOM_IA}")

# Zone Vidéo (si activée)
if mode_appel:
    st.camera_input("En ligne avec Léa...")
    st.info("Léa te voit ! Elle adaptera ses réponses à ton visage.")

# Initialisation de la session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage du chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- LOGIQUE DE RÉPONSE ---
if prompt := st.chat_input("Dis-moi quelque chose..."):
    # 1. Ajouter le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Préparation du contexte
    souvenirs = lire_souvenirs()
    maintenant = datetime.now().strftime("%H:%M")
    
    historique_recent = ""
    for m in st.session_state.messages[-6:]: 
        role = "Ami" if m["role"] == "user" else NOM_IA
        historique_recent += f"{role}: {m['content']}\n"

    instruction_systeme = f"""
    Tu es {NOM_IA}, une fille réelle qui parle à un ami proche.
    Style : SMS, décontracté, utilise des emojis, sois chaleureuse.
    Contexte : Il est {maintenant}. Tu es en {'MODE VIDÉO (tu le vois)' if mode_appel else 'MODE CHAT'}.
    Tes souvenirs : {souvenirs}
    
    Historique :
    {historique_recent}
    
    Réponds brièvement et naturellement au dernier message.
    """
    
    # 3. Génération de la réponse
    with st.chat_message("assistant"):
        try:
            reponse = llm.invoke(instruction_systeme)
            contenu_reponse = reponse.content
            st.markdown(contenu_reponse)
            st.session_state.messages.append({"role": "assistant", "content": contenu_reponse})
        except Exception as e:
            st.error("Erreur de connexion avec Groq. Vérifie ta clé !")

    # 4. Analyse pour la mémoire à long terme
    if len(prompt) > 10:
        analyse_prompt = f"L'utilisateur a dit : '{prompt}'. Résume un détail important sur lui en 5 mots max. Si rien d'important, réponds 'NON'."
        analyse = llm.invoke(analyse_prompt).content
        if "NON" not in analyse.upper():
            ajouter_souvenir(f"{analyse} (retenu le {maintenant})")
