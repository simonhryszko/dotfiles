FROM ghcr.io/windmill-labs/windmill:main

RUN apt update
RUN apt install ffmpeg -y

RUN apt install python3-pip -y
# RUN pip install -U openai-whisper --break-system-packages

# Configure git safe directory for Obsidian
RUN git config --global --add safe.directory /obsidian

# Install yq-go
ENV VERSION=v4.48.1
ENV PLATFORM=linux_amd64
RUN wget https://github.com/mikefarah/yq/releases/download/${VERSION}/yq_${PLATFORM} -O /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq

CMD ["windmill"]
