
import myTcpSocket
import time # for time.sleep()

def testAddToTrace(s):
    print(s)
    
    
def checkClientSocket():
    print("Testing the myTcpClientSocket...")
    c = myTcpSocket.myTcpClientSocket(testAddToTrace)
    c.connect('192.168.2.113', 23)
    print("connected="+str(c.isConnected))
    if (c.isConnected):
        #print("sending something to the server")
        #c.transmit(bytes("Test", "utf-8"))
        for i in range(0, 1000):
            #print("waiting 1s")
            time.sleep(0.02)
            if (c.isRxDataAvailable()):
                d = c.getRxData()
                print("received " + str(d))
            #if ((i % 3)==0):
            #    print("sending something to the server")
            #    c.transmit(bytes("Test", "utf-8"))
            
checkClientSocket()