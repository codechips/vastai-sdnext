# Model Provisioning System

The container includes an automated model provisioning system that can download models from multiple sources during startup.

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PROVISION_URL` | URL to TOML configuration file for automatic provisioning | None | No |
| `WORKSPACE` | Target directory for models and data | `/workspace` | No |
| `HF_TOKEN` | HuggingFace API token for gated models | None | No |
| `CIVITAI_TOKEN` | CivitAI API token for some models | None | No |

## Quick Provisioning Setup

1. **Create a TOML configuration file** (see [examples](examples/)):
   ```toml
   # Basic configuration example
   [models.checkpoints.sdxl-base]
   source = "huggingface"
   repo = "stabilityai/stable-diffusion-xl-base-1.0"
   file = "sd_xl_base_1.0.safetensors"

   [models.lora.detail-tweaker]
   source = "civitai"
   version_id = "58390"
   ```

2. **Host the configuration file** (GitHub, Google Drive, S3, HTTP server, etc.)

3. **Launch container with provisioning**:
   ```bash
   docker run -d \
     -p 8010:8010 -p 7010:7010 -p 7020:7020 -p 7030:7030 \
     -e USERNAME=admin -e PASSWORD=admin \
     -e PROVISION_URL=https://drive.google.com/file/d/YOUR_FILE_ID/view \
     -e HF_TOKEN=hf_your_token_here \
     -e CIVITAI_TOKEN=your_civitai_token \
     ghcr.io/codechips/vastai-sdnext:latest
   ```

## Manual Provisioning

You can also run the provisioning script manually from inside the container:

```bash
# Access container terminal (via ttyd web interface or docker exec)
cd /opt/bin

# Provision from local file
./provision/provision.py /workspace/config.toml

# Provision from URL
./provision/provision.py https://example.com/config.toml

# Dry run (validate without downloading)
./provision/provision.py config.toml --dry-run

# Override workspace directory
./provision/provision.py config.toml --workspace /custom/path

# Get help
./provision/provision.py --help
```

## Supported Model Sources

### 1. HuggingFace Hub
```toml
[models.checkpoints.model-name]
source = "huggingface"
repo = "username/repository"
file = "model.safetensors"
gated = false  # Set to true for gated models (requires HF_TOKEN)
```

### 2. CivitAI
```toml
[models.lora.model-name]
source = "civitai"
version_id = "12345"  # CivitAI model version ID (not model ID)
filename = "custom_name.safetensors"  # Optional
```

**Important Note**: CivitAI uses `version_id` (not `model_id`) which refers to a specific version of a model. You can find the version ID in the CivitAI URL or API response when viewing a specific model version.

### 3. Direct URLs (including Google Drive)
```toml
[models.vae.model-name]
source = "url"
url = "https://example.com/model.safetensors"
filename = "model.safetensors"
headers = { "Authorization" = "Bearer token" }  # Optional
```

### 4. Google Drive URLs
**Supported URL formats:**
```toml
# Google Drive sharing link
[models.checkpoints.gdrive-model]
source = "url"
url = "https://drive.google.com/file/d/1ABC123DEF456/view?usp=sharing"
filename = "custom-name.safetensors"

# Direct Google Drive download (auto-converted)
[models.lora.another-model]
source = "url"
url = "https://drive.google.com/uc?id=1ABC123DEF456"
```

**Features:**
- **Automatic conversion** from sharing links to direct download URLs
- **Virus scan bypass** - handles Google's "can't scan large files" warnings
- **Works for both** model files and provision config files (`PROVISION_URL`)
- **Example provision config**: `PROVISION_URL=https://drive.google.com/file/d/YOUR_ID/view`

### 5. Simple URL Format
```toml
[models.lora]
simple-model = "https://example.com/model.safetensors"
```

### 6. CLIP Text Encoders
```toml
[models.text_encoder.clip_l]
source = "huggingface"
repo = "comfyanonymous/flux_text_encoders"
file = "clip_l.safetensors"

[models.text_encoder.t5xxl_fp8]
source = "huggingface"
repo = "comfyanonymous/flux_text_encoders"
file = "t5xxl_fp8_e4m3fn.safetensors"

[models.text_encoder.openclip_vit_l14]
source = "huggingface"
repo = "zer0int/CLIP-GmP-ViT-L-14"
file = "ViT-L-14-BEST-smooth-GmP-HF-format.safetensors"
```

