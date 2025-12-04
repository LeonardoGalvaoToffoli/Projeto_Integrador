FROM python:3.10-slim

WORKDIR /app

# Instala dependências do sistema necessárias para o Tensorflow/OpenCV (se precisar)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY . .

# Expõe as portas (5000 para Flask, 8501 para Streamlit)
EXPOSE 5000 8501

# Script para rodar Flask e Streamlit simultaneamente
CMD ["sh", "-c", "python api_server.py & streamlit run app_streamlit.py --server.port=8501 --server.address=0.0.0.0"]