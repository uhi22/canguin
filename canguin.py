#
# canguin main module
#

import tkinter as tk
import myTcpSocket
import time # for time.sleep()
from helpers import prettyHexMessage

strCanLogMessage = ""

def testAddToTrace(s):
    print(s)
    
def decodeRxCanMessage(rxid, rxdlc, payload):
    global strCanLogMessage
    blEndOfLine = 0
    if (rxid == 0x56B) and (rxdlc==8):
        for i in range(0, len(payload)):
            x = payload[i]
            if (x==0x0d):
                blEndOfLine = 1
            if (x<0x20):
                x=0x20 # make unprintable character to space.
            strCanLogMessage+=chr(x) # convert ASCII code to string
    if (blEndOfLine>0):
        print("# " + strCanLogMessage)
        strCanLogMessage = ""

def initTelnet():
    global telnetsocket
    print("Creating telnet connection...")
    telnetsocket = myTcpSocket.myTcpClientSocket(testAddToTrace)
    telnetsocket.connect('192.168.2.113', 23)
    print("connected="+str(telnetsocket.isConnected))
    
def cyclicTelnet():
    global telnetsocket
    if (telnetsocket.isConnected):
        #print("sending something to the server")
        #c.transmit(bytes("Test", "utf-8"))
        if (telnetsocket.isRxDataAvailable()):
            rxData = telnetsocket.getRxData()
            #print("received " + str(rxData))
            #print(prettyHexMessage(rxData))
            # we here receive one or more of GVRET messages. The messages which contain
            # CAN data are starting with 0xF1 0x00, and are 20 bytes long.
            blFinished = 0
            while (blFinished==0):
                if (len(rxData)>=20):
                    header = rxData[0] << 8 + rxData[1]
                    #print(hex(header))
                    if (header == 0xf100):
                        rxTimestamp_us = rxData[2] + (rxData[3]<<8) + (rxData[4]<<16) + (rxData[5]<<24)
                        rxId = rxData[6] + (rxData[7]<<8) + (rxData[8]<<16) + (rxData[9]<<24)
                        rxDlc = rxData[10] & 0x0f
                        rxWhichBus = rxData[10] >> 4
                        rxPayload = rxData[11:19]
                        # 19 would be checksum, but is not used.
                        #print(hex(rxId) + ": " + prettyHexMessage(rxPayload))
                        decodeRxCanMessage(rxId, rxDlc, rxPayload)
                        rxData = rxData[20:] # done with the current 20 bytes. Take the next potentially.
                    else:
                        blFinished = 1
                else:
                    blFinished = 1
                
                
        #if ((i % 3)==0):
        #    print("sending something to the server")
        #    telnetsocket.transmit(bytes("Test", "utf-8"))

def storekeyname(event):
    global nKeystrokes
    global lastKey
    nKeystrokes+=1
    lastKey = event.keysym
    #worker.handleUserAction(lastKey)
    return 'break' # swallow the event


def cyclicMainfunction():
    cyclicTelnet()


root = tk.Tk()
root.geometry("400x350")
lastKey = ''
lblHelp = tk.Label(root, justify= "left")
lblHelp['text']="x=exit"
lblHelp.pack()
lblStatus = tk.Label(root, text="(Status)")
lblStatus.pack()

nKeystrokes=0
# Bind the keyboard handler to all relevant elements:
root.bind('<Key>', storekeyname)
#cbShowStatus("initialized")
root.update()
initTelnet()

nMainloops=0
while lastKey!="x":
    time.sleep(.01) # 'do some calculation'
    nMainloops+=1
    # print(str(nMainloops) + " " + str(nKeystrokes)) # show something in the console window
    root.update()
    cyclicMainfunction()

