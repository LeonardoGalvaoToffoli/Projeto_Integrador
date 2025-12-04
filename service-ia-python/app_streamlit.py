import os
import streamlit as st
import requests
import time
import pandas as pd
import json

FLASK_BASE_URL = os.getenv("FLASK_BASE_URL", "http://localhost:5000")
# --- CONSTANTE DE SEGURANÇA ---
HEADERS = {"X-API-KEY": "SCI-BDI-SECRET-KEY-2025"}

st.set_page_config(
    page_title="SCI-BDI: Clusterização de Imagens",
    layout="wide"
)

st.title("🧠 Sistema de Clusterização e Busca Inteligente")
st.markdown("Interface de controle para organização automática e busca visual de imagens.")

# --- 1. GERENCIAMENTO DE ESTADO (Onde ocorreu o erro) ---
# Este bloco é essencial para inicializar as variáveis na memória do navegador
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'job_status' not in st.session_state:
    st.session_state.job_status = "Aguardando Início"
if 'clustering_result' not in st.session_state:
    st.session_state.clustering_result = None

# --- 2. Painel de Controle ---
st.header("1. Pipeline de Processamento")

def start_job():
    st.session_state.job_status = "Iniciando..."
    st.session_state.clustering_result = None
    try:
        # Envia a chave de segurança no header
        response = requests.post(f"{FLASK_BASE_URL}/clusterizar", headers=HEADERS)
        if response.status_code == 202:
            data = response.json()
            st.session_state.job_id = data['job_id']
            st.session_state.job_status = data['status']
            st.success(f"Job iniciado: {st.session_state.job_id}")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"Erro na solicitação. Status: {response.status_code}")
            st.session_state.job_status = "ERRO"
    except requests.exceptions.ConnectionError:
        st.error("Falha de comunicação com a API Flask.")
        st.session_state.job_status = "ERRO"

if st.button("▶️ Executar Clusterização"):
    start_job()
    
# --- 3. Monitoramento ---
st.header("2. Monitoramento")

if st.session_state.job_id:
    st.info(f"ID do Job: **{st.session_state.job_id}**")
    
    def check_status():
        try:
            # Envia a chave de segurança no header
            response = requests.get(f"{FLASK_BASE_URL}/status/{st.session_state.job_id}", headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                st.session_state.job_status = data['status']
            else:
                st.session_state.job_status = "ERRO"
        except requests.exceptions.ConnectionError:
            st.session_state.job_status = "ERRO CONEXÃO"
            
    if st.session_state.job_status not in ["CONCLUÍDO", "ERRO", "ERRO CONEXÃO"]:
        check_status()
        
    st.subheader(f"Status: {st.session_state.job_status}")
    
    if st.session_state.job_status == "EM PROGRESSO":
        st.progress(0.5, text="Processando...")
        time.sleep(3) 
        st.rerun()
    elif st.session_state.job_status == "CONCLUÍDO":
        st.success("Processamento concluído.")
    
# --- 4. Resultados ---
st.header("3. Resultados")

if st.session_state.job_status == "CONCLUÍDO" and st.session_state.clustering_result is None:
    try:
        # Envia a chave de segurança no header
        response = requests.get(f"{FLASK_BASE_URL}/pastas/{st.session_state.job_id}", headers=HEADERS)
        if response.status_code == 200:
            st.session_state.clustering_result = response.json()
        else:
             st.error("Erro ao carregar resultados.")
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão.")

if st.session_state.clustering_result:
    result = st.session_state.clustering_result
    st.markdown(f"**Clusters Gerados:** `{len(result['pastas_ordenadas'])}`")
    
    pasta_data = []
    for pasta in result['pastas_ordenadas']:
        arquivos = result['conteudo_ordenado'].get(pasta, [])
        pasta_data.append({
            "Grupo": pasta,
            "Qtd Imagens": len(arquivos),
            "Exemplos": ", ".join(arquivos[:3]) + ("..." if len(arquivos) > 3 else "")
        })
    st.dataframe(pd.DataFrame(pasta_data), use_container_width=True)

    with st.expander("Dados Brutos (JSON)"):
        st.code(json.dumps(result, indent=2))

# --- 5. Busca Inteligente ---
st.markdown("---")
st.header("4. 🔎 Busca Visual")
st.markdown("Upload de imagem para classificação automática via índice Java.")

uploaded_file = st.file_uploader("Carregar imagem", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Imagem de Entrada", width=250)
    
    files_to_send = {'image': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    
    if st.button("🔍 Buscar Similaridade"):
        with st.spinner("Consultando serviço de busca..."):
            try:
                # Envia a chave de segurança no header
                response = requests.post(f"{FLASK_BASE_URL}/search", files=files_to_send, headers=HEADERS)
                
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"**Classificação:** `{result['clusterEncontrado']}`")
                else:
                    st.error(f"Erro: {response.json().get('error', 'Desconhecido')}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Serviço indisponível.")
            except Exception as e:
                st.error(f"Exceção: {e}")