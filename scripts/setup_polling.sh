#!/usr/bin/env bash
set -Eeuo pipefail

# ViranumPro - automated setup for Docker (Polling mode)
# - Installs official Docker + buildx plugin on Ubuntu/Debian
# - Builds Docker image (Dockerfile.dev)
# - Ensures .env exists and TELEGRAM_BOT_TOKEN is set
# - Runs the container in long-polling mode

PROJECT_NAME="ViranumPro"
IMAGE_NAME="viranumpro-dev:latest"
CONTAINER_NAME="viranumpro-dev"
ENV_FILE=".env"
DOCKERFILE="Dockerfile.dev"

msg() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*" >&2; }
die() { echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

require_root_or_sudo() {
  if [ "${EUID:-$(id -u)}" -ne 0 ]; then
    if command_exists sudo; then
      SUDO="sudo"
    else
      die "This script requires root or sudo. Please run as root or install sudo."
    fi
  else
    SUDO=""
  fi
}

check_network() {
  if ! curl -fsSL https://download.docker.com/ >/dev/null 2>&1; then
    warn "Unable to reach download.docker.com. Checking alternative..."
    if ! curl -fsSL https://www.google.com/ >/dev/null 2>&1; then
      die "No internet connectivity detected. Please check network/DNS."
    fi
  fi
}

install_docker_official() {
  if command_exists docker; then
    msg "Docker is already installed: $(docker --version | tr -d '\n')"
  else
    msg "Installing Docker from official repository..."
    $SUDO apt-get update -y
    $SUDO apt-get install -y ca-certificates curl gnupg lsb-release

    $SUDO install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    $SUDO chmod a+r /etc/apt/keyrings/docker.gpg

    # Detect Ubuntu codename (fallback to noble)
    if [ -r /etc/os-release ]; then
      . /etc/os-release
      CODENAME="${UBUNTU_CODENAME:-${VERSION_CODENAME:-noble}}"
      DISTRO_ID="${ID:-ubuntu}"
    else
      CODENAME="noble"
      DISTRO_ID="ubuntu"
    fi

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \nhttps://download.docker.com/linux/${DISTRO_ID} ${CODENAME} stable" | $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null

    $SUDO apt-get update -y
    $SUDO apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Enable/start docker service if systemd is available
    if command_exists systemctl; then
      $SUDO systemctl enable --now docker || true
    else
      $SUDO service docker start || true
    fi
  fi

  # Verify docker works
  docker version >/dev/null 2>&1 || die "Docker CLI/Daemon not working properly."

  # Verify buildx (provided by docker-buildx-plugin)
  if docker buildx version >/dev/null 2>&1; then
    msg "Docker buildx is available."
  else
    warn "Docker buildx is not available. Falling back to legacy build."
  fi

  # Verify docker compose plugin
  if docker compose version >/dev/null 2>&1; then
    msg "Docker Compose is available: $(docker compose version | head -n1)"
  else
    warn "Docker Compose plugin not available. Not required for this script."
  fi
}

ensure_env_file() {
  if [ ! -f "$ENV_FILE" ]; then
    msg "Creating $ENV_FILE from .env.example (if available) or minimal template..."
    if [ -f ".env.example" ]; then
      cp .env.example "$ENV_FILE"
    else
      cat > "$ENV_FILE" <<'EOF'
TELEGRAM_BOT_TOKEN=
# Optional
FIVESIM_TOKEN=
LOG_LEVEL=INFO
EOF
    fi
  fi

  # If TELEGRAM_BOT_TOKEN is provided via environment, inject/update it
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ]; then
    if grep -qE '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE"; then
      $SUDO sed -i "s#^TELEGRAM_BOT_TOKEN=.*#TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}#" "$ENV_FILE"
    else
      echo "TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}" | $SUDO tee -a "$ENV_FILE" >/dev/null
    fi
  fi

  # Validate token
  local token
  token=$(grep -E '^TELEGRAM_BOT_TOKEN=' "$ENV_FILE" | head -n1 | cut -d= -f2- || true)
  if [ -z "${token}" ] || [[ "${token}" == "your-telegram-bot-token" ]]; then
    die "Please set TELEGRAM_BOT_TOKEN in $ENV_FILE before continuing."
  fi
}

check_repo_requirements() {
  # Check pydantic version pin to avoid aiogram conflict
  if grep -qE '^pydantic==2\.9\.' requirements.txt 2>/dev/null; then
    die "requirements.txt pins pydantic==2.9.x which conflicts with aiogram 3.7.0. Please set pydantic==2.7.4."
  fi
}

build_image() {
  msg "Building Docker image ($IMAGE_NAME) using $DOCKERFILE..."
  if docker buildx version >/dev/null 2>&1; then
    docker buildx build -f "$DOCKERFILE" -t "$IMAGE_NAME" --load .
  else
    DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker build -f "$DOCKERFILE" -t "$IMAGE_NAME" .
  fi
}

run_container() {
  # Stop/remove existing
  if docker ps -a --format '{{.Names}}' | grep -wq "$CONTAINER_NAME"; then
    msg "Stopping existing container $CONTAINER_NAME..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    msg "Removing existing container $CONTAINER_NAME..."
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
  fi

  msg "Running container $CONTAINER_NAME from image $IMAGE_NAME..."
  docker run -d --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --env-file "$ENV_FILE" \
    "$IMAGE_NAME"

  msg "Container started. Use 'docker logs -f $CONTAINER_NAME' to follow logs."
}

main() {
  msg "Starting $PROJECT_NAME automated setup (Polling mode)..."
  require_root_or_sudo
  check_network
  install_docker_official
  ensure_env_file
  check_repo_requirements
  build_image
  run_container
  msg "Setup completed successfully."
}

main "$@"
