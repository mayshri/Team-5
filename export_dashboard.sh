#!/bin/bash

apikey=$(cat apikey.txt)

curl -s -X GET --insecure -H "Authorization: Bearer $apikey" -H "Content-Type: application/json" http://localhost:3000/api/dashboards/uid/3muOLut7k | python3 -c "import sys, time;\
time.sleep(1); print('{\"dashboard\":' + '\"id\":\"null\"'.join(sys.stdin.read().split('\"dashboard\":', maxsplit=1)[-1].split('\"id\":1', maxsplit=1)))" > dashboard.json
