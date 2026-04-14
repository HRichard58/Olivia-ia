import streamlit as st
from langchain_groq import ChatGroq
import base64
import requests
from datetime import datetime
import time
from gtts import gTTS
import io

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="Olivia", page_icon="👩‍🦰", layout="wide")

def local_css():
    st.markdown("""
    <style>
    /* Style des bulles de chat */
    .stChatMessage { border-radius: 15px; padding: 10px; margin-bottom: 10px; }
    .st-emotion-cache-janbn0 { flex-direction: row-reverse; text-align: right; background-color: #007AFF !important; color: white !important; } /* Utilisateur à droite */
    .st-emotion-cache-4oy321 { background-color: #E9E9EB !important; color: black !important; } /* IA à gauche */
    
    /* Masquer le menu Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Avatar style */
    .avatar-container { display: flex; justify-content: center; margin-bottom: 20px; }
    .ia-avatar { border-radius: 50%; border: 3px solid #FF4B4B; width: 150px; height: 150px; object-fit: cover; }
    </style>
    """, unsafe_allow_html=True)

local_css()

# --- CONSTANTES ---
NOM_IA = "Olivia"
NOM_UTILISATEUR = "Sean"
REPO_OWNER = "HRichard58"
REPO_NAME = "Olivia-ia"
FILE_PATH = "Souvenirs"

# --- INITIALISATION ---
try:
    groq_key = st.secrets["GROQ_API_KEY"]
    gh_token = st.secrets["GITHUB_TOKEN"]
    llm = ChatGroq(temperature=0.8, groq_api_key=groq_key, model_name="llama-3.1-8b-instant")
except:
    st.error("Configurez vos secrets (GROQ_API_KEY, GITHUB_TOKEN) dans Streamlit.")
    st.stop()

# --- FONCTIONS LOGIQUES (GITHUB & AUDIO) ---
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
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    data = {
        "message": f"Dialogue {auteur}",
        "content": base64.b64encode((contenu_actuel + nouveau_bloc).encode('utf-8')).decode('utf-8'),
        "sha": sha if sha else ""
    }
    requests.put(url, json=data, headers={"Authorization": f"token {gh_token}"})
    return contenu_actuel + nouveau_bloc

def text_to_speech(text):
    tts = gTTS(text=text, lang='fr')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

# --- INTERFACE SIDEBAR (MODES) ---
with st.sidebar:
    st.title(f"💞 {NOM_IA}")
    mode = st.radio("Mode d'interaction :", ["Chat Textuel", "Appel Audio", "Appel Vidéo"])
    st.divider()
    if st.button("Effacer l'historique"):
        st.session_state.messages = []
        st.rerun()

# Gestion de l'état
if "messages" not in st.session_state: st.session_state.messages = []
if "souvenirs" not in st.session_state:
    memo, _ = lire_memoire_github()
    st.session_state.souvenirs = memo

# --- AFFICHAGE SELON LE MODE ---

if mode == "Chat Textuel":
    # Affichage des messages
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    if prompt := st.chat_input("Écris un message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        # Logique de réponse
        instruction = f"Tu es {NOM_IA}. Tu parles à {NOM_UTILISATEUR}. Souvenirs : {st.session_state.souvenirs}"
        response = llm.invoke(instruction).content
        
        with st.chat_message("assistant"):
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.souvenirs = sauver_memoire_github(NOM_IA, response)

elif mode == "Appel Audio":
    st.subheader("📞 Appel en cours...")
    col1, col2 = st.columns(2)
    with col1:
        st.info("Olivia t'écoute...")
        # Note : Le vrai STT en temps réel nécessite des bibliothèques plus complexes comme streamlit-mic-recorder
    if st.button("Parler (Simulé)"):
        # Ici on simule une entrée vocale
        prompt = "Olivia, tu m'entends ?"
        st.write(f"Toi : {prompt}")
        response = llm.invoke(f"Réponds brièvement à : {prompt}").content
        st.write(f"Olivia : {response}")
        audio_fp = text_to_speech(response)
        st.audio(audio_fp, format='audio/mp3', autoplay=True)

elif mode == "Appel Vidéo":
    st.subheader("📹 Visioconférence")
    col_me, col_ia = st.columns(2)
    
    with col_me:
        st.write("Ta caméra")
        img_file = st.camera_input("Activer ma caméra", label_visibility="collapsed")
        
    with col_ia:
        st.write(f"Le visage de {NOM_IA}")
        # Image statique ou GIF animé pour simuler l'IA
        st.image("https://pinkmirror.com/blog/wp-content/uploads/2022/05/AI-Generation-of-Face.jpg", use_column_width=True)
        if st.button("Lancer la discussion"):
            st.write("Olivia vous regarde et sourit...")
