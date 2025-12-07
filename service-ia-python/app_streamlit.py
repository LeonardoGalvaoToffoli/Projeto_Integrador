import streamlit as st
import requests, time, os

# Configurações
FLASK_URL = os.getenv("FLASK_BASE_URL", "http://127.0.0.1:5000")
HEADERS = {"X-API-KEY": os.getenv("API_SECRET_KEY", "SCI-BDI-SECRET-KEY-2025")}

st.set_page_config(page_title="Neon AI", layout="wide", page_icon="⚡")

# --- DESIGN SYSTEM: NEON & NAVY ---
st.markdown("""
<style>
    .stApp { background-color: #050A30; }
    h1, h2, h3, p, div, span, label, .stMarkdown { color: #E0E0E0 !important; font-family: 'Courier New', monospace; }
    
    /* Upload Box */
    .stFileUploader { 
        border: 2px dashed #39FF14; 
        padding: 20px; 
        border-radius: 15px; 
        background-color: rgba(57, 255, 20, 0.05);
    }
    
    /* Esconder Elementos */
    [data-testid="stSidebar"] { display: none; }
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Botões */
    div.stButton > button {
        background-color: transparent;
        color: #39FF14 !important;
        border: 1px solid #39FF14;
        width: 100%;
        border-radius: 8px;
    }
    div.stButton > button:hover {
        background-color: #39FF14;
        color: #050A30 !important;
        font-weight: bold;
    }
    
    /* Cards de Resultado */
    .neon-card {
        border: 1px solid #39FF14;
        background-color: #000050;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.1);
    }
    .card-head { font-size: 1.2rem; font-weight: bold; color: #39FF14 !important; }
    
    /* Imagens na Galeria */
    img { border-radius: 5px; border: 1px solid #444; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ SCI-BDI: Organizador Automático")
st.markdown("Arraste suas fotos. A IA agrupa imagens similares automaticamente.")

# Inicialização de Variáveis
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0
if 'last_count' not in st.session_state: st.session_state.last_count = 0
if 'job_id' not in st.session_state: st.session_state.job_id = None
if 'status' not in st.session_state: st.session_state.status = ""
if 'result' not in st.session_state: st.session_state.result = None

# --- Upload Automático ---
files = st.file_uploader(
    "", 
    accept_multiple_files=True, 
    type=['png','jpg','jpeg'], 
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}"
)

# CRÍTICO: Cria o mapa {nome: arquivo} para poder exibir as fotos depois
file_map = {f.name: f for f in files} if files else {}

# Botão para limpar a seleção (Só aparece se tiver arquivos)
if files:
    col_vazia, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("🗑️ Limpar Seleção"):
            st.session_state.uploader_key += 1
            st.session_state.last_count = 0
            st.session_state.job_id = None
            st.session_state.status = ""
            st.session_state.result = None
            st.rerun()

# Processamento
if files:
    curr = len(files)
    if curr != st.session_state.last_count:
        st.session_state.last_count = curr
        
        with st.status("⚡ Processando...", expanded=True) as status:
            try:
                # Payload padrão
                payload = [('images', (f.name, f.getvalue(), f.type)) for f in files]
                res = requests.post(f"{FLASK_URL}/clusterizar", files=payload, headers=HEADERS)
                
                if res.status_code == 202:
                    st.session_state.job_id = res.json()['job_id']
                    st.session_state.status = "EM PROGRESSO"
                    st.session_state.result = None
                    
                    st.write("Analisando similaridade visual...")
                    while True:
                        check = requests.get(f"{FLASK_URL}/status/{st.session_state.job_id}", headers=HEADERS).json()
                        s = check.get('status', 'ERRO')
                        if s == "CONCLUÍDO":
                            st.session_state.status = "CONCLUÍDO"
                            status.update(label="Pronto!", state="complete", expanded=False)
                            break
                        elif s == "ERRO": 
                            st.error("Erro."); break
                        time.sleep(1)
                    
                    if st.session_state.status == "CONCLUÍDO":
                        st.session_state.result = requests.get(f"{FLASK_URL}/pastas/{st.session_state.job_id}", headers=HEADERS).json()
                        st.rerun()
            except Exception as e: st.error(f"Erro de conexão: {e}")

# Resultados (Só aparece se CONCLUÍDO)
if st.session_state.result and st.session_state.status == "CONCLUÍDO":
    st.divider()
    st.subheader("📂 Grupos Formados")
    
    data = st.session_state.result
    cols = st.columns(3)
    
    for idx, folder in enumerate(data['pastas_ordenadas']):
        with cols[idx % 3]:
            file_list = data['conteudo_ordenado'][folder]
            count = len(file_list)
            
            st.markdown(f"""
            <div class="neon-card">
                <div class="card-head">{folder}</div>
                <div style="color: #ccc;">{count} imagens</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Galeria de Fotos (Correção aplicada aqui)
            with st.expander("Ver Fotos"):
                img_grid = st.columns(3) # Grid interna 3x3
                for i, filename in enumerate(file_list):
                    # Verifica se a imagem está na memória (file_map)
                    if filename in file_map:
                        with img_grid[i % 3]:
                            st.image(file_map[filename], use_container_width=True)
    
    # Botão Limpar Tudo
    st.divider()
    if st.button("Limpar Tudo e Reiniciar"):
        st.session_state.uploader_key += 1
        st.session_state.last_count = 0
        st.session_state.result = None
        st.session_state.job_id = None
        st.session_state.status = ""
        st.rerun()

    # --- Busca Visual (MOVIDA PARA CÁ) ---
    # Só aparece se o status for CONCLUÍDO, pois depende do índice Java estar pronto
    st.markdown("---")
    st.subheader("🔍 Testar Busca Visual")
    st.caption("Agora que a IA aprendeu suas fotos, envie uma nova para ver onde ela se encaixa.")
    
    with st.expander("Abrir Classificador", expanded=True):
        test = st.file_uploader("", type=['jpg','png'], key="search")
        if test and st.button("Classificar"):
            try:
                r = requests.post(f"{FLASK_URL}/search", files={'image':test}, headers=HEADERS)
                if r.status_code == 200:
                    st.success(f"A IA classificou como: **{r.json()['clusterEncontrado']}**")
                    st.image(test, width=150)
                else: st.error("Erro na busca")
            except: st.error("Erro de conexão")