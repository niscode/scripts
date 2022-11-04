#python3 tlcclient.py CA001 ca-platform.org 11001 itb-teleco01 1890 10.186.42.29

# (ATR net) atr-dev02 env /// for ATR-demo
# python3 ~/teleco-v_scripts/wsc-json_atr-dev02.py "https://atr-dev02.ca-platform.org/api/login" "CA001" "CA001" "wss://atr-dev02-websocket.ca-platform.org" "10.186.42.46" "1890" "10.186.42.31" "11920"

# (ATR net) atr-dev02 env /// for hanazono-demo
# python3 ~/teleco-v_scripts/wsc-json-hanazono.py "https://atr-dev02.ca-platform.org/api/login" "CA001" "CA001" "wss://atr-dev02-websocket.ca-platform.org" "10.186.42.46" "1890" "10.186.42.31" "11920"
# python3 ~/teleco-v_scripts/wsc-json-hanazono.py "https://atr-dev02.ca-platform.org/api/login" "CA002" "CA002" "wss://atr-dev02-websocket.ca-platform.org" "10.186.42.37" "1890" "10.186.42.75" "11920"

# (md-wlan) hanzono env /// for hanazono-demo
# ---- CA001
# python3 ~/teleco-v_scripts/wsc-json-hanazono.py "https://hanazono.ca-platform.org/api/login" "CA001" "CA001" "wss://hanazono-websocket.ca-platform.org" "192.168.100.121" "1890" "192.168.100.122" "11920"
# ---- CA002
python3 ~/teleco-v_scripts/wsc-json-hanazono.py "https://hanazono.ca-platform.org/api/login" "CA002" "CA002" "wss://hanazono-websocket.ca-platform.org" "192.168.100.121" "1890" "192.168.100.122" "11920"

# python3 ~/teleco-v_scripts/wsc-json-hanazono.py "https://atr-dev02.ca-platform.org/api/login" "CA001" "CA001" "wss://atr-dev02-websocket.ca-platform.org" "192.168.100.121" "1890" "192.168.100.122" "11920"
