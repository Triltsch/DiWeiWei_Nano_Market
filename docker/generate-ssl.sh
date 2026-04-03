#!/usr/bin/env sh
set -eu

CERT_DIR="docker/ssl"
CERT_FILE="$CERT_DIR/server.crt"
KEY_FILE="$CERT_DIR/server.key"

mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -newkey rsa:4096 \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -days 365 \
  -subj "/C=DE/ST=BW/L=Stuttgart/O=DiWeiWei/CN=localhost"

echo "Self-signed certificate generated"
echo "  certificate: $CERT_FILE"
echo "  key:         $KEY_FILE"
openssl x509 -enddate -noout -in "$CERT_FILE"
