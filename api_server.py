import os
import uuid
import threading
from flask import Flask, jsonify, request

# Importa a função principal do seu módulo de IA
from image_processor import run_clustering # Supondo que a função está no image_processor.py

app = Flask(__name__)

# Simulação de cache/estado de trabalhos assíncronos (CRUCIAL para IA lenta)
# Em produção, use um banco de dados ou Celery
job_statuses = {} 

# --- ENDPOINT 1: Inicia a Clusterização (Assíncrono) ---
@app.route('/clusterizar', methods=['POST'])
def start_clustering_job():
    """
    Inicia o processamento de IA em uma thread separada para não bloquear a API.
    """
    job_id = str(uuid.uuid4())
    job_statuses[job_id] = {"status": "EM PROGRESSO", "resultado": None}
    
    # O processamento pesado da IA roda aqui, fora da thread principal do Flask.
    def worker(job_id):
        print(f"Job {job_id} - Processamento da IA iniciado...")
        try:
            # CHAMA A SUA FUNÇÃO DE IA
            results = run_clustering() 
            
            job_statuses[job_id]["status"] = "CONCLUÍDO"
            job_statuses[job_id]["resultado"] = results
            print(f"Job {job_id} - CONCLUÍDO.")
        except Exception as e:
            job_statuses[job_id]["status"] = "ERRO"
            job_statuses[job_id]["resultado"] = str(e)
            print(f"Job {job_id} - ERRO: {e}")

    # Inicia a thread
    thread = threading.Thread(target=worker, args=(job_id,))
    thread.start()

    return jsonify({
        "job_id": job_id, 
        "status": "Processamento de IA iniciado em segundo plano.",
        "monitoramento": f"/status/{job_id}"
    }), 202

# --- ENDPOINT 2: Verifica o Status do Job ---
@app.route('/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Permite verificar o status (Em Progresso, Concluído, Erro).
    """
    if job_id not in job_statuses:
        return jsonify({"message": "Job ID não encontrado"}), 404
        
    return jsonify({"status": job_statuses[job_id]["status"]}), 200

# --- ENDPOINT 3: Entrega o Resultado para o Módulo Java (Busca Binária) ---
@app.route('/pastas/<job_id>', methods=['GET'])
def get_folders_content(job_id):
    """
    Retorna o JSON ORDENADO que o módulo Java precisa para a Busca Binária.
    """
    if job_id not in job_statuses:
        return jsonify({"message": "Job ID não encontrado"}), 404
        
    job = job_statuses[job_id]

    if job["status"] != "CONCLUÍDO":
        return jsonify({"message": "Aguarde, o processamento da IA ainda não foi concluído.", "status": job["status"]}), 409
    
    # Retorna o resultado ORDENADO
    return jsonify(job["resultado"]), 200

if __name__ == '__main__':
    # Execute a API
    app.run(debug=True, port=5000)