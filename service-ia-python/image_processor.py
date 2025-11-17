import os
import numpy as np
from PIL import Image
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import GlobalAveragePooling2D
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize # <--- Importação Essencial

# --- Configurações ---
IMAGE_DIR = 'images_to_process'
OUTPUT_DIR = 'clustered_images'
NUM_CLUSTERS = 4
TARGET_SIZE = (224, 224)

# Inicialização de diretórios
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
for i in range(NUM_CLUSTERS):
    cluster_dir = os.path.join(OUTPUT_DIR, f'cluster_{i}')
    if not os.path.exists(cluster_dir):
        os.makedirs(cluster_dir)

# --- Carregamento do Modelo (VGG16 com Pooling) ---

base_model = VGG16(weights='imagenet', include_top=False)

# Global Average Pooling reduz o vetor para 512 dimensões e foca no conteúdo semântico
x = base_model.get_layer('block5_pool').output
x = GlobalAveragePooling2D()(x)

feature_extractor = Model(inputs=base_model.input, outputs=x)
print("Modelo VGG16 carregado com Otimização (Global Pooling).")

# --- Funções de Processamento ---

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
            print(f"Falha ao processar imagem {path}: {e}")
            continue
    return np.vstack(images), image_paths

def extract_features(preprocessed_images):
    """
    Extrai features e aplica NORMALIZAÇÃO L2.
    Isso é crucial para diferenciar imagens com paletas de cores similares (Praia vs Deserto).
    """
    print("Iniciando extração de características...")
    features = feature_extractor.predict(preprocessed_images)
    features_flattened = features.reshape(features.shape[0], -1)
    
    # NORMALIZAÇÃO: Transforma os vetores para terem o mesmo "tamanho" matemático.
    # Isso faz o K-Means funcionar baseando-se na direção (conteúdo) e não na intensidade.
    return normalize(features_flattened, axis=1, norm='l2')

def get_features_for_single_image(image_file):
    try:
        img = Image.open(image_file).convert("RGB")
        img = img.resize(TARGET_SIZE)
        img_array = np.array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        features = feature_extractor.predict(img_array)
        features_flattened = features.reshape(features.shape[0], -1)
        
        # Aplica a mesma normalização na busca!
        features_normalized = normalize(features_flattened, axis=1, norm='l2')
        
        return features_normalized[0].tolist()
    except Exception as e:
        print(f"Erro no processamento unitário: {e}")
        return None

def cluster_features(features):
    print(f"Executando K-Means com {NUM_CLUSTERS} clusters...")
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42, n_init=10)
    kmeans.fit(features)
    return kmeans.labels_, kmeans.cluster_centers_

def run_clustering():
    all_image_paths = [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not all_image_paths:
        return {}, {}
    
    processed_images, valid_paths = load_and_preprocess_images(all_image_paths)
    features = extract_features(processed_images)
    labels, centers = cluster_features(features)
    
    clusters = {}
    for i, path in enumerate(valid_paths):
        cluster_label = f'cluster_{labels[i]}'
        filename = os.path.basename(path)
        
        if cluster_label not in clusters:
            clusters[cluster_label] = []
        clusters[cluster_label].append(filename)

    data_result = {
        "pastas_ordenadas": sorted(list(clusters.keys())),
        "conteudo_ordenado": {k: sorted(v) for k, v in clusters.items()}
    }

    centroids_map = {}
    for i in range(NUM_CLUSTERS):
        cluster_name = f'cluster_{i}'
        centroids_map[cluster_name] = centers[i].tolist()
    
    return data_result, centroids_map