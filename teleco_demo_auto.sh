#!/bin/sh
# ROSCoreを実行
echo "# ROSCore Starts..."
roscore &

##  telecoデモプログラムを別プロセスで時差を持たせ実行 引数：〔commu_ip〕　
echo "## Demo Program Starts..." 
(sleep 10; echo done; python3 ~/scripts/demo_IGNIS.py "10.186.42.31" >> output_demo.txt) &

### teleco-CAPF間コマンド中継プログラムを別プロセスで実行
echo "### Bridge Program Starts..."
python3 ~/scripts/wsc-json-IGNIS.py "https://ignis2.ca-platform.org/api/login" "CA003" "CA003" "wss://ignis2-websocket.ca-platform.org" "10.186.42.91" "1890" "10.186.42.31" "11920" >> outpu_bridge.txt &