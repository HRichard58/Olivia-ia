import streamlit as st
from langchain_groq import ChatGroq
import base64
import requests
from datetime import datetime

# --- 1. CONFIGURATION ---
NOM_IA = "Léa"
REPO_OWNER = "HRichard58"  # <--- TON PSEUDO GITHUB ICI
REPO_NAME = "lea-ia"
FILE_PATH = "souvenirs_lea.txt"

# Récupération des clés
try:
    groq_key = st.secrets["GROQ_API_KEY"]
    gh_token = st.secrets["GITHUB_TOKEN"]
    llm = ChatGroq(temperature=0.8, groq_api_key=groq_key, model_name="llama-3.1-8b-instant")
except:
    st.error("Configure les Secrets (GROQ_API_KEY et GITHUB_TOKEN) sur Streamlit.")
    st.stop()

# --- 2. FONCTIONS MÉMOIRE GITHUB ---
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
    nouveau_contenu = contenu_actuel + f"\n- {nouveau_souvenir} ({datetime.now().strftime('%d/%m')})"
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    data = {
        "message": "Nouveau souvenir",
        "content": base64.b64encode(nouveau_contenu.encode('utf-8')).decode('utf-8'),
        "sha": sha
    }
    requests.put(url, json=data, headers={"Authorization": f"token {gh_token}"})

# --- 3. INTERFACE ---
st.set_page_config(page_title="Discussion", page_icon="🌸")

# Barre latérale pour l'appel
with st.sidebar:
    st.title("📱 Téléphone")
    mode_appel = st.toggle("📞 Lancer l'appel", help="Active la caméra et le micro pour parler à Léa")
    st.write("---")
    if st.button("Effacer l'historique"):
        st.session_state.messages = []
        st.rerun()

st.title(f"💬 {NOM_IA}")

# ZONE APPEL VIDÉO
if mode_appel:
    st.subheader("🎥 Appel en cours...")
    # Ceci active la caméra de l'utilisateur
    img_file = st.camera_input("Léa te regarde !")
    if img_file:
        st.success("Léa sourit en te voyant !")

# Initialisation
if "messages" not in st.session_state:
    st.session_state.messages = []
if "souvenirs" not in st.session_state:
    memo, _ = lire_memoire_github()
    st.session_state.souvenirs = memo

# Affichage du chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 4. LOGIQUE DE CHAT ---
if prompt := st.chat_input("Dis-lui quelque chose..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    historique = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-5:]])
    
    # Instruction adaptée si on est en "appel"
    contexte_appel = "Tu es en APPEL VIDÉO, tu vois l'utilisateur." if mode_appel else "Tu es en CHAT SMS."
    
    instruction = f"""Tu es {NOM_IA}, une amie réelle. {contexte_appel}
    Souvenirs : {st.session_state.souvenirs}
    Historique : {historique}"""

    with st.chat_message("assistant"):
        try:
            reponse = llm.invoke(instruction).content
            st.markdown(reponse)
            st.session_state.messages.append({"role": "assistant", "content": reponse})
            
            # Mémoire
            if len(prompt) > 10:
                analyse = llm.invoke(f"Retiens un fait important en 3 mots : '{prompt}'. Sinon 'NON'").content
                if "NON" not in analyse.upper():
                    sauver_memoire_github(analyse.strip())
                    st.session_state.souvenirs += f"\n- {analyse.strip()}"
        except Exception as e:
            st.error(f"Bug : {e}")
