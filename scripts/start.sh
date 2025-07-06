#!/usr/bin/env bash
# Main orchestrator for VastAI SD.Next container services

# Simple process manager for SD.Next and supporting services
# Based on vastai-fooocus pattern with modular service architecture

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICES_DIR="$SCRIPT_DIR/services"

# Source utilities
source "$SERVICES_DIR/utils.sh"

# Source service scripts
source "$SERVICES_DIR/nginx.sh"
source "$SERVICES_DIR/sdnext.sh"
source "$SERVICES_DIR/filebrowser.sh"
source "$SERVICES_DIR/ttyd.sh"
source "$SERVICES_DIR/logdy.sh"
source "$SERVICES_DIR/provisioning.sh"

# Main execution
echo "Starting VastAI SD.Next container..."

# Setup workspace
setup_workspace

# Start services
start_nginx
start_filebrowser
start_sdnext
start_ttyd
start_logdy

# Show information
show_info

# Run provisioning if enabled
run_provisioning

# Keep container running
echo ""
echo "Container is running. Press Ctrl+C to stop."
sleep infinity