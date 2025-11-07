import os
import numpy as np
import cv2 # OpenCV para manipulação de imagem
from PIL import Image # Pillow para manipulação de imagem
from tensorflow.keras.applications.vgg16 import VGG16, preprocess_input
from tensorflow.keras.models import Model
from sklearn.cluster import KMeans

# --- 1. CONFIGURAÇÕES GLOBAIS ---
IMAGE_DIR = 'images_to_process' # Crie uma pasta com suas imagens
OUTPUT_DIR = 'clustered_images'
NUM_CLUSTERS = 4 # Ex: praia, deserto, floresta, cidade
TARGET_SIZE = (224, 224) # Tamanho esperado pelo modelo VGG16

# Garante que as pastas existam
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
for i in range(NUM_CLUSTERS):
    if not os.path.exists(os.path.join(OUTPUT_DIR, f'cluster_{i}')):
        os.makedirs(os.path.join(OUTPUT_DIR, f'cluster_{i}'))

# --- 2. CARREGAMENTO E PRÉ-PROCESSAMENTO DE IMAGENS ---

def load_and_preprocess_images(image_paths):
    """Carrega as imagens, redimensiona e pré-processa para a CNN."""
    images = []
    for path in image_paths:
        try:
            # Carrega a imagem e garante que é RGB
            img = Image.open(path).convert("RGB") 
            # Redimensiona para o tamanho de entrada do VGG16
            img = img.resize(TARGET_SIZE) 
            # Converte para array numpy
            img_array = np.array(img)
            # Adiciona dimensão de batch
            img_array = np.expand_dims(img_array, axis=0)
            # Pré-processa a imagem de acordo com o VGG16 (normalização)
            img_array = preprocess_input(img_array) 
            images.append(img_array)
        except Exception as e:
            print(f"Erro ao processar imagem {path}: {e}")
            continue
            
    # Concatena todas as imagens em um único array (N, H, W, C)
    return np.vstack(images), image_paths

# --- 3. EXTRAÇÃO DE CARACTERÍSTICAS COM CNN (VGG16) ---

def extract_features(preprocessed_images):
    """Carrega o VGG16 e usa a penúltima camada para extrair features (embeddings)."""
    
    # Carrega o VGG16 pré-treinado na base ImageNet
    # include_top=False: remove a camada final de classificação (o que queremos)
    base_model = VGG16(weights='imagenet', include_top=False)
    
    # Criamos o modelo de feature extraction a partir da camada 'block5_pool'
    # que é a penúltima camada de pooling, rica em features de alto nível.
    feature_extractor = Model(inputs=base_model.input, outputs=base_model.get_layer('block5_pool').output)
    
    print("Extraindo features...")
    features = feature_extractor.predict(preprocessed_images)
    
    # Achata as features 3D em vetores 1D (embeddings) para o K-Means
    # (N, 7, 7, 512) -> (N, 7*7*512)
    features_flattened = features.reshape(features.shape[0], -1)
    
    return features_flattened

# --- 4. CLUSTERIZAÇÃO COM K-MEANS ---

def cluster_features(features):
    """Aplica o algoritmo K-Means nos vetores de características."""
    print(f"Aplicando K-Means com K={NUM_CLUSTERS}...")
    # Inicializa e treina o K-Means
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42, n_init=10)
    kmeans.fit(features)
    
    # Retorna os rótulos de cluster para cada imagem
    return kmeans.labels_

# --- 5. ORGANIZAÇÃO DAS IMAGENS EM PASTAS ---

def organize_images(image_paths, labels):
    """Move/Copia as imagens para as pastas dos clusters."""
    print("Organizando imagens nas pastas...")
    
    for i, path in enumerate(image_paths):
        # Determina a pasta de destino
        cluster_label = labels[i]
        filename = os.path.basename(path)
        destination_folder = os.path.join(OUTPUT_DIR, f'cluster_{cluster_label}')
        destination_path = os.path.join(destination_folder, filename)
        
        # Simplesmente copia o arquivo para a pasta de destino
        import shutil
        try:
            shutil.copy(path, destination_path)
        except Exception as e:
            print(f"Não foi possível copiar o arquivo {filename}: {e}")
            
    print("Organização concluída!")

# --- EXECUÇÃO PRINCIPAL ---

def run_clustering():
    # 1. Encontra todos os arquivos de imagem
    all_image_paths = [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    # ... (Resto da lógica de carregamento e extração) ...
    processed_images, valid_paths = load_and_preprocess_images(all_image_paths)
    features = extract_features(processed_images)
    labels = cluster_features(features)
    
    # --- NOVO TRECHO: Construção do resultado ordenado ---
    clusters = {}
    for i, path in enumerate(valid_paths):
        cluster_label = f'cluster_{labels[i]}'
        filename = os.path.basename(path)
        
        if cluster_label not in clusters:
            clusters[cluster_label] = []
        clusters[cluster_label].append(filename)

    # 4. Retorna os dados E move/copia os arquivos (se ainda quiser o output no disco)
    # organize_images(valid_paths, labels) # Chama a função de cópia
    
    # Prepara o JSON para o Java: dados ORDENADOS para a busca binária
    data_for_java = {
        "pastas_ordenadas": sorted(list(clusters.keys())),
        "conteudo_ordenado": {k: sorted(v) for k, v in clusters.items()}
    }

    return data_for_java
