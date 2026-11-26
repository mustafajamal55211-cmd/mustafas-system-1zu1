#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y xfce4 xfce4-goodies picom firefox-esr zram-tools network-manager bluez
echo 'ZRAM_ENABLED=yes' > /etc/default/zramswap
echo 'PERCENT=50' >> /etc/default/zramswap
systemctl enable zramswap
apt-get clean