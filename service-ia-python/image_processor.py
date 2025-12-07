import os
import numpy as np
from PIL import Image
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import img_to_array
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import normalize

TARGET_SIZE = (224, 224)

# --- CARREGAMENTO DA IA ---
# ResNet50 completa para extração profunda de características (shapes, textures, objects)
base_model = ResNet50(weights='imagenet', include_top=True)
# Camada de pooling (2048 dimensões) - Onde "mora" a semântica da imagem
feature_extractor = Model(inputs=base_model.input, outputs=base_model.get_layer('avg_pool').output)

print("IA Carregada: ResNet50 (Fine-Tuned for Precision)")

# --- Utilitários ---
def load_and_preprocess(paths):
    images, valid = [], []
    for path in paths:
        try:
            img = Image.open(path).convert("RGB").resize(TARGET_SIZE)
            arr = img_to_array(img)
            arr = np.expand_dims(arr, axis=0)
            arr = preprocess_input(arr)
            images.append(arr)
            valid.append(path)
        except: pass
    if not images: return None, []
    return np.vstack(images), valid

def get_color_features(paths):
    """Extrai histograma de cor para diferenciar ambientes (ex: fundo branco vs grama)"""
    color_feats = []
    for path in paths:
        try:
            img = Image.open(path).convert("RGB").resize((64, 64))
            arr = np.array(img)
            # Histograma 4x4x4 (64 dimensões)
            hist, _ = np.histogramdd(arr.reshape(-1, 3), bins=(4, 4, 4), range=((0, 256), (0, 256), (0, 256)))
            hist = hist.flatten() / (hist.sum() + 1e-6)
            color_feats.append(hist)
        except:
            color_feats.append(np.zeros(64))
    return np.array(color_feats)

def get_features_single(img_bytes):
    try:
        # Pipeline para uma única imagem (Busca)
        img = Image.open(img_bytes).convert("RGB")
        
        # 1. Semântica
        img_resized = img.resize(TARGET_SIZE)
        arr = img_to_array(img_resized)
        arr = np.expand_dims(arr, axis=0)
        arr = preprocess_input(arr)
        sem_feat = feature_extractor.predict(arr)
        sem_feat = normalize(sem_feat, axis=1, norm='l2')
        
        # 2. Cor
        img_small = img.resize((64, 64))
        arr_small = np.array(img_small)
        hist, _ = np.histogramdd(arr_small.reshape(-1, 3), bins=(4, 4, 4), range=((0, 256), (0, 256), (0, 256)))
        col_feat = hist.flatten() / (hist.sum() + 1e-6)
        col_feat = col_feat.reshape(1, -1)
        # Aplica o mesmo peso reduzido
        col_feat = normalize(col_feat, axis=1, norm='l2') * 0.25
        
        final_feat = np.hstack([sem_feat, col_feat])
        return final_feat[0].tolist()
    except: return None

# --- Auto-K Dinâmico e Sensível ---
def find_best_k(features, num_images):
    if num_images < 2: return 1
    if num_images <= 3: return num_images # Se tem 3 fotos, separa as 3 se precisar
    
    best_k = 2
    best_score = -1
    
    # AJUSTE: Permite mais grupos. 
    # Antes o max era 5. Agora é metade das imagens ou 10 (o que for menor).
    # Ex: Se mandar 20 fotos, ele pode criar até 10 grupos se forem muito diferentes.
    max_k = min(10, num_images - 1)
    
    # Loop de teste de agrupamento
    for k in range(2, max_k + 1):
        # n_init=30: Tenta 30 vezes achar os melhores centros (antes era 10)
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=30).fit(features)
        labels = kmeans.labels_
        
        # Penaliza grupos com 1 só item se tivermos muitas imagens (ruído)
        # Mas permite se tivermos poucas imagens
        unique, counts = np.unique(labels, return_counts=True)
        if num_images > 6 and min(counts) < 2:
            score_penalty = 0.1 # Penalidade leve
        else:
            score_penalty = 0.0
            
        if len(set(labels)) < 2: continue
        
        score = silhouette_score(features, labels) - score_penalty
        
        # AJUSTE: Prefere dividir mais (Over-clustering é melhor que misturar)
        # Se o score do K maior for pelo menos 90% do score do K menor, prefere o maior.
        if score > best_score or (score > best_score * 0.90 and k > best_k):
            best_k = k
            best_score = score
            
    print(f"Auto-K escolheu: {best_k} grupos (Score: {best_score:.3f})")
    return best_k

# --- Pipeline Principal ---
def run_clustering_on_files(paths):
    # 1. Carregamento
    imgs, valid = load_and_preprocess(paths)
    if imgs is None: return {}, {}
    
    # 2. Extração Semântica (PESO TOTAL)
    print("Extraindo semântica (ResNet)...")
    semantic_feats = feature_extractor.predict(imgs)
    semantic_feats = normalize(semantic_feats, axis=1, norm='l2')
    
    # 3. Extração de Cor (PESO REDUZIDO)
    # Baixamos de 0.6 para 0.25. 
    # A cor agora só serve para desempatar (ex: gato preto vs gato branco).
    # A forma (ResNet) domina a decisão.
    print("Extraindo cores...")
    color_feats = get_color_features(valid)
    color_feats = normalize(color_feats, axis=1, norm='l2') * 0.25 
    
    # 4. Fusão
    final_feats = np.hstack([semantic_feats, color_feats])
    
    # 5. Clusterização
    k = find_best_k(final_feats, len(valid))
    
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=30)
    labels = kmeans.fit_predict(final_feats)
    
    # 6. Organização
    clusters, centroids = {}, {}
    temp = {i: [] for i in range(k)}
    
    for i, lbl in enumerate(labels):
        temp[lbl].append(valid[i])
        
    group_counter = 1
    for lbl, group_paths in temp.items():
        if not group_paths: continue
        
        cluster_name = f"Grupo {group_counter}"
        group_counter += 1
            
        clusters[cluster_name] = sorted([os.path.basename(p) for p in group_paths])
        centroids[cluster_name] = kmeans.cluster_centers_[lbl].tolist()
        
    return {"pastas_ordenadas": sorted(clusters.keys()), "conteudo_ordenado": clusters}, centroids