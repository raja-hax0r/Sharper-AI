import os
import subprocess
import sys

VPS_IP = "139.59.60.206"
VPS_PATH = "/root/sharper-ai"
SSH_KEY = r"C:\Users\Raja\.ssh\id_ed25519"
SERVICE_NAME = "pariahs-mineshaft.service"

def run_cmd(cmd, shell=False):
    print(f"Executing: {cmd}")
    try:
        res = subprocess.run(cmd, shell=shell, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.stdout:
            print(res.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def deploy():
    print("🚀 Starting VPS Deployment for Pariah's Mineshaft...")
    
    # 1. Create directory on VPS if it doesn't exist
    ssh_prefix = f"ssh -i {SSH_KEY} -o StrictHostKeyChecking=no root@{VPS_IP}"
    run_cmd(f'{ssh_prefix} "mkdir -p {VPS_PATH}/static {VPS_PATH}/templates"')
    
    # 2. SCP core files
    files_to_transfer = [
        "app.py",
        "db.py",
        "generator.py",
        "requirements.txt"
    ]
    
    for file in files_to_transfer:
        if os.path.exists(file):
            run_cmd(f"scp -i {SSH_KEY} -o StrictHostKeyChecking=no {file} root@{VPS_IP}:{VPS_PATH}/{file}")
            
    # 3. SCP HTML templates and static assets
    if os.path.exists("templates/index.html"):
        run_cmd(f"scp -i {SSH_KEY} -o StrictHostKeyChecking=no templates/index.html root@{VPS_IP}:{VPS_PATH}/templates/index.html")
        
    static_files = ["app.js", "style.css", "bg.png", "bgm2.wav"]
    for s_file in static_files:
        path = os.path.join("static", s_file)
        if os.path.exists(path):
            run_cmd(f"scp -i {SSH_KEY} -o StrictHostKeyChecking=no {path} root@{VPS_IP}:{VPS_PATH}/static/{s_file}")
            
    # 4. Copy .env to VPS (ensure the API key is synced)
    if os.path.exists(".env"):
        run_cmd(f"scp -i {SSH_KEY} -o StrictHostKeyChecking=no .env root@{VPS_IP}:{VPS_PATH}/.env")

    # 5. Remote shell operations: Virtual environment setup, requirements, and systemd service
    print("📦 Setting up virtual environment and service on VPS...")
    vps_commands = f"""
    cd {VPS_PATH}
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    venv/bin/pip install -r requirements.txt
    
    # Write systemd service file
    cat <<EOT > /etc/systemd/system/{SERVICE_NAME}
[Unit]
Description=Pariah's Mineshaft Webapp
After=network.target

[Service]
User=root
WorkingDirectory={VPS_PATH}
ExecStart={VPS_PATH}/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOT
    
    # Enable and restart service
    systemctl daemon-reload
    systemctl enable {SERVICE_NAME}
    systemctl restart {SERVICE_NAME}
    systemctl status {SERVICE_NAME} --no-pager
    """
    
    # Run the commands on VPS
    run_cmd(f'{ssh_prefix} "{vps_commands}"')
    
    print("\n✅ Deployment completed! App should be reachable over Tailscale at http://100.72.83.40:8003")

if __name__ == "__main__":
    deploy()
