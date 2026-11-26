FROM debian:trixie-slim
RUN apt-get update && apt-get install -y \
    xfce4 \
    xfce4-goodies \
    picom \
    firefox-esr \
    zram-tools \
    && rm -rf /var/lib/apt/lists/*
CMD ["startxfce4"]