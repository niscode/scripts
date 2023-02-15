#!/bin/sh

# ❶roscoreを終了
pid_roscore=`ps -ax | grep roscore | grep python | awk '{ print $1 }'`
kill -9 $pid_roscore; echo ✅ roscore - done;

# ❷デモプロセスを終了
pid_demo=`ps -ax | grep python | grep demo | awk '{ print $1 }'`
kill -9 $pid_demo; echo ✅ デモ - done;

# ❸中継プロセスを終了
pid_bridge=`ps -ax | grep python | grep wsc | awk '{ print $1 }'`
kill -9 $pid_bridge; echo ✅ 中継 - done;

# ❹ナビゲーションプロセスを終了   関連するノードごと全終了させる
ps aux | grep ros | grep -v grep | awk '{ print "kill -9", $2 }' | sh; echo ✅ ナビゲーション - done;

echo プロセスを終了しました。最後にターミナルを閉じてください。