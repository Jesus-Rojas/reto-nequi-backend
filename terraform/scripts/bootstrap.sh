#!/bin/bash
set -euo pipefail
exec > /var/log/user-data.log 2>&1

echo "==> Actualizando paquetes..."
apt-get update -y
apt-get upgrade -y

echo "==> Instalando dependencias..."
apt-get install -y ca-certificates curl gnupg git

echo "==> Instalando Docker..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io

systemctl enable docker
systemctl start docker

echo "==> Clonando repositorio..."
git clone --recurse-submodules ${repo_url} /opt/app
cd /opt/app/backend

echo "==> Creando directorio de datos persistentes..."
mkdir -p /opt/nequi-data

echo "==> Construyendo y levantando el contenedor del backend..."
docker build -t nequi-backend .

docker run -d \
  --name nequi-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  -v /opt/nequi-data:/app/data \
  -e DATABASE_URL=sqlite:///./data/messages.db \
  -e API_KEY=${app_api_key} \
  -e DEBUG=false \
  -e RATE_LIMIT_PER_MINUTE=${rate_limit_per_minute} \
  nequi-backend

echo "==> Bootstrap del backend completado."
