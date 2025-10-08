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

backup_stack() {
  dir=$1
  echo "Starting backup for stack: $dir"
  cd "$dir"

  if [ ! -f .volumes ]; then
    if [ -n "$(docker compose volumes -q)" ]; then
      touch .volumes
    else
      echo "No volumes found, skipping creation of .volumes file"
      echo
      cd -
      return 0
    fi
  fi

  # Add volumes that are not yet in .volumes file
  for volume in $(docker compose volumes -q); do
    if ! grep -q $volume .volumes; then
      echo "Adding volume $volume to .volumes"
      echo "#$volume" >>.volumes
    fi
  done

  # Remove entries from .volumes that are no longer in docker compose file
  for line in $(cat .volumes); do
    if ! docker compose volumes | grep -q "${line#\#}"; then
      echo "Removing $line from .volumes (no longer in compose file)"
      sed -i "\|^${line}|d" .volumes
    fi
  done

  echo "Finished backup for stack: $dir"
  echo

  cd -
}

fix_permissions() {
  echo "Fixing backup directory permissions..."
  docker run --rm \
    -v "$BACKUPS_DIR:/data" \
    alpine chown -R "$(id -u):$(id -g)" /data
}

# Main part
echo "Welcome to the backup script!"

for dir in "$SCRIPT_DIR"/*/; do
  if [ -r "$dir/docker-compose.yml" ]; then
    backup_stack "$dir"
  fi
done

fix_permissions
