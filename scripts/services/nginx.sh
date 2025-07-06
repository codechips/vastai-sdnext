#!/usr/bin/env bash
# Nginx service with dynamic landing page

function start_nginx() {
    echo "nginx: starting web server"
    
    # Create nginx directories
    mkdir -p /opt/nginx/html
    mkdir -p /var/log/nginx
    
    # Get external IP and port mappings from Vast.ai environment
    EXTERNAL_IP="${PUBLIC_IPADDR:-localhost}"
    FORGE_PORT="${VAST_TCP_PORT_8010:-8010}"
    FILES_PORT="${VAST_TCP_PORT_7010:-7010}"
    TERMINAL_PORT="${VAST_TCP_PORT_7020:-7020}"
    LOGS_PORT="${VAST_TCP_PORT_7030:-7030}"
    
    echo "nginx: generating landing page for IP ${EXTERNAL_IP}"
    echo "nginx: ports - forge:${FORGE_PORT}, files:${FILES_PORT}, terminal:${TERMINAL_PORT}, logs:${LOGS_PORT}"
    
    # Copy and process the landing page HTML template
    cp "${WORKSPACE}/config/nginx/index.html" /opt/nginx/html/index.html

    # Get build information from Docker build
    BUILD_DATE=$(cat /root/BUILDTIME.txt 2>/dev/null || echo "unknown")
    FULL_SHA=$(cat /root/BUILD_SHA.txt 2>/dev/null || echo "unknown")
    GIT_SHA=$(echo "$FULL_SHA" | cut -c1-7)

    # Replace placeholders with actual values
    sed -i "s/EXTERNAL_IP:FORGE_PORT/${EXTERNAL_IP}:${FORGE_PORT}/g" /opt/nginx/html/index.html
    sed -i "s/EXTERNAL_IP:FILES_PORT/${EXTERNAL_IP}:${FILES_PORT}/g" /opt/nginx/html/index.html
    sed -i "s/EXTERNAL_IP:TERMINAL_PORT/${EXTERNAL_IP}:${TERMINAL_PORT}/g" /opt/nginx/html/index.html
    sed -i "s/EXTERNAL_IP:LOGS_PORT/${EXTERNAL_IP}:${LOGS_PORT}/g" /opt/nginx/html/index.html
    sed -i "s/GIT_SHA/${GIT_SHA}/g" /opt/nginx/html/index.html
    sed -i "s/BUILD_DATE/${BUILD_DATE}/g" /opt/nginx/html/index.html
    
    # Copy nginx configuration
    cp "${WORKSPACE}/config/nginx/default.conf" /etc/nginx/sites-available/default

    # Start nginx
    nginx -t && nginx -g 'daemon off;' >"${WORKSPACE}/logs/nginx.log" 2>&1 &
    
    echo "nginx: started on port 80"
    echo "nginx: log file at ${WORKSPACE}/logs/nginx.log"
    echo "nginx: serving landing page at http://${EXTERNAL_IP}:80"
}

# Main execution if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    start_nginx
fi