### 7. FLUX VAE
```toml
# Required for FLUX models
[models.vae.flux-vae]
source = "huggingface"
repo = "black-forest-labs/FLUX.1-dev"
file = "ae.safetensors"
```

## Model Categories and Directories

| Category | Directory | Description |
|----------|-----------|-------------|
| `checkpoints` | `models/Stable-diffusion/` | Main model files |
| `lora` | `models/Lora/` | LoRA adaptation files |
| `vae` | `models/VAE/` | Variational Auto-Encoder models |
| `controlnet` | `models/ControlNet/` | ControlNet models |
| `esrgan` | `models/ESRGAN/` | Upscaling models |
| `embeddings` | `models/embeddings/` | Text embeddings |
| `hypernetworks` | `models/hypernetworks/` | Hypernetwork models |
| `text_encoder` | `models/text_encoder/` | CLIP and text encoder models |
| `clip` | `models/text_encoder/` | Alias for text_encoder |

**Note**: Models are stored in SD.Next's standard directory structure (`/opt/sdnext/models/`), with workspace symlinks for convenient access via file browser at `${WORKSPACE}/sdnext/models/` (default: `/workspace/sdnext/models/`).

## Example Configurations

- [**Minimal Example**](examples/test-provision-minimal.toml): Small test files for validation
- [**Full Example**](examples/test-provision-full.toml): Comprehensive configuration with all features
- [**FLUX Example**](examples/flux-provision.toml): Complete FLUX.1-dev setup with VAE and text encoders
- [**Main Example**](examples/provision-config.toml): Production-ready configuration template

## Local Testing

Test the provisioning system locally:

```bash
# Run the test setup script
./test_provision_local.sh

# This creates a test environment at /tmp/vastai-sdnext-test
# and provides commands to test different scenarios
```

## Troubleshooting

**Common Issues:**

1. **Authentication Errors**: Ensure `HF_TOKEN` and `CIVITAI_TOKEN` are set correctly
2. **Gated Models**: Visit the HuggingFace model page and accept terms of service
3. **Network Issues**: Check if URLs are accessible and not blocked
4. **Disk Space**: Ensure adequate storage for model downloads
5. **TOML Syntax**: Validate configuration with `--dry-run` option
6. **CivitAI Version ID**: Make sure you're using `version_id` (not `model_id`) for CivitAI models

**Logs**: Check provisioning logs at `/workspace/logs/provision.log` or via the logdy interface (port 7030).

## Advanced Configuration

### Authentication Tokens

**HuggingFace Token (`HF_TOKEN`)**:
- Required for gated models (FLUX.1-dev, etc.)
- Get from: https://huggingface.co/settings/tokens
- Must accept Terms of Service for gated repositories

**CivitAI Token (`CIVITAI_TOKEN`)**:
- Optional for most models, required for some premium content
- Get from: https://civitai.com/user/account
- Improves download reliability and access to exclusive content

### Performance Tuning

**Concurrent Downloads**: The system downloads models in parallel by default (max 5 concurrent).

**Memory Usage**: Large models are downloaded with streaming to minimize memory usage.

**Error Handling**: Failed downloads are retried and logged with detailed error messages.

### Directory Structure

Models are organized following SD.Next conventions:

```
/workspace/sdnext/models/
├── Stable-diffusion/     # Checkpoints
├── Lora/                 # LoRA models
├── VAE/                  # VAE models
├── ControlNet/           # ControlNet models
├── ESRGAN/               # Upscaling models
├── embeddings/           # Text embeddings
├── hypernetworks/        # Hypernetwork models
└── text_encoder/         # CLIP and text encoders
```

## API and Integration

The provisioning system can be integrated into other workflows:

```python
from provision.core import ProvisioningSystem

# Initialize system
provisioner = ProvisioningSystem(workspace_dir="/workspace")

# Provision from URL
await provisioner.provision_from_url("https://example.com/config.toml")

# Provision from local file
await provisioner.provision_from_file("/path/to/config.toml")
```
