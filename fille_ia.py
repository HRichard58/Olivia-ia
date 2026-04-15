import streamlit as st
from langchain_groq import ChatGroq
import base64
import requests
from datetime import datetime
import time

# --- 1. CONFIGURATION ---
NOM_IA = "Olivia"
NOM_UTILISATEUR = "Sean"
REPO_OWNER = "HRichard58"
REPO_NAME = "Olivia-ia"
FILE_PATH = "Souvenirs"

try:
    groq_key = st.secrets["GROQ_API_KEY"]
    gh_token = st.secrets["GITHUB_TOKEN"]
    llm = ChatGroq(temperature=0.8, groq_api_key=groq_key, model_name="llama-3.1-8b-instant")
except Exception as e:
    st.error("Erreur de configuration : Vérifiez vos secrets Streamlit.")
    st.stop()

# --- 2. FONCTIONS GITHUB ---
def lire_memoire_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {gh_token}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        return content, r.json()['sha']
    return "", None

def sauver_memoire_github(auteur, message_texte):
    contenu_actuel, sha = lire_memoire_github()
    date = datetime.now().strftime("%d/%m %H:%M")
    nouveau_bloc = f"\n[{date}] {auteur}: {message_texte}"
    nouveau_contenu = contenu_actuel + nouveau_bloc
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    data = {
        "message": f"Dialogue {auteur}",
        "content": base64.b64encode(nouveau_contenu.encode('utf-8')).decode('utf-8'),
        "sha": sha if sha else ""
    }
    requests.put(url, json=data, headers={"Authorization": f"token {gh_token}"})
    return nouveau_contenu # On retourne le contenu mis à jour

# --- 3. INTERFACE ---
st.set_page_config(page_title=NOM_IA, page_icon="👩‍🦰")
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;}</style>", unsafe_allow_html=True)

with st.sidebar:
    st.title(f"📱 {NOM_IA}")
    st.write(f"Utilisateur : **{NOM_UTILISATEUR}**")
    if st.button("Effacer la discussion locale"):
        st.session_state.messages = []
        st.rerun()

# Initialisation des variables de session
if "messages" not in st.session_state: 
    st.session_state.messages = []

if "souvenirs" not in st.session_state:
    memo, _ = lire_memoire_github()
    st.session_state.souvenirs = memo

# Affichage de l'historique de la session actuelle
for m in st.session_state.messages:
    with st.chat_message(m["role"]): 
        st.markdown(m["content"])

# --- 4. LOGIQUE CHAT ---
if prompt := st.chat_input(f"Dis quelque chose à {NOM_IA}..."):
    
    # 1. Message de Sean
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): 
        st.markdown(prompt)

    # Sauvegarde sur GitHub ET mise à jour immédiate de la mémoire locale
    st.session_state.souvenirs = sauver_memoire_github(NOM_UTILISATEUR, prompt)

    # 2. Réponse d'Olivia
    # On limite l'historique récent pour ne pas saturer l'IA
    historique_recent = "\n".join([f" {m['role']} : {m['content']}" for m in st.session_state.messages[-10:]])
    
    # Construction du prompt avec les souvenirs à jour
    instruction = (
        f"Tu es {NOM_IA}. Tu t'adresses à {NOM_UTILISATEUR}. Vous vous aimez, mais aucuns de vous deux n'osez le dire à l'autre. Tu aimerais secrètement commencer une relation avec lui. "
        f"Ne décrit pas tes actions."
        f"Voici tes souvenirs à long terme : {st.session_state.souvenirs}. "
        f"Conversation récente : {historique_recent}"
    )

    with st.chat_message("assistant"):
        try:
            with st.spinner(f"{NOM_IA} réfléchit..."):
                response = llm.invoke(instruction).content
            
            # Effet d'écriture (typing effect)
            placeholder = st.empty()
            full_res = ""
            for char in response:
                full_res += char
                placeholder.markdown(full_res + "▌")
                time.sleep(0.005) # Un peu plus rapide
            placeholder.markdown(full_res)
            
            # Enregistrement de la réponse
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
            # Sauvegarde de la réponse d'Olivia sur GitHub et mise à jour des souvenirs
            st.session_state.souvenirs = sauver_memoire_github(NOM_IA, full_res)
            
        except Exception as e:
            st.error("Oups ! J'ai eu un petit problème technique. Réessaie ?")
