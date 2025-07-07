#!/usr/bin/env bash
# Filebrowser service

function start_filebrowser() {
    echo "filebrowser: starting"
    cd /root

    # Remove existing database to ensure clean initialization
    rm -f /root/filebrowser.db

    # Initialize database and create admin user
    echo "filebrowser: initializing database"
    if ! /usr/local/bin/filebrowser config init --minimum-password-length 5; then
        echo "filebrowser: ERROR - Failed to initialize database"
        return 1
    fi
    
    # Set the password to use (default to admin123 if not provided)
    ADMIN_PASSWORD="${PASSWORD:-admin123}"
    
    # Validate password length (minimum 5 characters as per config)
    if [[ ${#ADMIN_PASSWORD} -lt 5 ]]; then
        echo "filebrowser: ERROR - Password must be at least 5 characters long"
        echo "filebrowser: Using default password 'admin123'"
        ADMIN_PASSWORD="admin123"
    fi
    
    # Create admin user with the specified password
    echo "filebrowser: creating admin user"
    if ! /usr/local/bin/filebrowser users add admin "${ADMIN_PASSWORD}" --perm.admin; then
        echo "filebrowser: ERROR - Failed to create admin user"
        return 1
    fi
    
    echo "filebrowser: admin user created successfully"

    # Start filebrowser in background
    nohup /usr/local/bin/filebrowser >"${WORKSPACE}/logs/filebrowser.log" 2>&1 &
    echo "filebrowser: started on port 7010"
    echo "filebrowser: log file at ${WORKSPACE}/logs/filebrowser.log"
}

# Main execution if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    start_filebrowser
fi