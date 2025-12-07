import os, uuid, shutil, threading, requests
from flask import Flask, jsonify, request
from functools import wraps
from io import BytesIO 
from image_processor import run_clustering_on_files, get_features_single
from werkzeug.utils import secure_filename # SEGURANÇA: Import necessário

app = Flask(__name__)

JAVA_API = os.getenv("JAVA_API_URL", "http://localhost:8080")
API_KEY = os.getenv("API_SECRET_KEY", "SCI-BDI-SECRET-KEY-2025")
UPLOAD_FOLDER = 'temp_uploads'
if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)

job_statuses = {} 

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.headers.get('X-API-KEY') == API_KEY: return f(*args, **kwargs)
        return jsonify({"error": "Acesso Negado"}), 401
    return decorated

@app.route('/clusterizar', methods=['POST'])
@require_api_key
def start_job():
    if 'images' not in request.files: return jsonify({"error": "No images"}), 400
    files = request.files.getlist('images')
    
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_FOLDER, job_id)
    os.makedirs(job_dir)
    
    paths = []
    for f in files:
        # SEGURANÇA: Sanitização do nome do arquivo (OWASP)
        # Transforma "../hack.exe" em "hack.exe"
        safe_name = secure_filename(f.filename)
        
        # Garante que o arquivo tenha nome (caso secure_filename retorne vazio)
        if not safe_name: safe_name = f"image_{uuid.uuid4().hex[:8]}.jpg"
            
        p = os.path.join(job_dir, safe_name)
        f.save(p)
        paths.append(p)
        
    job_statuses[job_id] = {"status": "EM PROGRESSO", "resultado": None}
    
    def worker(jid, pths, jdir):
        try:
            # Chama o processador padrão (apenas conteúdo)
            res, centroids = run_clustering_on_files(pths)
            
            if centroids: 
                requests.post(f"{JAVA_API}/build", json=centroids, headers={"X-API-KEY": API_KEY})
                
            job_statuses[jid]["status"] = "CONCLUÍDO"
            job_statuses[jid]["resultado"] = res
        except Exception as e:
            print(f"Erro: {e}")
            job_statuses[jid]["status"] = "ERRO"
            job_statuses[jid]["resultado"] = str(e)
        finally: shutil.rmtree(jdir)
            
    threading.Thread(target=worker, args=(job_id, paths, job_dir)).start()
    return jsonify({"job_id": job_id, "status": "Iniciado"}), 202

@app.route('/status/<jid>', methods=['GET'])
@require_api_key
def status(jid): return jsonify({"status": job_statuses.get(jid, {}).get("status", "404")})

@app.route('/pastas/<jid>', methods=['GET'])
@require_api_key
def result(jid): return jsonify(job_statuses.get(jid, {}).get("resultado", {}))

@app.route('/search', methods=['POST'])
@require_api_key
def search():
    try:
        vec = get_features_single(BytesIO(request.files['image'].read()))
        if not vec: return jsonify({"error": "Bad Image"}), 400
        res = requests.post(f"{JAVA_API}/search", json={"imageVector": vec}, headers={"X-API-KEY": API_KEY})
        return jsonify(res.json())
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
@require_api_key
def history():
    try:
        return jsonify(requests.get(f"{JAVA_API}/history", headers={"X-API-KEY": API_KEY}).json())
    except: return jsonify([])

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)