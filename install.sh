#!/usr/bin/env bash

set -u
set -e

if [ "$(id -u)" != "0" ]; then
    echo 'Must be run as root.' > /dev/stderr
    exit 1
fi

path="$(cd "$(dirname $0)"; pwd)"
cp -a "${path}/chutbot.py" /usr/local/bin/chutbot
chmod a+x /usr/local/bin/chutbot
cp -a "${path}/chutbot.service" /etc/systemd/system/chutbot.service
systemctl daemon-reload
systemctl enable chutbot.service
addgroup --system -q chutbot
adduser --system --home /var/local/lib/chutbot --shell /bin/rbash --ingroup chutbot --disabled-password --disabled-login --gecos 'ChutBot' -q chutbot
adduser -q chutbot audio
