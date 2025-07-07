#!/usr/bin/env bash
# Filebrowser service

function start_filebrowser() {
    echo "filebrowser: starting"
    cd /root

    # Update password if provided
    if [[ ${PASSWORD} ]] && [[ ${PASSWORD} != "admin123" ]]; then
        echo "filebrowser: updating admin password"
        if /usr/local/bin/filebrowser users update admin -p ${PASSWORD}; then
            echo "filebrowser: password updated successfully"
        else
            echo "filebrowser: ERROR - Failed to update password. Check if password meets requirements:"
            echo "filebrowser: - Must be at least 5 characters long"
            echo "filebrowser: - Must not be a common password (like 'password', '123456', etc.)"
            echo "filebrowser: - Keeping default password 'admin123'"
        fi
    fi

    # Start filebrowser in background
    nohup /usr/local/bin/filebrowser >"${WORKSPACE}/logs/filebrowser.log" 2>&1 &
    echo "filebrowser: started on port 7010"
    echo "filebrowser: log file at ${WORKSPACE}/logs/filebrowser.log"
}

# Main execution if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    start_filebrowser
fi