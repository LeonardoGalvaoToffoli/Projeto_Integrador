import os
import numpy as np
from PIL import Image
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.models import Model
from sklearn.cluster import KMeans

# --- 1. CONFIGURAÇÕES GLOBAIS ---
IMAGE_DIR = 'images_to_process'
OUTPUT_DIR = 'clustered_images'
NUM_CLUSTERS = 4
TARGET_SIZE = (224, 224)

# Garante que as pastas existam
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
for i in range(NUM_CLUSTERS):
    if not os.path.exists(os.path.join(OUTPUT_DIR, f'cluster_{i}')):
        os.makedirs(os.path.join(OUTPUT_DIR, f'cluster_{i}'))

# --- 2. CARREGAMENTO E PRÉ-PROCESSAMENTO ---

def load_and_preprocess_images(image_paths):
    images = []
    for path in image_paths:
        try:
            img = Image.open(path).convert("RGB") 
            img = img.resize(TARGET_SIZE) 
            img_array = np.array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array) 
            images.append(img_array)
        except Exception as e:
            print(f"Erro ao processar imagem {path}: {e}")
            continue
    return np.vstack(images), image_paths

# --- 3. EXTRAÇÃO DE CARACTERÍSTICAS (CNN) ---

# CARREGA O MODELO VGG16 GLOBALMENTE
base_model = VGG16(weights='imagenet', include_top=False)
feature_extractor = Model(inputs=base_model.input, outputs=base_model.get_layer('block5_pool').output)
print("Modelo VGG16 carregado globalmente.")

def extract_features(preprocessed_images):
    print("Extraindo features...")
    features = feature_extractor.predict(preprocessed_images)
    features_flattened = features.reshape(features.shape[0], -1)
    return features_flattened

def get_features_for_single_image(image_file):
    """Recebe um arquivo de imagem (ex: de upload) e retorna seu vetor de features."""
    try:
        img = Image.open(image_file).convert("RGB")
        img = img.resize(TARGET_SIZE)
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        features = feature_extractor.predict(img_array)
        features_flattened = features.reshape(features.shape[0], -1)
        
        return features_flattened[0].tolist() # Retorna como lista p/ JSON
    except Exception as e:
        print(f"Erro ao processar imagem única: {e}")
        return None

# --- 4. CLUSTERIZAÇÃO (K-MEANS) ---

def cluster_features(features):
    print(f"Aplicando K-Means com K={NUM_CLUSTERS}...")
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42, n_init=10)
    kmeans.fit(features)
    
    # Retorna os rótulos E os centróides
    return kmeans.labels_, kmeans.cluster_centers_

# --- 5. ORGANIZAÇÃO (Opcional) ---
def organize_images(image_paths, labels):
    # Seu código original aqui...
    pass

# --- EXECUÇÃO PRINCIPAL ---

def run_clustering():
    all_image_paths = [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not all_image_paths:
        return {}, {} # Retorna dicionários vazios se não houver imagens

    processed_images, valid_paths = load_and_preprocess_images(all_image_paths)
    features = extract_features(processed_images)
    
    # Pega os rótulos E os centróides
    labels, centers = cluster_features(features)
    
    # (Opcional) organize_images(valid_paths, labels)
    
    # 1. Prepara o JSON para o Streamlit (como antes)
    clusters = {}
    for i, path in enumerate(valid_paths):
        cluster_label = f'cluster_{labels[i]}'
        filename = os.path.basename(path)
        
        if cluster_label not in clusters:
            clusters[cluster_label] = []
        clusters[cluster_label].append(filename)

    data_for_streamlit = {
        "pastas_ordenadas": sorted(list(clusters.keys())),
        "conteudo_ordenado": {k: sorted(v) for k, v in clusters.items()}
    }

    # 2. Prepara o JSON de centróides para o Java
    centroids_map = {}
    for i in range(NUM_CLUSTERS):
        cluster_name = f'cluster_{i}'
        centroids_map[cluster_name] = centers[i].tolist() # Converte array numpy para lista
    
    # 6. Retorna AMBOS os dicionários
    return data_for_streamlit, centroids_map