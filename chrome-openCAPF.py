#　ライブラリ読み込み
# selenium == 4.7.2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
# ChromeのWebDriverライブラリをインポート（不要）
# import chromedriver_binary

#　Chromeの立ち上げ
driver=webdriver.Chrome()

#　ページ接続
driver.get('https://atr-dev01.ca-platform.org/login')

#　id/pw 入力
driver.find_element(By.XPATH, '//*[@id="name"]').send_keys("CA001")
driver.find_element(By.XPATH, '//*[@id="password"]').send_keys("CA001")

#　ログインボタンのクリック
driver.find_element(By.XPATH, '/html/body/div/form/main/div/div/div[9]/button').click()

#　10秒終了を待つ
# time.sleep(10)

#　Chromeの終了処理
# driver.close()

