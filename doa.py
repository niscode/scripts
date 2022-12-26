# coding: utf-8

from tuning import Tuning
# usb_4_mic_array/Tuning.py を参照
import usb.core
import usb.util
import time

dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)

if dev:
    Mic_tuning = Tuning(dev)
    print(Mic_tuning.direction)
    while True:
        try:
            if Mic_tuning.read('SPEECH DETECTED') == 1:
                print(Mic_tuning.direction)
                print('    degから誰かが話しかけた...')
                time.sleep(1)
            # else:
            #     print(Mic_tuning.direction)
            #     print('    degから音が聞こえる...')
        except KeyboardInterrupt:
            break