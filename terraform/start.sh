#!/bin/bash
set -euo pipefail

exec > >(tee -a /var/log/startup-script.log) 2>&1
echo "Starting idempotent VM setup"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl gnupg lvm2 git

if ! command -v docker &> /dev/null; then
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable"| tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

systemctl enable --now docker

setup_lvm_volume() {
    local DEVICE="$1"
    local VG_NAME="$2"
    local LV_NAME="$3"
    local MOUNT_POINT="$4"

    if [ ! -b "$DEVICE" ]; then
        echo "Disk $DEVICE not found"
        return
    fi

    if ! pvs "$DEVICE" &> /dev/null; then
        pvcreate -ff -y "$DEVICE"
    fi

    if ! vgs "$VG_NAME" &> /dev/null; then
        vgcreate "$VG_NAME" "$DEVICE"
    fi

    local LV_PATH="/dev/$VG_NAME/$LV_NAME"
    if ! lvs "$LV_PATH" &> /dev/null; then
        lvcreate -l 100%FREE -n "$LV_NAME" "$VG_NAME"
    fi

    if ! blkid "$LV_PATH" | grep -q "TYPE=\"etx4\""; then
        mkfs.etx4 -F "$LV_PATH"
    fi

    mkdir -p "$MOUNT_POINT"
    if ! grep -q "$LV_PATH" /etc/fstab; then
        echo "$LV_PATH $MOUNT_POINT ext4 defaults,nofail 0 2" >> /etc/fstab
    fi

    if ! mountpoint -q "$MOUNT_POINT"; then
        mount "$MOUNT_POINT"
    fi
}

setup_lvm_volume "/dev/disk/by-id/google-db-disk" "vg_db" "lv_db" "/data/db"
setup_lvm_volume "/dev/disk/by-id/google-models-disk" "vg_models" "lv_models" "/models"

APP_DIR="/opt/ai-tutor-app"
REPO_URL="${repo_url}"

if [ ! -d "$APP_DIR/.git" ]; then
    git clone "$REPO_URL" "$APP_DIR"
else
    git -C "$APP_DIR" fetch --all
    git -C "$APP_DIR" pull --ff-only || true
fi

PROJECT_ID="${project_id}"
DB_PASSWORD=$(gcloud secrets versions access latest --secret="${db_secret_id}" --project="$PROJECT_ID")

cat <<EOF > "$APP_DIR/.env"
DB_HOST=database
DB_PORT=5432
DB_NAME=${db_name}
DB_USER=${db_user}
DB_PASSWORD=$DB_PASSWORD
FLASK_SERVER_ADDRESS=flask-app:5000
LOCAL_AI_DEV=True
EOF

chmod 600 "$APP_DIR/.env"

cd "$APP_DIR"
docker compose up -d --build
echo "Startup Completed"