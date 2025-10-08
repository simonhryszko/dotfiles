#!/usr/bin/env bash
set -e

# Bash script designed to create backups from volumes
SCRIPT_DIR="$(realpath "$(dirname "$0")")"

# Check required parameters
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <stacks_directory> <backup_repository>"
  echo "  stacks_directory: Directory containing docker-compose stacks"
  echo "  backup_repository: Directory for restic backup repository"
  exit 1
fi

STACKS_DIR="$1"
BACKUPS_DIR="$(realpath "$2")"
VOLUMES_FILE=".volumes"

sync_volumes_file() {
  if [ ! -f .volumes ]; then
    if [ -n "$(docker compose volumes -q)" ]; then
      touch .volumes
    else
      return 0
    fi
  fi

  # Add volumes that are not yet in .volumes file
  for volume in $(docker compose volumes -q); do
    if ! grep -q $volume .volumes; then
      echo "Adding volume $volume to .volumes"
      echo "# $volume" >>.volumes
    fi
  done
}

backup_volume() {
  volume_name="$1"
  echo "Starting backup for volume: $volume_name"

  docker run --rm \
    --hostname "$(hostname)" \
    -v "$volume_name:/$volume_name:ro" \
    -v "$BACKUPS_DIR:/repo" \
    --env-file "$SCRIPT_DIR/.env" \
    -e RESTIC_REPOSITORY=/repo \
    restic/restic backup "/$volume_name" --compression max

  echo "Finished backup for volume: $volume_name"
  echo
}

backup_stack() {
  dir=$1
  cd "$dir"

  sync_volumes_file

  active_volumes=$(cat .volumes 2>/dev/null | grep -v '^#' | grep -vE '^$' || true)
  if [ -z "$active_volumes" ]; then
    cd - >/dev/null
    return 0
  fi

  echo "Starting backup for stack: $dir"

  if [ -n "$(docker compose ps --status running -q)" ]; then
    docker compose stop
    was_running=1
  fi

  for volume in $active_volumes; do
    backup_volume "$volume"
  done

  [ -n "$was_running" ] && docker compose start

  echo "Finished backup for stack: $dir"
  echo
  cd - >/dev/null
}

fix_permissions() {
  echo "Fixing backup directory permissions..."
  docker run --rm \
    -v "$BACKUPS_DIR:/data" \
    alpine chown -R "$(id -u):$(id -g)" /data
}

# Main part
echo "Welcome to the backup script!"
echo "Stacks directory: $STACKS_DIR"
echo "Backups directory: $BACKUPS_DIR"
echo

# Loop over subdirectories
for dir in "$STACKS_DIR"/*/; do
  if [ -f "$dir/docker-compose.yml" ]; then
    backup_stack "$dir"
  fi
done

fix_permissions

echo "All backups completed!"
