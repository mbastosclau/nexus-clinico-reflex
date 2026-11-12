FROM python:3.11-slim

WORKDIR /app

# Instala as ferramentas base (curl e unzip)
RUN apt-get update && apt-get install -y curl unzip

# Adiciona o repositório oficial da versão 22 e instala o Node.js mais recente
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs

# Copia e instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto para o servidor
COPY . .

# Comando de arranque do servidor em modo de produção
CMD ["reflex", "run", "--env", "prod"]