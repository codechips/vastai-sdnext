# Vast.ai SD.Next Docker Image

Simplified single Docker image for running SD.Next (Stable Diffusion Next) on Vast.ai with integrated web-based management tools and automated model provisioning.

## Features

**All-in-one Docker image** with:
- **SD.Next** (port 8010): Advanced Stable Diffusion interface with support for multiple model types
- **Filebrowser** (port 7010): File management interface
- **ttyd** (port 7020): Web-based terminal (writable)
- **logdy** (port 7030): Log viewer
- **Automated Model Provisioning**: Download models from HuggingFace, CivitAI, and direct URLs
- **PyTorch 2.7.0 + CUDA 12.8**: Latest optimized runtime
- **Simple process management**: No complex orchestration

## Quick Start

### For Vast.ai Users

1. Create a new instance with:
   ```
   Docker Image: ghcr.io/codechips/vastai-sdnext:latest
   ```

2. Configure environment variables:
   ```bash
   -e USERNAME=your_username -e PASSWORD=your_password -e OPEN_BUTTON_PORT=8010
   ```

   **Optional model provisioning** (see [PROVISION.md](PROVISION.md) for details):
   ```bash
   -e PROVISION_URL=https://your-server.com/config.toml
   -e HF_TOKEN=hf_your_huggingface_token
   -e CIVITAI_TOKEN=your_civitai_token
   ```

3. Map ports:
   ```bash
   -p 8010:8010 -p 7010:7010 -p 7020:7020 -p 7030:7030
   ```

4. Launch with "Entrypoint" mode for best compatibility

### Access Your Services

- **SD.Next**: Port 8010 (main interface, protected with auth)
- **File Manager**: Port 7010 (manage models and outputs, protected with auth)
- **Terminal**: Port 7020 (command line access, writable, protected with auth)
- **Logs**: Port 7030 (monitor all application logs)

## Default Credentials

- Username: `admin`
- Password: `admin`

## Environment Variables

### Core Configuration
- `USERNAME`: Username for all services (default: `admin`)
- `PASSWORD`: Password for all services (default: `admin`)
- `OPEN_BUTTON_PORT`: Port for Vast.ai's "Open" button (default: `8010`)

### SD.Next Configuration
- `SDNEXT_ARGS`: Additional arguments for SD.Next (default: empty)
- `NO_ACCELERATE`: Disable HuggingFace Accelerate optimization (default: empty/false)

### ttyd Terminal Configuration
- `ENABLE_TTYD`: Enable/disable web terminal service (default: `true`)
- `TTYD_START_DIR`: Directory where terminal starts (default: `${WORKSPACE}`)

### Model Provisioning
- `PROVISION_URL`: URL to TOML configuration file for model provisioning
- `HF_TOKEN`: HuggingFace token for private model access
- `CIVITAI_TOKEN`: CivitAI token for model downloads

### Advanced Options
- `NO_TCMALLOC`: Disable TCMalloc memory optimization (default: empty/false)
- `LD_PRELOAD`: Custom memory allocator (default: `libtcmalloc.so.4`)

## Model Provisioning

📋 **Complete provisioning documentation has been moved to [PROVISION.md](PROVISION.md)**

The container includes an automated model provisioning system that can download models from HuggingFace, CivitAI, and direct URLs during startup.

**Quick example:**
```bash
docker run -d \
  -p 8010:8010 -p 7010:7010 -p 7020:7020 -p 7030:7030 \
  -e USERNAME=admin -e PASSWORD=admin \
  -e PROVISION_URL=https://your-server.com/config.toml \
  -e HF_TOKEN=hf_your_token_here \
  -e CIVITAI_TOKEN=your_civitai_token \
  ghcr.io/codechips/vastai-sdnext:latest
```

**See [PROVISION.md](PROVISION.md) for:**
- Complete configuration guide
- All supported model sources
- Authentication setup
- Troubleshooting tips
- Example configurations

## Automated Updates

The Docker image is automatically built and updated:

- **Push Builds**: New image built immediately when changes are pushed to main branch
- **Weekly Builds**: Every Sunday at 2 AM UTC to catch upstream SD.Next updates
- **Version Management**: Always maintains exactly 3 most recent versions
- **Tags**: `latest` (current), `YYYYMMDD` (date-based), `YYYY-WUU` (weekly builds)

This ensures your image stays current with both repository changes and upstream SD.Next improvements.

## Performance Optimization

### Accelerate Support (Enabled by Default)

The container uses HuggingFace Accelerate by default for optimized multi-core performance:

**Benefits:**
- **Multi-core optimization**: Uses `--num_cpu_threads_per_process=6` for better CPU utilization
- **Memory efficiency**: Improved memory management for large models
- **Faster loading**: Optimized model loading and inference
- **Automatic fallback**: Uses standard Python if accelerate is unavailable

**Control:**
```bash
# Disable accelerate if needed (not recommended)
-e NO_ACCELERATE=True
```

