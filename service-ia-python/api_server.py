import os
import uuid
import threading
from flask import Flask, jsonify, request
import requests # NOVO
from io import BytesIO # NOVO

# Importa as funções ATUALIZADAS
from image_processor import run_clustering, get_features_for_single_image

app = Flask(__name__)

job_statuses = {} 
JAVA_API_URL = "http://localhost:8080" # URL do seu serviço Java

# --- ENDPOINT 1: Inicia a Clusterização (Modificado) ---
@app.route('/clusterizar', methods=['POST'])
def start_clustering_job():
    job_id = str(uuid.uuid4())
    job_statuses[job_id] = {"status": "EM PROGRESSO", "resultado": None}
    
    def worker(job_id):
        print(f"Job {job_id} - Processamento da IA iniciado...")
        try:
            # 1. CHAMA A FUNÇÃO DE IA (agora retorna 2 coisas)
            results_json, centroids_map = run_clustering() 
            
            # 2. NOVO: Envia os centróides para o serviço Java
            if centroids_map:
                try:
                    print(f"Job {job_id} - Enviando {len(centroids_map)} centróides para o serviço Java em {JAVA_API_URL}/build...")
                    response = requests.post(f"{JAVA_API_URL}/build", json=centroids_map, timeout=10)
                    
                    if response.status_code == 200:
                        print(f"Job {job_id} - Índice Java construído com sucesso.")
                    else:
                        print(f"Job {job_id} - ERRO ao construir índice Java. Status: {response.status_code}, Msg: {response.text}")
                
                except requests.exceptions.ConnectionError:
                    print(f"\nJob {job_id} - ERRO DE CONEXÃO: Não foi possível conectar ao serviço Java em {JAVA_API_URL}.")
                    print("Verifique se o serviço 'service-busca-java' (Spring Boot) está rodando na porta 8080.\n")
                except Exception as e_java:
                     print(f"Job {job_id} - ERRO desconhecido ao enviar para o Java: {e_java}")
            else:
                print(f"Job {job_id} - Nenhum centróide gerado. O envio para o Java foi ignorado.")

            # 3. Salva o resultado (para o Streamlit)
            job_statuses[job_id]["status"] = "CONCLUÍDO"
            job_statuses[job_id]["resultado"] = results_json
            print(f"Job {job_id} - CONCLUÍDO.")

        except Exception as e:
            job_statuses[job_id]["status"] = "ERRO"
            job_statuses[job_id]["resultado"] = str(e)
            print(f"Job {job_id} - ERRO GERAL: {e}")

    thread = threading.Thread(target=worker, args=(job_id,))
    thread.start()

    return jsonify({
        "job_id": job_id, 
        "status": "Processamento de IA iniciado em segundo plano.",
        "monitoramento": f"/status/{job_id}"
    }), 202

# --- ENDPOINT 2: Verifica o Status (Sem Alterações) ---
@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    if job_id not in job_statuses:
        return jsonify({"message": "Job ID não encontrado"}), 404
    return jsonify({"status": job_statuses[job_id]["status"]}), 200

# --- ENDPOINT 3: Entrega Resultado p/ Streamlit (Sem Alterações) ---
@app.route('/pastas/<job_id>', methods=['GET'])
def get_folders_content(job_id):
    if job_id not in job_statuses:
        return jsonify({"message": "Job ID não encontrado"}), 404
    job = job_statuses[job_id]
    if job["status"] != "CONCLUÍDO":
        return jsonify({"message": "Aguarde, processamento não concluído.", "status": job["status"]}), 409
    return jsonify(job["resultado"]), 200


# --- NOVO ENDPOINT 4: Busca por Imagem Similar ---
@app.route('/search', methods=['POST'])
def search_similar_image():
    if 'image' not in request.files:
        return jsonify({"error": "Nenhum arquivo de imagem enviado"}), 400
    
    file = request.files['image']
    
    try:
        # 1. Extrai o vetor de features da imagem enviada
        image_in_memory = BytesIO(file.read()) 
        image_vector = get_features_for_single_image(image_in_memory)
        
        if image_vector is None:
             return jsonify({"error": "Não foi possível processar a imagem"}), 500

        # 2. Prepara o JSON para o serviço Java
        java_payload = {
            "imageVector": image_vector
        }

        # 3. Consulta o serviço Java
        try:
            response = requests.post(f"{JAVA_API_URL}/search", json=java_payload, timeout=10)
            if response.status_code == 200:
                return jsonify(response.json()), 200
            else:
                return jsonify({"error": "Erro no serviço Java de busca", "details": response.text}), 500
        except requests.exceptions.ConnectionError:
            return jsonify({"error": f"Não foi possível conectar ao serviço Java em {JAVA_API_URL}"}), 503
    except Exception as e:
        return jsonify({"error": f"Erro ao processar imagem: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)