#!/usr/bin/env bash
set -e

# Bash script designed to create backups from volumes

SCRIPT_DIR="$(dirname "$0")"
BACKUPS_DIR="$SCRIPT_DIR/backups"
VOLUMES_FILE="$SCRIPT_DIR/.volumes"

get_volumes_from_file() {
  if [ -r "$VOLUMES_FILE" ]; then
    cat "$VOLUMES_FILE" | grep -v '^#'
    return 0
  else
    echo "$VOLUMES_FILE file not found or not readable"
    return 1
  fi
}

backup_volume() {
  volume_name="$1"
  echo "Starting backup for volume: $volume_name"

  docker run --rm \
    --hostname $(hostname) \
    -v "$volume_name:/$volume_name:ro" \
    -v "$BACKUPS_DIR:/repo" \
    --env-file "$SCRIPT_DIR/.env" \
    -e RESTIC_REPOSITORY=/repo \
    restic/restic backup /$volume_name --compression max

  echo "Finished backup for volume: $volume_name"
  echo
}

fix_permissions() {
  echo "Fixing backup directory permissions..."
  docker run --rm \
    -v "$BACKUPS_DIR:/data" \
    alpine chown -R "$(id -u):$(id -g)" /data
}

# Main part
echo "Welcome to the backup script!"
volumes=$(get_volumes_from_file)

for volume in $volumes; do
  backup_volume "$volume"
done

fix_permissions