**Usage:**
- **Enabled by default**: No configuration needed for optimal performance
- **Automatic detection**: Only activates if accelerate is available
- **Safe fallback**: Uses standard Python launch if accelerate fails
- **Particularly beneficial**: On multi-core systems (most Vast.ai instances)

### TCMalloc Memory Optimization

The container automatically detects and uses TCMalloc for improved memory performance:

**Features:**
- **Automatic detection**: Finds and configures TCMalloc libraries at startup
- **glibc compatibility**: Handles different glibc versions (pre/post 2.34)
- **Memory efficiency**: Significantly reduces memory fragmentation
- **CPU performance**: Better memory allocation performance
- **Safe fallback**: Continues without TCMalloc if unavailable

**Control:**
- **Disable**: Set `NO_TCMALLOC=1` to skip TCMalloc setup
- **Manual override**: Set `LD_PRELOAD` to use custom memory allocator
- **Automatic**: Enabled by default on Linux systems

**Supported libraries:**
- `libtcmalloc-minimal4` (pre-installed in container)
- `libtcmalloc.so` variants
- Compatible with Ubuntu 22.04 glibc

## Directory Structure

```
vastai-sdnext/
├── Dockerfile                      # Single image with all components
├── scripts/
│   ├── start.sh                   # Main orchestrator script
│   ├── services/                  # Modular service scripts
│   │   ├── utils.sh              # Shared utilities (TCMalloc, workspace)
│   │   ├── sdnext.sh             # SD.Next WebUI service
│   │   ├── filebrowser.sh        # File browser service
│   │   ├── ttyd.sh               # Web terminal service
│   │   ├── logdy.sh              # Log viewer service
│   │   └── provisioning.sh       # Model provisioning service
│   └── provision/                 # Model provisioning system
│       ├── provision.py           # Main provisioning script
│       ├── config/                # Configuration parsing
│       ├── downloaders/           # Download implementations
│       ├── utils/                 # Utilities and logging
│       └── validators/            # Token validation
├── config/
│   ├── filebrowser/               # Filebrowser configuration
│   └── forge/                     # SD.Next configuration (if any)
├── examples/                      # Provisioning configuration examples
│   ├── provision-config.toml      # Production template
│   ├── test-provision-minimal.toml # Minimal test config
│   └── test-provision-full.toml   # Full feature example
├── docs/                          # Documentation
├── test_provision_local.sh        # Local testing script
├── .github/workflows/             # Simplified CI/CD workflows
│   ├── weekly-build.yml           # Main build & cleanup workflow
│   └── delete-package-versions.yml # Reusable cleanup component
└── .mise.toml                     # Task runner configuration
```

## Local Development

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Mise](https://mise.jdx.dev/) task runner

### Quick Start
```bash
# Build and test everything
mise run dev

# Or step by step:
mise run build    # Build image
mise run test     # Start test container
mise run status   # Check service status

# Test provisioning system locally
./test_provision_local.sh
```

### Available Mise Tasks

#### Building
```bash
mise run build          # Build image
mise run build-no-cache # Build without cache (for debugging)
mise run build-prod     # Build production image for linux/amd64
```

#### Testing
```bash
mise run test           # Start test container
mise run test-services  # Test services with curl
mise run dev            # Full development workflow
```

#### Management
```bash
mise run status         # Check container and service status
mise run logs           # Follow container logs
mise run shell          # Get shell access to container
mise run stop           # Stop test container
mise run clean          # Clean up everything
```

### Manual Docker Commands
If you prefer not to use Mise:
```bash
# Build image
docker build -t vastai-sdnext:local .

# Run container
docker run -d --name vastai-test \
  -p 8010:8010 -p 7010:7010 -p 7020:7020 -p 7030:7030 \
  -e USERNAME=admin -e PASSWORD=admin \
  vastai-sdnext:local
```

## Log Monitoring

The logdy interface (port 7030) provides real-time monitoring of:

- **SD.Next**: Complete SD.Next logs including model loading, generation progress, and errors
- **Filebrowser**: Application logs and access logs
- **ttyd**: Terminal session logs
- **Logdy**: Log viewer service logs

All logs are easily searchable through the logdy web interface.

## Security Features

- **Unified authentication** across all services:
  - SD.Next: Built-in authentication
  - Filebrowser: Native authentication
  - ttyd terminal: Basic authentication
- **Configurable credentials** via environment variables (USERNAME/PASSWORD)
- **Simple, secure access** to all management tools

## Compatibility

- **CUDA**: 12.8 (with cudnn9)
- **PyTorch**: 2.7.0 (with CUDA 12.8 support)
- **Python**: 3.10
- **GPU**: NVIDIA GPUs with CUDA support
- **Platform**: Vast.ai, local Docker environments
- **Architecture**: x86_64 (AMD64)


## Useful links

- [SD.Next GitHub Repository](https://github.com/vladmandic/sdnext)
- [SD.Next Documentation](https://github.com/vladmandic/sdnext/wiki)
- [SD.Next Discord](https://discord.gg/VjvR2tabEX)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `mise run dev`
5. Submit a pull request

## License

This project is open source. Please check individual component licenses for specific terms.
