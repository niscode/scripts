# coding: utf-8

import sys
import socket
import time

from datetime import datetime

def __sendmsg(soc, msg) :
    result = True
    n = len(msg)
    remain = n
    while remain > 0 :
        try :
            t = soc.send(msg)
            remain -= t
            msg = msg[t:]
        except :
            result = False
            break
    return result

def doCommu4Command(soc, cmd) :
    result = True


    cmdlist = []
    initstr = 'M0 0 800 -40 -800 40 0 0 0 0 0 0 -50 0\n'
    if cmd == '*init*' :
        cmdlist = ["S\n"]
    elif cmd == '*terminate*' :
        cmdlist = ["E\n"]
    elif cmd == 'tlc;MoveRightHand' :
        #cmdlist.append(initstr)
        #cmdlist.append("*%d" % 2000)
        cmdlist.append("M0 0 800 -40 800 40 0 0 0 0 0 0 -50 0\n")
        cmdlist.append("*%d" % 1000)
        cmdlist.append("M0 0 800 -40 -800 40 0 0 0 0 0 0 -50 0\n")
        #cmdlist.append("*%d" % 2000)
    elif cmd == 'tlc;MoveLeftHand' :
        #cmdlist.append(initstr)
        #cmdlist.append("*%d" % 2000)
        cmdlist.append("M0 0 -800 -40 -800 40 0 0 0 0 0 0 -50 0\n")
        cmdlist.append("*%d" % 1000)
        cmdlist.append("M0 0 800 -40 -800 40 0 0 0 0 0 0 -50 0\n")
        #cmdlist.append("*%d" % 2000)
    elif cmd == 'tlc;MoveBothHand' :
        #cmdlist.append(initstr)
        #cmdlist.append("*%d" % 2000)
        cmdlist.append("M0 0 -800 -40 800 40 0 0 0 0 0 0 -50 0\n")
        cmdlist.append("*%d" % 1000)
        cmdlist.append("M0 0 800 -40 -800 40 0 0 0 0 0 0 -50 0\n")
        #cmdlist.append("*%d" % 2000)
    else :
        pass

    for command in cmdlist :
        if len(command) == 0 : continue
        #print("command =", command)
        if command[0] == '*' :
            n = int(command[1:]) / 1000
            time.sleep(n)
        else :
            if not __sendmsg(soc, command.encode('utf-8')) :
                result = False
                break
            try :
                msg = soc.recv(1024)
            except :
                result = False
                break
            
    return result

#

def login(soc, sid):
    sf = soc.makefile()
    try :
        data = soc.recv(4096).decode()
        print(str(data))
        cmd = str(data.rstrip())
        line = 'id;%s' % sid
        #print(line)
        soc.send(line.encode('utf-8'))
        #rdata = soc.recv(4096).decode()
        # サーバから受信したデータを出力
        #print(rdata)
    except :
        print('サーバーとの通信に失敗しました。')
        sys.exit(0)
    
def loop(serversoc, adr,port, tlc):
    #tlc  = ("localhost", 1234)
    #tlc  = ("10.186.42.31", 1234)

    sota = (adr, port)
    st = serversoc.makefile()

    tlc_soc = None
    
    while True:
        if tlc_soc is None :
            tlc_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                tlc_soc.connect(tlc)
            except :
                print('Commu4Serverとの通信に失敗しました :', datetime.now())
                tlc_soc = None
                time.sleep(5)
                continue
            if not doCommu4Command(tlc_soc, '*init*') :
                print('Commu4Serverとの通信に失敗しました :', datetime.now())
                tlc_soc.close()
                tlc_soc = None
                time.sleep(5)
                continue

        try :
            data = st.readline().strip()
            #data = serversoc.recv(4096)
            print(data)
            #data = data.decode()
        except socket.timeout :
            continue
            
        cmd = str(data.rstrip())
        #cmd = st.readline()
        if len(cmd) <= 3 :
            continue
        #print(cmd)
        header = cmd[:3]
        if header == 'tlc' :
            if not doCommu4Command(tlc_soc, cmd) :
                print('Commu4Serverとの通信に失敗しました :', datetime.now())
                tlc_soc.close()
                tlc_soc = None
                continue
        else :
            try :
                sota_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sota_soc.connect(sota)
                sota_soc.send(cmd.encode('utf-8')) #(bytes(cmd))
                #cmd = st.readline()
                sota_soc.close()
                sota_soc = None
            except :
                print('SOTAとの通信に失敗しました :', datetime.now())

            if cmd == "cmd;motion;Nodding":
                print("Nodding")
            elif cmd == "cmd;motion;HeadShaking":
                print("HeadShaking")
            elif cmd == "cmd;motion;RightHandWaving":
                print("RightHandWaving")
            elif cmd == "cmd;motion;LeftHandWaving":
                print("LeftHandWaving")
            elif cmd == "cmd;motion;BothHandWaving":
                print("BothHandWaving")
            elif cmd == "cmd;motion;BothHandRaising":
                print("BothHandRaising")
            elif cmd == "cmd;end":
                print("End")
            else:
                pass
                    #print("Unknown command")

if __name__ == '__main__':
    if (len(sys.argv) != 7):
        print("Usage: {} <id> <server ip> <server port> <sota ip> <sota port> <teleco ip>".format(sys.argv[0]))
        sys.exit(1)

    sid = sys.argv[1]
    serverip = sys.argv[2]
    serverport = sys.argv[3]
    sotaip = sys.argv[4]
    sotaport = int(sys.argv[5])
    server = (serverip, int(serverport))
    tlc = (sys.argv[6], 1234)
    
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #soc.settimeout(10.0)
    try :
        soc.connect(server)
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except:
        print('serverとの接続に失敗しました。 : %s:%s' % (serverip, serverport))
        sys.exit(0)

        
    login(soc, sid)
    loop(soc, sotaip, sotaport, tlc)
    soc.close()
