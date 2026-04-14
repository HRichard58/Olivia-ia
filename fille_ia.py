import streamlit as st
from langchain_groq import ChatGroq
import base64
import requests
from datetime import datetime
import time

# --- 1. CONFIGURATION ---
NOM_IA = "x"
REPO_OWNER = "HRichard58" # <--- À changer
REPO_NAME = "x-ia"
FILE_PATH = "souvenirs_x" # Ton fichier de mémoire

# Connexion API
try:
    groq_key = st.secrets["GROQ_API_KEY"]
    gh_token = st.secrets["GITHUB_TOKEN"]
    llm = ChatGroq(temperature=0.8, groq_api_key=groq_key, model_name="llama-3.1-8b-instant")
except:
    st.error("Vérifie tes Secrets Streamlit !")
    st.stop()

# --- 2. FONCTIONS GITHUB (MÉMOIRE) ---
def lire_memoire_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {gh_token}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()['content']).decode('utf-8')
        return content, r.json()['sha']
    return "x est ...", None

def sauver_memoire_github(nouveau_souvenir):
    contenu_actuel, sha = lire_memoire_github()
    date = datetime.now().strftime("%d/%m")
    nouveau_contenu = contenu_actuel + f"\n- {nouveau_souvenir} ({date})"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    data = {
        "message": "Nouveau souvenir",
        "content": base64.b64encode(nouveau_contenu.encode('utf-8')).decode('utf-8'),
        "sha": sha if sha else ""
    }
    requests.put(url, json=data, headers={"Authorization": f"token {gh_token}"})

# --- 3. INTERFACE ---
st.set_page_config(page_title=NOM_IA)

# Style CSS pour centrer le visage
st.markdown("""
    <style>
    .avatar-container { display: flex; justify-content: center; margin-bottom: 20px; }
    .avatar-img { border-radius: 50%; border: 4px solid #FF69B4; width: 200px; height: 200px; object-fit: cover; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("📱 Menu")
    mode_appel = st.toggle("📞 Mode Appel Vidéo")
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# AFFICHAGE DU VISAGE
if mode_appel:
    st.markdown('<div class="avatar-container">', unsafe_allow_html=True)
    # Si tu as une image sur GitHub, on utilise son URL directe
    url_visage = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/lea_visage.gif"
    st.image(url_visage, width=200)
    st.markdown('</div>', unsafe_allow_html=True)
    st.info("x t'écoute... (Utilise le micro de ton clavier)")

# Initialisation
if "messages" not in st.session_state: st.session_state.messages = []
if "souvenirs" not in st.session_state:
    memo, _ = lire_memoire_github()
    st.session_state.souvenirs = memo

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. LOGIQUE CHAT ---
if prompt := st.chat_input("Parle à x..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    historique = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-20:]])
    instruction = f"Tu es {NOM_IA}. En appel : {mode_appel}. Souvenirs : {st.session_state.souvenirs}. Historique : {historique}"

    with st.chat_message("assistant"):
        try:
            # Simulation de "x réfléchit"
            with st.spinner("x réfléchit..."):
                response = llm.invoke(instruction).content
            
            # Affichage progressif (effet machine à écrire)
            placeholder = st.empty()
            full_res = ""
            for char in response:
                full_res += char
                placeholder.markdown(full_res + "▌")
                time.sleep(0.02)
            placeholder.markdown(full_res)
            
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
            # Mémoire automatique
            if len(prompt) > 12:
                analyse = llm.invoke(f"Fait important en 3 mots : '{prompt}'. Sinon 'NON'").content
                if "NON" not in analyse.upper():
                    sauver_memoire_github(analyse.strip())
                    st.session_state.souvenirs += f"\n- {analyse.strip()}"
        except Exception as e:
            st.error(f"Bug : {e}")
