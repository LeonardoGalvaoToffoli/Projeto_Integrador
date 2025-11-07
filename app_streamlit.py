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

# Se o Job ID não estiver na sessão, ele será None
if 'job_id' not in st.session_state:
    st.session_state.job_id = None
if 'job_status' not in st.session_state:
    st.session_state.job_status = "Aguardando Início"
if 'clustering_result' not in st.session_state:
    st.session_state.clustering_result = None

def start_job():
    """Chama o endpoint /clusterizar da API Flask."""
    st.session_state.job_status = "Iniciando..."
    st.session_state.clustering_result = None
    
    try:
        response = requests.post(f"{FLASK_BASE_URL}/clusterizar")
        
        if response.status_code == 202: # 202 Accepted
            data = response.json()
            st.session_state.job_id = data['job_id']
            st.session_state.job_status = data['status']
            st.success(f"Clusterização iniciada! Job ID: {st.session_state.job_id}")
            time.sleep(1) # Pequena pausa visual
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

current_job_id = st.session_state.job_id

if current_job_id:
    st.info(f"Monitorando Job ID: **{current_job_id}**")
    
    # Função para verificar o status e atualizar o estado da sessão
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
            
    # Checa o status se o job não estiver concluído ou com erro
    if st.session_state.job_status not in ["CONCLUÍDO", "ERRO", "ERRO - ID não encontrado", "ERRO - Falha na Conexão Flask"]:
        check_status() # Chama a verificação
        
    st.subheader(f"Status Atual: {st.session_state.job_status}")
    
    # Se o status ainda é "EM PROGRESSO", continua o refresh automático
    if st.session_state.job_status == "EM PROGRESSO":
        st.progress(0.5, text="Processamento da IA em andamento. Aguardando...")
        # Recarrega a página automaticamente a cada 3 segundos
        time.sleep(3) 
        st.experimental_rerun()
    elif st.session_state.job_status == "CONCLUÍDO":
        st.success("✅ Clusterização Concluída! Pronto para Visualizar.")
    

# --- Sessão 3: Visualização dos Resultados ---

st.header("3. Visualização dos Resultados")

if st.session_state.job_status == "CONCLUÍDO" and st.session_state.clustering_result is None:
    try:
        # Busca os resultados finais ordenados (que seriam usados pelo Java)
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
    
    # Exibe os dados em formato de tabela
    pasta_data = []
    for pasta in result['pastas_ordenadas']:
        arquivos = result['conteudo_ordenado'].get(pasta, [])
        pasta_data.append({
            "Pasta (Cluster)": pasta,
            "Total de Imagens": len(arquivos),
            "Exemplo de Imagens": ", ".join(arquivos[:3]) + ("..." if len(arquivos) > 3 else "")
        })
    
    st.dataframe(pd.DataFrame(pasta_data), use_container_width=True)

    st.markdown("---")
    st.subheader("Conteúdo Detalhado para a Busca Binária (Próxima Fase)")
    
    # Opcional: Mostrar o JSON completo
    with st.expander("Ver JSON Completo (Dados Ordenados)"):
        st.code(json.dumps(result, indent=2))
        st.caption("Este é o formato de dados EXATAMENTE como o Java precisaria para a Busca Binária eficiente.")