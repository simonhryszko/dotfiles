# Update package lists and install FFmpeg
# apt-get update
# apt-get install -y ffmpeg #python3-pip python3-full yt-dlp
# xargs -n1 uv tool install <<<"ffmpeg python3-full python3-pip"

# python3 -m pip install yt-dlp
# npm install -g windmill-cli

uv tool install ffmpeg
uv pip install yt-dlp #--system --target /tmp/windmill/cache/python_3_11/global-site-packages

# Optional: Install additional codecs if needed
# apt-get install -y libavcodec-extra
