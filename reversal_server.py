#!/usr/local/bin/jython
from datetime import datetime
from time import sleep
import SocketServer
import sys
import threading

from reversal import Reversal

errmsg = 'Failed to specify long or short for ticker %s, expiry %s, strike %s'

r = Reversal(client_id=1001)

class TCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        reversal_position = self.request.recv(1024).strip()
        data = [x.strip() for x in reversal_position.split(',')]
        ticker, expiry, strike, qty, long = data
        if long.lower() == 'long': long = True
        elif long.lower() == 'short': long = False
        else: raise Exception(errmsg % (ticker, expiry, strike))
        order_id = r.enter_position(ticker, expiry, strike, qty=qty, long=long)

if __name__ == '__main__':
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
    server = SocketServer.TCPServer((HOST, PORT), TCPRequestHandler)
    server.serve_forever()
