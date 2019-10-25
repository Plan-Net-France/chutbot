#!/usr/bin/env bash

set -u
set -e

if [ "$(id -u)" != "0" ]; then
    echo 'Must be run as root.' > /dev/stderr
    exit 1
fi

addgroup --system -q chutbot
adduser --system --home /var/local/lib/chutbot --shell /bin/rbash --ingroup chutbot --disabled-password --disabled-login --gecos 'ChutBot' -q chutbot
adduser -q chutbot audio
path="$(cd "$(dirname $0)"; pwd)"
install -o chutbot -g chutbot -m 0644 -p "${path}/example.ini" /var/local/lib/chutbot/example.ini
install -o root -g root -m 0755 -p "${path}/chutbot.py" /usr/local/bin/chutbot
install -o root -g root -m 0644 -p "${path}/chutbot.service" /etc/systemd/system/chutbot.service
systemctl daemon-reload
systemctl enable chutbot.service
