#!/bin/bash

download() {
  local url="$1"
  local dir="$2"
  local cache_file="$dir/.cache"

  # Check if URL is in cache, if not add it
  if ! grep -q "^$url|" "$cache_file" 2>/dev/null; then
    local title=$(yt-dlp --skip-download --get-title "$url" 2>/dev/null)
    [[ -n "$title" ]] && echo "$url|$title" >>"$cache_file"
  fi

  # Get title from cache
  local title=$(grep "^$url|" "$cache_file" 2>/dev/null | cut -d'|' -f2-)

  # Check if we have title
  if [[ -z "$title" ]]; then
    echo "ERROR: Cannot process URL: $url"
    return
  fi

  # Check if file exists (any audio extension)
  if ls "$dir"/* 2>/dev/null | grep -q "$title"; then
    echo "EXISTS: $title"
    return
  fi

  # Download audio
  echo "DOWNLOADING: $title"
  cd "$dir" && yt-dlp -x "$url"
}

process_dir() {
  local dir="$1"

  # Process subdirectories first
  for subdir in "$dir"/*; do
    [[ -d "$subdir" ]] && process_dir "$subdir"
  done

  # Process .urls file if exists
  if [[ -f "$dir/.urls" ]]; then
    echo "Processing: $dir"
    while read -r url; do
      [[ -n "$url" && ! "$url" =~ "^#" ]] && download "$url" "$dir"
    done <"$dir/.urls"
  else
    echo "In $dir directory is not file '.urls' - if you create it, it will be processed"
  fi
}

# Main
if [[ -z "$1" || ! -d "$1" ]]; then
  echo "Error: Please provide a valid directory."
  exit 1
fi

process_dir "$1"
