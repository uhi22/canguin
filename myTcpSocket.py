
# Client on a non-blocking socket
#
# explanation of socket handling:
# https://docs.python.org/3/howto/sockets.html
# https://realpython.com/python-sockets/
# https://stackoverflow.com/questions/5308080/python-socket-accept-nonblocking
#


import socket
import select
import sys # for argv
import time # for time.sleep()
import errno
import os
import subprocess
# from configmodule import getConfigValue, getConfigValueBool

class myTcpClientSocket():
    def __init__(self, callbackAddToTrace):
        self.callbackAddToTrace = callbackAddToTrace
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use
        # The SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state, without
        # waiting for its natural timeout to expire.
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.isConnected = False
        self.rxData = []

    def addToTrace(self, s):
        self.callbackAddToTrace(s)
        
    def connect(self, host, port):
        try:
            self.addToTrace("TCP connecting to " + str(host) + " port " + str(port) + "...")
            # for connecting, we are still in blocking-mode because
            # otherwise we run into error "[Errno 10035] A non-blocking socket operation could not be completed immediately"
            # We set a shorter timeout, so we do not block too long if the connection is not established:
            #print("step1")
            self.sock.settimeout(0.5)
            #print("step2")

            # https://stackoverflow.com/questions/71022092/python3-socket-program-udp-ipv6-bind-function-with-link-local-ip-address-gi
            # While on Windows10 just connecting to a remote link-local-address works, under
            # Raspbian the socket.connect says "invalid argument".
            # host = "2003:d1:170f:d500:1744:89d:d921:b20f" # works
            # host = "2003:d1:170f:d500:2052:326e:cef9:ad07" # works
            # host = "fe80::c690:83f3:fbcb:980e" # invalid argument. Link local address needs an interface specified.
            # host = "fe80::c690:83f3:fbcb:980e%eth0" # ok with socket.getaddrinfo
            if (os.name != 'nt'):
                # We are at the Raspberry
                #print(host[0:5].lower())
                if (host[0:5].lower()=="fe80:"):
                    #print("This is a link local address. We need to add %eth0 at the end.")
                    ethInterface = getConfigValue("eth_interface") # e.g. "eth0"
                    host = host + "%" + ethInterface
            socket_addr = socket.getaddrinfo(host,port,socket.AF_INET,socket.SOCK_DGRAM,socket.SOL_UDP)[0][4]
            
            #print(socket_addr)
            #print("step2b")
            # https://stackoverflow.com/questions/5358021/establishing-an-ipv6-connection-using-sockets-in-python
            #  (address, port, flow info, scope id) 4-tuple for AF_INET6
            # On Raspberry, the ScopeId is important. Just giving 0 leads to "invalid argument" in case
            # of link-local ip-address.
            #self.sock.connect((host, port, 0, 0))
            self.sock.connect(socket_addr)
            #print("step3")
            self.sock.setblocking(0) # make this socket non-blocking, so that the recv function will immediately return
            self.isConnected = True
        except socket.error as e:
            self.addToTrace("TCP connection failed" + str(e))
            self.isConnected = False

    def disconnect(self):
        # When connection is broken, the OS may still keep the information of socket usage in the background,
        # and this could raise the error "A connect request was made on an already connected socket" when
        # we try a simple connect again. 
        # This is explained here:
        # https://www.codeproject.com/Questions/1187207/A-connect-request-was-made-on-an-already-connected
        try:
            self.sock.close() # Close is not just closing. It means destroying the socket object. So we
            # need a new one:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # https://stackoverflow.com/questions/29217502/socket-error-address-already-in-use
            # The SO_REUSEADDR flag tells the kernel to reuse a local socket in TIME_WAIT state, without
            # waiting for its natural timeout to expire.
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)            
            pass
        except socket.error as e:
            # if it was already closed, it is also fine.
            pass
        self.isConnected = False
            
    def transmit(self, msg):
        if (self.isConnected == False):
            # if not connected, just ignore the transmission request
            return -1
        totalsent = 0
        MSGLEN = len(msg)
        while (totalsent < MSGLEN) and (self.isConnected):
            try:
                sent = self.sock.send(msg[totalsent:])
                if sent == 0:
                    self.isConnected = False
                    self.addToTrace("TCP socket connection broken")
                    return -1
                totalsent = totalsent + sent
            except:
                self.isConnected = False
                return -1
        return 0 # success
        
    def isRxDataAvailable(self):
        # check for availability of data, and get the data from the socket into local buffer.
        if (self.isConnected == False):
            return False
        blDataAvail=False
        try:
            msg = self.sock.recv(4096)
        except socket.error as e:
            err = e.args[0]
            if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                # this is the normal case, if no data is available
                # print('No data available')
                pass
            else:
                # a "real" error occurred
                # print("real error")
                # print(e)
                self.isConnected = False
        else:
            if len(msg) == 0:
                # print('orderly shutdown on server end')
                self.isConnected = False
            else:
                # we received data. Store it.
                self.rxData = msg
                blDataAvail=True
        return blDataAvail
        
    def getRxData(self):
        # provides the received data, and clears the receive buffer
        d = self.rxData
        self.rxData = []
        return d 




def testAddToTrace(s):
    print(s)

def testClientSocket():
    print("Testing the myTcpClientSocket...")
    c = myTcpClientSocket(testAddToTrace)
    #c.connect('fe80::e0ad:99ac:52eb:85d3', 15118)
    #c.connect('fe80::e0ad:99ac:52eb:9999', 15118)
    #c.connect('localhost', 15118)
    c.connect('192.168.2.113', 23)
    print("connected="+str(c.isConnected))
    if (c.isConnected):
        print("sending something to the server")
        c.transmit(bytes("Test", "utf-8"))
        for i in range(0, 10):
            print("waiting 1s")
            time.sleep(1)
            if (c.isRxDataAvailable()):
                d = c.getRxData()
                print("received " + str(d))
            if ((i % 3)==0):
                print("sending something to the server")
                c.transmit(bytes("Test", "utf-8"))
            
    print("end")

def testExtra():
    print("testExtra")
    #findLinkLocalIpv6Address()
    

if __name__ == "__main__":
    print("Testing myTcpSocket.py....")
    
    if (len(sys.argv) == 1):
        print("Use command line argument c for clientSocket")
        exit()
    if (sys.argv[1] == "c"):
        testClientSocket()
        exit()
    if (sys.argv[1] == "x"):
        testExtra()
        exit()
    print("Use command line argument c for clientSocket or s for serverSocket")
