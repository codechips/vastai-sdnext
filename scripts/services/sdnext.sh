#!/usr/bin/env bash
# SD.Next WebUI service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/utils.sh"

function start_sdnext() {
    echo "sdnext: starting"
    cd /opt/sdnext

    # Activate the uv-created virtual environment
    source .venv/bin/activate

    # Default SD.Next arguments
    DEFAULT_ARGS="--listen --port 8010 --data-dir ${WORKSPACE}"

    # Add authentication using environment variables
    if [[ ${USERNAME} ]] && [[ ${PASSWORD} ]]; then
        AUTH_ARGS="--auth ${USERNAME}:${PASSWORD}"
        echo "sdnext: enabling authentication for user: ${USERNAME}"
    else
        AUTH_ARGS=""
        echo "sdnext: starting without authentication (no USERNAME/PASSWORD set)"
    fi

    # Combine default args with auth and any custom args
    FULL_ARGS="${DEFAULT_ARGS} ${AUTH_ARGS} ${SDNEXT_ARGS}"

    # Prepare TCMalloc for better memory performance
    prepare_tcmalloc

    # SD.Next handles its own optimizations, just launch normally
    echo "sdnext: launching with args: ${FULL_ARGS}"
    nohup python launch.py ${FULL_ARGS} >"${WORKSPACE}/logs/sdnext.log" 2>&1 &

    echo "sdnext: started on port 8010"
    echo "sdnext: log file at ${WORKSPACE}/logs/sdnext.log"
}

# Main execution if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    start_sdnext
fi