import streamlit as st
from langchain_groq import ChatGroq
import base64
import requests
from datetime import datetime
import time

# --- 1. CONFIGURATION ---
NOM_IA = "Olivia"
REPO_OWNER = "HRichard58"
REPO_NAME = "Olivia-ia"
FILE_PATH = "souvenirs.txt" 

# Connexion API
try:
    groq_key = st.secrets["GROQ_API_KEY"]
    gh_token = st.secrets["GITHUB_TOKEN"]
    llm = ChatGroq(temperature=0.8, groq_api_key=groq_key, model_name="llama-3.1-8b-instant")
except Exception as e:
    st.error(f"Vérifie tes Secrets Streamlit ! Erreur : {e}")
    st.stop()

# --- 2. FONCTIONS GITHUB (MÉMOIRE) ---
def lire_memoire_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {gh_token}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        return content, r.json()['sha']
    return "Début du journal.", None

def sauver_memoire_github(nouveau_souvenir):
    contenu_actuel, sha = lire_memoire_github()
    date = datetime.now().strftime("%d/%m %H:%M")
    # On ajoute directement le message au contenu existant
    nouveau_contenu = contenu_actuel + f"\n- {nouveau_souvenir} ({date})"
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    data = {
        "message": "Nouvel échange enregistré",
        "content": base64.b64encode(nouveau_contenu.encode('utf-8')).decode('utf-8'),
        "sha": sha if sha else ""
    }
    
    r = requests.put(url, json=data, headers={"Authorization": f"token {gh_token}"})
    return r.status_code

# --- 3. INTERFACE ---
st.set_page_config(page_title=NOM_IA)

with st.sidebar:
    st.title("📱 Menu")
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()
    st.write("---")
    st.write(f"Fichier : `{FILE_PATH}`")

# Initialisation
if "messages" not in st.session_state: st.session_state.messages = []
if "souvenirs" not in st.session_state:
    memo, _ = lire_memoire_github()
    st.session_state.souvenirs = memo

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. LOGIQUE CHAT ---
if prompt := st.chat_input("Parle à Olivia..."):
    # 1. Afficher le message utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    # 2. Sauvegarde immédiate dans GitHub
    status = sauver_memoire_github(prompt)
    if status in [200, 201]:
        st.toast("Souvenir enregistré !", icon="💾")
    else:
        st.error(f"Erreur de sauvegarde GitHub : {status}")

    # 3. Préparer la réponse de l'IA
    historique = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-10:]])
    instruction = f"Tu es {NOM_IA}. Tes souvenirs permanents : {st.session_state.souvenirs}. Historique récent : {historique}"

    with st.chat_message("assistant"):
        try:
            with st.spinner("Olivia réfléchit..."):
                response = llm.invoke(instruction).content
            
            placeholder = st.empty()
            full_res = ""
            for char in response:
                full_res += char
                placeholder.markdown(full_res + "▌")
                time.sleep(0.01)
            placeholder.markdown(full_res)
            
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
        except Exception as e:
            st.error(f"Bug : {e}")
