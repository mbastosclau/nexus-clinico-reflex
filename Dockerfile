FROM python:3.11-slim

WORKDIR /app

# Instala as dependências de sistema que o Reflex exige no Linux (Node.js, unzip, curl)
RUN apt-get update && apt-get install -y curl unzip nodejs npm

# Copia e instala as bibliotecas Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código do projeto Nexus Clínico para o servidor
COPY . .

# Comando de arranque do servidor em modo de produção
CMD ["reflex", "run", "--env", "prod"]