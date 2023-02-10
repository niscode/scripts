#!/bin/sh
# arg1: 'id' = 1 or 2 or 3 〔default="1”〕   Set Login ID number for CAPF
# arg2: 'option1' = 0 or 1 〔default="1”〕   Set Headless Option
python3 ~/scripts/capf_auto_login.py 3 0 >> login.log