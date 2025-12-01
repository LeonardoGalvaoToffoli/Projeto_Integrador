import os
import uuid
import threading
from flask import Flask, jsonify, request
import requests
from io import BytesIO 
from functools import wraps
from image_processor import run_clustering, get_features_for_single_image

app = Flask(__name__)

# Cache em memória
job_statuses = {} 

# Configurações
JAVA_API_URL = "http://localhost:8080"
API_KEY = "SCI-BDI-SECRET-KEY-2025"  # <--- Chave definida

# --- 1. Decorator de Segurança ---
# Essa função verifica se a chave chegou no request
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-API-KEY') == API_KEY:
            return f(*args, **kwargs)
        else:
            return jsonify({"error": "Acesso Negado: API Key inválida"}), 401
    return decorated_function

# --- Rotas ---

@app.route('/clusterizar', methods=['POST'])
@require_api_key
def start_clustering_job():
    job_id = str(uuid.uuid4())
    job_statuses[job_id] = {"status": "EM PROGRESSO", "resultado": None}
    
    def worker(job_id):
        print(f"Job {job_id} - Iniciado.")
        try:
            results_json, centroids_map = run_clustering() 
            
            # Sincronização com Java
            if centroids_map:
                try:
                    print(f"Job {job_id} - Enviando dados para indexação Java...")
                    
                    # --- 2. ENVIANDO A CHAVE PARA O JAVA ---
                    headers_java = {"X-API-KEY": API_KEY}
                    response = requests.post(f"{JAVA_API_URL}/build", json=centroids_map, headers=headers_java, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"Job {job_id} - Indexação concluída.")
                    else:
                        print(f"Job {job_id} - Falha Java: {response.status_code}")
                
                except requests.exceptions.ConnectionError:
                    print(f"Job {job_id} - Erro: Serviço Java inacessível.")
                except Exception as e_java:
                     print(f"Job {job_id} - Erro de integração: {e_java}")

            job_statuses[job_id]["status"] = "CONCLUÍDO"
            job_statuses[job_id]["resultado"] = results_json
            print(f"Job {job_id} - Finalizado.")

        except Exception as e:
            job_statuses[job_id]["status"] = "ERRO"
            job_statuses[job_id]["resultado"] = str(e)
            print(f"Job {job_id} - Exceção: {e}")

    thread = threading.Thread(target=worker, args=(job_id,))
    thread.start()

    return jsonify({"job_id": job_id, "status": "Processamento iniciado."}), 202

@app.route('/status/<job_id>', methods=['GET'])
@require_api_key
def get_job_status(job_id):
    if job_id not in job_statuses:
        return jsonify({"message": "Job não encontrado"}), 404
    return jsonify({"status": job_statuses[job_id]["status"]}), 200

@app.route('/pastas/<job_id>', methods=['GET'])
@require_api_key
def get_folders_content(job_id):
    if job_id not in job_statuses:
        return jsonify({"message": "Job não encontrado"}), 404
    job = job_statuses[job_id]
    if job["status"] != "CONCLUÍDO":
        return jsonify({"message": "Processamento em andamento.", "status": job["status"]}), 409
    return jsonify(job["resultado"]), 200

@app.route('/search', methods=['POST'])
@require_api_key
def search_similar_image():
    if 'image' not in request.files:
        return jsonify({"error": "Arquivo ausente"}), 400
    
    file = request.files['image']
    
    try:
        image_in_memory = BytesIO(file.read()) 
        image_vector = get_features_for_single_image(image_in_memory)
        
        if image_vector is None:
             return jsonify({"error": "Falha no processamento"}), 500

        java_payload = {"imageVector": image_vector}

        try:
            # --- 3. ENVIANDO A CHAVE PARA O JAVA ---
            headers_java = {"X-API-KEY": API_KEY}
            response = requests.post(f"{JAVA_API_URL}/search", json=java_payload, headers=headers_java, timeout=10)
            
            if response.status_code == 200:
                return jsonify(response.json()), 200
            else:
                return jsonify({"error": "Erro no serviço de busca Java"}), 500
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Serviço de busca indisponível"}), 503
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)