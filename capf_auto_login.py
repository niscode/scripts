#!/usr/bin/env python
# coding: utf-8
### for miniPC

# chromedriver-binary==109.0.5414.25.0
import chromedriver_binary
# selenium   4.7.2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import time
import argparse
import sys
from datetime import datetime

parser = argparse.ArgumentParser(description='引数にLogin IDとオプションを指定せよ')
parser.add_argument('id', default="1", help='Set Login ID number for CAPF')
parser.add_argument('option1', default="1", help='Set Headless Option 1 - true, 0 - false')
args = parser.parse_args()
id = "CA00" + args.id
isHeadless = args.option1

# カメラ(マイク)の使用を許可しますか」ダイアログを回避
options = webdriver.ChromeOptions()
if(isHeadless == "1"):
    options.add_argument("--headless")# 実行時の引数に応じてヘッドレスオプションを指定

options.add_argument("--use-fake-ui-for-media-stream")# ダイアログを回避オプションを指定
# options.add_argument("--use-fake-device-for-media-stream")# 偽のカメラ・マイクデバイスを用意するオプションを指定

# Chrome/Chromiumの立ち上げ
driver = webdriver.Chrome(options=options)

# ページ接続
driver.get('https://ignis2.ca-platform.org/login')

# キー入力
# driver.find_element_by_xpath('//*[@id="name"]').send_keys("CA001")
driver.find_element(By.XPATH, '//*[@id="name"]').send_keys(id)
driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(id)


# デバイス指定
input1 = "ReSpeaker 4 Mic Array (UAC1.0) マルチチャネル"
output1 = "Yamaha YVC-200 Analog Mono"
output2 = "Yamaha YVC-200 モノ"
time.sleep(3)

#  マイクの選択 ReSpeaker -> なければYamaha
try:
    Select(driver.find_element(By.XPATH, '//*[@id="deviceIdMic"]')).select_by_visible_text(input1)
except:
    print("ReSpeakerとの接続を確認できない。")
    try:
        Select(driver.find_element(By.XPATH, '//*[@id="deviceIdMic"]')).select_by_visible_text(output1)
    except:
        Select(driver.find_element(By.XPATH, '//*[@id="deviceIdMic"]')).select_by_visible_text(output2)

#  スピーカーの選択
try:
    Select(driver.find_element(By.XPATH, '//*[@id="deviceIdSpk"]')).select_by_visible_text(output1)
except:
    Select(driver.find_element(By.XPATH, '//*[@id="deviceIdSpk"]')).select_by_visible_text(output2)


# ログインボタン入力
driver.find_element(By.XPATH, '//*[@name="btn"]').click()

# 接続を12時間維持
# time.sleep(43200)

# 接続を無限に設定
while True:
	try:
		time.sleep(10)
	except KeyboardInterrupt :
		print(datetime.now() + "コマンドの割り込みにより接続を終了します。")
		break

# クロームの終了処理
driver.close()
sys.exit(1)