#!/usr/bin/env bash
# Local testing script for the provisioning system

echo "Setting up local test environment for provisioning system..."

# Create test workspace
TEST_DIR="/tmp/vastai-sdnext-test"
mkdir -p "$TEST_DIR/models/Stable-diffusion"
mkdir -p "$TEST_DIR/models/Lora" 
mkdir -p "$TEST_DIR/models/VAE"
mkdir -p "$TEST_DIR/models/ControlNet"
mkdir -p "$TEST_DIR/models/ESRGAN"
mkdir -p "$TEST_DIR/logs"

# Set environment variables
export WORKSPACE="$TEST_DIR"

# Optional: Set tokens if you have them
# export HF_TOKEN="hf_xxxxxxxxxxxx"
# export CIVITAI_TOKEN="xxxxxxxxx"

# Create a simple test configuration
cat > "$TEST_DIR/test-config.toml" << 'EOF'
# Test configuration for local provisioning

# Small test model from HuggingFace (public, no auth required)
[models.checkpoints.test-model]
source = "huggingface"
repo = "hf-internal-testing/tiny-stable-diffusion-pipe"
file = "scheduler.bin"  # Very small file for testing

# Direct URL test (small file)
[models.lora.test-lora]
source = "url"
url = "https://raw.githubusercontent.com/CompVis/stable-diffusion/main/LICENSE"
filename = "test-license.txt"

# Uncomment to test gated models (requires HF_TOKEN)
# [models.checkpoints.sdxl-base]
# source = "huggingface"
# repo = "stabilityai/stable-diffusion-xl-base-1.0"
# file = "sd_xl_base_1.0.safetensors"
# gated = false  # This model is not gated

# Uncomment to test CivitAI (requires CIVITAI_TOKEN for some models)
# [models.lora.test-civitai]
# source = "civitai"
# model_id = "87153"  # Replace with actual model ID
EOF

echo ""
echo "Test environment created at: $TEST_DIR"
echo ""
echo "To run the provisioning test:"
echo ""
echo "1. Using local config file:"
echo "   ./scripts/provision/provision.py $TEST_DIR/test-config.toml"
echo ""
echo "2. Using remote URL (start a local server first):"
echo "   python -m http.server 8000 --directory $TEST_DIR"
echo "   ./scripts/provision/provision.py http://localhost:8000/test-config.toml"
echo ""
echo "3. Test with tokens:"
echo "   export HF_TOKEN='your-token-here'"
echo "   export CIVITAI_TOKEN='your-token-here'"
echo "   ./scripts/provision/provision.py $TEST_DIR/test-config.toml"
echo ""
echo "Models will be downloaded to: $TEST_DIR/models/"
echo "Logs will be saved to: $TEST_DIR/logs/provision.log"
echo ""
echo "To clean up test environment:"
echo "   rm -rf $TEST_DIR"