#!/bin/sh

TRAEFIK_API_URL="${TRAEFIK_API_URL:-}"
if [ -z "$TRAEFIK_API_URL" ]; then
  echo "Error: TRAEFIK_API_URL is not set" >&2
  exit 1
fi

localhost_line=$(grep -E '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}[[:space:]]+.*localhost' /etc/hosts)
sleep 4

for router in $(wget -q -O - "$TRAEFIK_API_URL/api/http/routers" | grep -o '"name":"[^"]*"' | cut -d'"' -f4); do
  router_data=$(wget -q -O - "$TRAEFIK_API_URL/api/http/routers/$router")
  provider=$(echo "$router_data" | grep -o '"provider":"[^"]*"' | cut -d'"' -f4)
  if [ "$provider" = "docker" ]; then
    rule=$(echo "$router_data" | grep -o '"rule":"[^"]*"' | cut -d'"' -f4)
    if echo "$rule" | grep -q "Host"; then
      hostname=$(echo "$rule" | sed 's/.*Host(`\([^`]*\)`).*/\1/')

      # Check if hostname already exists in localhost line
      if ! echo "$localhost_line" | grep -q "$hostname"; then
        new_record="$localhost_line $hostname"

        tmpfile="/tmp/hosts.$$"
        # Create a new hosts file with the update
        sed "s|^$localhost_line$|$new_record|" /etc/hosts >"$tmpfile"
        # Overwrite the original (no rename, so works on bind mount)
        cat "$tmpfile" >/etc/hosts
        rm -f "$tmpfile"

        echo "Updated record: $new_record"
      else
        echo "$hostname already exists in localhost line"
      fi
    fi
  fi
done
