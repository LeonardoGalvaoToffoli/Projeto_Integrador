import os
import uuid
import threading
from flask import Flask, jsonify, request
import requests
from io import BytesIO 
from image_processor import run_clustering, get_features_for_single_image

app = Flask(__name__)

# Cache em memória para controle de estado dos jobs.
job_statuses = {} 

# Endereço do serviço de Estrutura de Dados (Java)
JAVA_API_URL = "http://localhost:8080"

@app.route('/clusterizar', methods=['POST'])
def start_clustering_job():
    """
    Inicia o processo de clusterização de forma assíncrona.
    Utiliza threads para evitar bloqueio da API durante o processamento pesado de IA.
    """
    job_id = str(uuid.uuid4())
    job_statuses[job_id] = {"status": "EM PROGRESSO", "resultado": None}
    
    def worker(job_id):
        print(f"Job {job_id} - Iniciado.")
        try:
            # Execução do pipeline de IA
            results_json, centroids_map = run_clustering() 
            
            # Sincronização com o Microsserviço Java:
            # Envia os centróides calculados para indexação na tabela hash.
            if centroids_map:
                try:
                    print(f"Job {job_id} - Enviando dados para indexação Java...")
                    response = requests.post(f"{JAVA_API_URL}/build", json=centroids_map, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"Job {job_id} - Indexação concluída com sucesso.")
                    else:
                        print(f"Job {job_id} - Falha na indexação. Código: {response.status_code}")
                
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

    return jsonify({
        "job_id": job_id, 
        "status": "Processamento iniciado.",
        "monitoramento": f"/status/{job_id}"
    }), 202

@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Monitora o estado atual de um job de processamento."""
    if job_id not in job_statuses:
        return jsonify({"message": "Job não encontrado"}), 404
    return jsonify({"status": job_statuses[job_id]["status"]}), 200

@app.route('/pastas/<job_id>', methods=['GET'])
def get_folders_content(job_id):
    """Retorna os resultados organizados após a conclusão do job."""
    if job_id not in job_statuses:
        return jsonify({"message": "Job não encontrado"}), 404
    job = job_statuses[job_id]
    if job["status"] != "CONCLUÍDO":
        return jsonify({"message": "Processamento em andamento.", "status": job["status"]}), 409
    return jsonify(job["resultado"]), 200

@app.route('/search', methods=['POST'])
def search_similar_image():
    """
    Endpoint de busca por similaridade.
    Fluxo:
    1. Recebe imagem -> Extrai vetor (Python).
    2. Envia vetor -> Busca vizinho mais próximo (Java).
    3. Retorna cluster identificado.
    """
    if 'image' not in request.files:
        return jsonify({"error": "Arquivo ausente"}), 400
    
    file = request.files['image']
    
    try:
        image_in_memory = BytesIO(file.read()) 
        image_vector = get_features_for_single_image(image_in_memory)
        
        if image_vector is None:
             return jsonify({"error": "Falha no processamento da imagem"}), 500

        java_payload = {
            "imageVector": image_vector
        }

        try:
            response = requests.post(f"{JAVA_API_URL}/search", json=java_payload, timeout=10)
            if response.status_code == 200:
                return jsonify(response.json()), 200
            else:
                return jsonify({"error": "Erro no serviço de busca", "details": response.text}), 500
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Serviço de busca indisponível"}), 503
    except Exception as e:
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)