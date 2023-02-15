#!/bin/sh

# Chromeを自動起動
(echo ✅ デモ - done; python3 ~/scripts/capf_auto_login.py 3 0 >> login.log) $

# ROSCoreを実行
(echo ✅ roscore - done; roscore) &

##  telecoデモプログラムを別プロセスで時差を持たせ実行 引数：〔commu_ip〕　
echo "## Demo Program Starts..." 
(sleep 5; echo ✅ デモ - done; python3 ~/scripts/demo_Suidobashi.py "10.186.42.31" >> output_demo.txt) &

### teleco-CAPF間コマンド中継プログラムを別プロセスで実行
echo "### Bridge Program Starts..."
(echo ✅ 中継 - done; python3 ~/scripts/wsc-json-suidobashi.py "https://ignis2.ca-platform.org/api/login" "CA003" "CA003" "wss://ignis2-websocket.ca-platform.org" "10.186.42.91" "1890" "10.186.42.31" "11920" >> output_bridge.txt) &

#### navigation_stackを起動
# (sleep 10; roslaunch telecoV suidobashi_navigation.launch) &
(sleep 10; echo ✅ ナビゲーション - done; roslaunch telecoV dual_navigation.launch) &