# SD.Next Dockerfile for Vast.ai
# Based on SD.Next official Dockerfile with additional services

# Base image - using SD.Next recommended PyTorch image
FROM pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime

# Build arguments
ARG SDNEXT_VERSION=main
ARG DEBIAN_FRONTEND=noninteractive

# Set shell with pipefail for safety
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=true \
    UV_NO_CACHE=true \
    PIP_ROOT_USER_ACTION=ignore \
    SHELL=/bin/bash \
    PYTHONPATH=/opt/sdnext/.venv/lib/python3.10/site-packages \
    SD_NOHASHING=true \
    SD_DOCKER=true

# Install system dependencies and uv in one layer, then clean up
# hadolint ignore=DL3008
RUN apt-get update && \
    # Install runtime dependencies (no Python packages - uv will handle Python)
    apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    google-perftools \
    ffmpeg \
    bc \
    nginx-light \
    tmux \
    nano \
    vim \
    htop \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    # Install uv (fastest Python package manager and environment manager)
    && curl -LsSf https://astral.sh/uv/install.sh | bash \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && /usr/sbin/ldconfig


# Install ttyd and logdy (x86_64 only)
RUN curl -L --progress-bar https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.x86_64 -o /usr/local/bin/ttyd && \
    curl -L --progress-bar https://github.com/logdyhq/logdy-core/releases/download/v0.13.0/logdy_linux_amd64 -o /usr/local/bin/logdy && \
    chmod +x /usr/local/bin/ttyd /usr/local/bin/logdy

# Install filebrowser and set up directories
RUN curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash && \
    mkdir -p /workspace/logs /opt/sdnext /root/.config

# Clone SD.Next and fetch latest changes
WORKDIR /opt
RUN git clone https://github.com/vladmandic/sdnext.git sdnext

WORKDIR /opt/sdnext
# Always fetch latest changes and checkout the specified version (defaults to master)
RUN git fetch origin && \
    git checkout ${SDNEXT_VERSION} && \
    git pull origin ${SDNEXT_VERSION}

# Create Python environment with uv and install SD.Next
# hadolint ignore=SC2015
RUN uv venv --seed --python 3.10 .venv && \
    # Activate the virtual environment
    . .venv/bin/activate && \
    # SD.Next will run all necessary pip install operations during first launch
    # Run initial setup with test mode to install dependencies
    python launch.py --debug --uv --use-cuda --log sdnext.log --test --optional && \
    # Verify PyTorch installation
    python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')" && \
    # Clean up build dependencies (keep uv for runtime)
    apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    find /opt/sdnext/.venv -name "*.pyc" -delete && \
    find /opt/sdnext/.venv -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Copy configuration files and scripts (frequently changing layer)
COPY config/ /opt/config/
COPY config/filebrowser/filebrowser.json /root/.filebrowser.json
COPY scripts/start.sh /opt/bin/start.sh
COPY scripts/services/ /opt/bin/services/
COPY scripts/provision/ /opt/provision/

# Configure filebrowser, set permissions, and final cleanup
# hadolint ignore=SC2015
RUN mkdir -p /opt/bin && \
    chmod +x /opt/bin/start.sh /opt/bin/services/*.sh /opt/provision/provision.py && \
    date -u +"%Y-%m-%dT%H:%M:%SZ" > /root/BUILDTIME.txt && \
    # Final cleanup
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    # Remove any remaining build artifacts
    find /opt -name "*.pyc" -delete && \
    find /opt -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Set environment variables
ENV USERNAME=admin \
    PASSWORD=admin123 \
    WORKSPACE=/workspace \
    SD_DATADIR="/workspace" \
    SDNEXT_ARGS="" \
    NO_ACCELERATE="" \
    LD_PRELOAD=libtcmalloc.so.4 \
    OPEN_BUTTON_PORT=80

# Expose ports
EXPOSE 80 8010 7010 7020 7030

# Set working directory
WORKDIR /workspace

# Entrypoint
ENTRYPOINT ["/opt/bin/start.sh"]
