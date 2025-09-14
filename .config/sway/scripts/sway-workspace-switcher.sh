#!/bin/bash
# Sway workspace switcher with back-and-forth functionality like in i3wm
# Usage: ./sway-workspace-switcher.sh <WORKSPACE_ID>

SWAY_WORKSTATION_HISTORY=${SWAY_WORKSTATION_HISTORY:-/tmp/sway_workstation_history}
WORKSTATION_ID=$1
CURRENT_WS=$(swaymsg -t get_workspaces | jq -r '.[] | select(.focused==true) | .num')

append_to_history() {
  local ws=$1
  local last_entry=$(tail -1 "$SWAY_WORKSTATION_HISTORY" 2>/dev/null)
  if [[ "$ws" != "$last_entry" ]]; then
    echo "$ws" >>"$SWAY_WORKSTATION_HISTORY"
  fi
}

# Check if workspace ID was provided
if [[ -z "$WORKSTATION_ID" ]]; then
  echo "Error: No workspace ID provided" >&2
  echo "Usage: $0 <WORKSPACE_ID>" >&2
  exit 1
fi

# If requested workspace is the current one, go to previous workspace
if [[ "$WORKSTATION_ID" == "$CURRENT_WS" ]]; then
  # Get second to last workspace from history (previous workspace)
  PREVIOUS_WS=$(tail -2 "$SWAY_WORKSTATION_HISTORY" 2>/dev/null | head -1)
  if [[ -n "$PREVIOUS_WS" && "$PREVIOUS_WS" != "$CURRENT_WS" ]]; then
    WORKSTATION_ID="$PREVIOUS_WS"
    echo "Switching back to workspace $WORKSTATION_ID"
  else
    echo "No previous workspace found or same as current" >&2
    exit 1
  fi
else
  echo "Switching to workspace $WORKSTATION_ID"
fi

# Switch to the workspace
if swaymsg workspace "$WORKSTATION_ID" >/dev/null 2>&1; then
  # Append current workspace to history (before the switch)
  append_to_history "$CURRENT_WS"
  echo "Successfully switched to workspace $WORKSTATION_ID"
else
  echo "Error: Failed to switch to workspace $WORKSTATION_ID" >&2
  exit 1
fi
