#!/usr/bin/env bash
# Source this file so variables stay in the current shell.
# Usage: source proxy-session.sh http://127.0.0.1:YOUR_HTTP_PORT
if [[ -z "${1:-}" ]]; then
  echo 'Usage: source proxy-session.sh http://HOST:HTTP_PORT'; return 1 2>/dev/null || exit 1
fi
case "$1" in
  http://*|https://*|socks5h://*) ;;
  *) echo '[ERROR] Include the proxy protocol.'; return 1 2>/dev/null || exit 1 ;;
esac
export http_proxy="$1" https_proxy="$1" HTTP_PROXY="$1" HTTPS_PROXY="$1"
export no_proxy="localhost,127.0.0.1,::1,0.0.0.0${no_proxy:+,$no_proxy}"
export NO_PROXY="$no_proxy"
echo '[OK] Current-shell proxy set. Local model traffic bypasses it.'
