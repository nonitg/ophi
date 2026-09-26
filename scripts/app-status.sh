#!/bin/bash
# Status code of each main screen on a running app (default port 8801); prints the error body on a 500.
port="${1:-8801}"
for p in / /cases/kowalchuk /cases/singh /cases/tremblay /cases/whitfield /cases/fontaine /cases/park /cases/okafor /cases/nguyen /cases/marchand /cases/rosco /cases/deng /cases/whitfield/packet /cases/fontaine/packet /recover /results /settings; do
  code=$(curl -s -o /tmp/ophi-status-body -w '%{http_code}' "http://127.0.0.1:$port$p")
  echo "$code $p"
  [ "$code" = "500" ] && head -c 600 /tmp/ophi-status-body && echo
done
