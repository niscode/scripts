#python3 tlcclient.py CA001 ca-platform.org 11001 itb-teleco01 1890 10.186.42.29

# atr-dev02 env /// for ATR-demo (ATR net)
# python3 ~/teleco-v_scripts/wsc-json_atr-dev02.py "https://atr-dev02.ca-platform.org/api/login" "CA001" "CA001" "wss://atr-dev02-websocket.ca-platform.org" "10.186.42.46" "1890" "10.186.42.31" "11920"

# atr-dev02 env /// for hanazono-demo (ATR net)
python3 ~/teleco-v_scripts/wsc-json-hanazono.py "https://atr-dev02.ca-platform.org/api/login" "CA002" "CA002" "wss://atr-dev02-websocket.ca-platform.org" "10.186.42.36" "1890" "10.186.42.29" "11920"

# hanzono env /// for hanazono-demo (md-wlan)
# python3 ~/teleco-v_scripts/wsc-json-hanazono.py "https://hanazono.ca-platform.org/api/login" "CA001" "CA001" "wss://hanazono-websocket.ca-platform.org" "192.168.100.201" "1890" "192.168.100.202" "11920"
# python3 ~/teleco-v_scripts/wsc-json-hanazono.py "https://atr-dev02.ca-platform.org/api/login" "CA001" "CA001" "wss://atr-dev02-websocket.ca-platform.org" "192.168.100.201" "1890" "192.168.100.202" "11920"
