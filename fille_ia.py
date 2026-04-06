import streamlit as st
from langchain_groq import ChatGroq
import base64
import requests
from datetime import datetime

# --- 1. CONFIGURATION ---
NOM_IA = "Léa"
REPO_OWNER = "HRichard58"  # <--- METS TON NOM D'UTILISATEUR GITHUB ICI
REPO_NAME = "lea-ia"       # <--- LE NOM DE TON DOSSIER SUR GITHUB
FILE_PATH = "memoire.txt"

# Récupération sécurisée des clés depuis les Secrets
try:
    groq_key = st.secrets["GROQ_API_KEY"]
    gh_token = st.secrets["GITHUB_TOKEN"]
    llm = ChatGroq(
        temperature=0.8, 
        groq_api_key=groq_key, 
        model_name="llama-3.1-8b-instant"
    )
except Exception as e:
    st.error("Erreur : Les clés (Groq ou GitHub) ne sont pas configurées dans les Secrets.")
    st.stop()

# --- 2. FONCTIONS DE MÉMOIRE (GITHUB) ---
def lire_memoire_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {gh_token}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        return content, r.json()['sha']
    return "Léa est une amie proche.", None

def sauver_memoire_github(nouveau_souvenir):
    contenu_actuel, sha = lire_memoire_github()
    date = datetime.now().strftime("%d/%m %H:%M")
    nouveau_contenu = contenu_actuel + f"\n- {nouveau_souvenir} ({date})"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {gh_token}"}
    data = {
        "message": "Léa a appris quelque chose de nouveau",
        "content": base64.b64encode(nouveau_contenu.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    requests.put(url, json=data, headers=headers)

# --- 3. INTERFACE ---
st.set_page_config(page_title=NOM_IA, page_icon="🌸")
st.title(f"💬 {NOM_IA}")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Charger les souvenirs au premier lancement
if "souvenirs" not in st.session_state:
    memo, _ = lire_memoire_github()
    st.session_state.souvenirs = memo

# Affichage du chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 4. LOGIQUE DE CHAT ---
if prompt := st.chat_input("Dis-moi quelque chose..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Contexte pour Léa
    historique = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
    instruction = f"""Tu es {NOM_IA}, une amie réelle. Style SMS. 
    Tes souvenirs : {st.session_state.souvenirs}
    Discussion : {historique}"""

    with st.chat_message("assistant"):
        try:
            reponse = llm.invoke(instruction).content
            st.markdown(reponse)
            st.session_state.messages.append({"role": "assistant", "content": reponse})
            
            # Analyse pour la mémoire éternelle
            if len(prompt) > 10:
                analyse = llm.invoke(f"Retiens un fait sur l'utilisateur en 3 mots max de : '{prompt}'. Sinon 'NON'").content
                if "NON" not in analyse.upper():
                    sauver_memoire_github(analyse.strip())
                    st.session_state.souvenirs += f"\n- {analyse.strip()}"
                    st.toast("Souvenir enregistré sur GitHub ! 🧠")
        except Exception as e:
            st.error(f"Bug : {e}")
