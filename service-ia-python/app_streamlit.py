import streamlit as st
import requests
import time
import pandas as pd
import json

# --- Configurações da API ---
FLASK_BASE_URL = "http://localhost:5000"

st.set_page_config(
    page_title="Projeto Integrador IA: Clusterização de Imagens",
    layout="wide"
)

st.title("🧠 Clusterização de Imagens com CNN e K-Means")
st.markdown("Use esta interface para iniciar o processamento de IA e visualizar a organização das imagens.")

# --- Sessão 1: Iniciar o Processamento ---
st.header("1. Iniciar o Processamento de Clusterização")

# ... (Seu código original da Sessão 1 - sem alterações) ...
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'job_status' not in st.session_state:
    st.session_state.job_status = "Aguardando Início"
if 'clustering_result' not in st.session_state:
    st.session_state.clustering_result = None

def start_job():
    st.session_state.job_status = "Iniciando..."
    st.session_state.clustering_result = None
    try:
        response = requests.post(f"{FLASK_BASE_URL}/clusterizar")
        if response.status_code == 202:
            data = response.json()
            st.session_state.job_id = data['job_id']
            st.session_state.job_status = data['status']
            st.success(f"Clusterização iniciada! Job ID: {st.session_state.job_id}")
            time.sleep(1)
            st.rerun()
        else:
            st.error(f"Erro ao iniciar a clusterização. Status: {response.status_code}. Mensagem: {response.text}")
            st.session_state.job_status = "ERRO"
    except requests.exceptions.ConnectionError:
        st.error("ERRO: Não foi possível conectar ao servidor Flask. Verifique se 'api_server.py' está rodando na porta 5000.")
        st.session_state.job_status = "ERRO"

if st.button("▶️ Iniciar Clusterização de Imagens"):
    start_job()
    
# --- Sessão 2: Monitoramento do Status ---
st.header("2. Monitoramento e Status")
# ... (Seu código original da Sessão 2 - sem alterações) ...
current_job_id = st.session_state.job_id
if current_job_id:
    st.info(f"Monitorando Job ID: **{current_job_id}**")
    
    def check_status():
        try:
            response = requests.get(f"{FLASK_BASE_URL}/status/{current_job_id}")
            if response.status_code == 200:
                data = response.json()
                st.session_state.job_status = data['status']
            else:
                st.session_state.job_status = "ERRO - ID não encontrado"
        except requests.exceptions.ConnectionError:
            st.session_state.job_status = "ERRO - Falha na Conexão Flask"
            
    if st.session_state.job_status not in ["CONCLUÍDO", "ERRO", "ERRO - ID não encontrado", "ERRO - Falha na Conexão Flask"]:
        check_status()
        
    st.subheader(f"Status Atual: {st.session_state.job_status}")
    
    if st.session_state.job_status == "EM PROGRESSO":
        st.progress(0.5, text="Processamento da IA em andamento. Aguardando...")
        time.sleep(3) 
        st.rerun()
    elif st.session_state.job_status == "CONCLUÍDO":
        st.success("✅ Clusterização Concluída! Pronto para Visualizar.")
    
# --- Sessão 3: Visualização dos Resultados ---
st.header("3. Visualização dos Resultados")
# ... (Seu código original da Sessão 3 - sem alterações) ...
if st.session_state.job_status == "CONCLUÍDO" and st.session_state.clustering_result is None:
    try:
        response = requests.get(f"{FLASK_BASE_URL}/pastas/{current_job_id}")
        if response.status_code == 200:
            st.session_state.clustering_result = response.json()
        else:
             st.error(f"Erro ao buscar resultados: {response.status_code}. Mensagem: {response.text}")
             st.session_state.job_status = "ERRO"
    except requests.exceptions.ConnectionError:
        st.error("ERRO: Não foi possível conectar ao servidor Flask.")

if st.session_state.clustering_result:
    result = st.session_state.clustering_result
    st.subheader("Pastas Geradas (Organização da IA)")
    st.markdown(f"**Total de Pastas (Clusters):** `{len(result['pastas_ordenadas'])}`")
    pasta_data = []
    for pasta in result['pastas_ordenadas']:
        arquivos = result['conteudo_ordenado'].get(pasta, [])
        pasta_data.append({
            "Pasta (Cluster)": pasta,
            "Total de Imagens": len(arquivos),
            "Exemplo de Imagens": ", ".join(arquivos[:3]) + ("..." if len(arquivos) > 3 else "")
        })
    st.dataframe(pd.DataFrame(pasta_data), use_container_width=True)
    with st.expander("Ver JSON Completo (Dados Ordenados)"):
        st.code(json.dumps(result, indent=2))
        st.caption("Este é o formato de dados EXATAMENTE como o Java precisaria para a Busca Binária eficiente.")

# --- NOVA SEÇÃO 4: Buscar Imagem Similar ---
st.markdown("---")
st.header("4. 🔎 Buscar Imagem Similar")
st.markdown("Faça o upload de uma imagem para descobrir a qual cluster ela pertence.")

uploaded_file = st.file_uploader("Escolha uma imagem para buscar", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="Imagem Enviada", width=300)
    
    # Prepara o arquivo para envio via API (multipart/form-data)
    files_to_send = {'image': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
    
    with st.spinner("Analisando imagem e buscando no índice Java..."):
        try:
            # Chama o endpoint /search do Flask
            response = requests.post(f"{FLASK_BASE_URL}/search", files=files_to_send)
            
            if response.status_code == 200:
                result = response.json()
                st.success(f"**Cluster Encontrado:** `{result['clusterEncontrado']}`")
                st.balloons()
            else:
                st.error(f"Erro ao buscar: {response.json().get('error', response.text)}")
                
        except requests.exceptions.ConnectionError:
            st.error("ERRO: Não foi possível conectar ao servidor Flask. Verifique se 'api_server.py' está rodando.")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")