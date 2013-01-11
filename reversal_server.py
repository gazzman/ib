#!/usr/local/bin/jython
from datetime import datetime
from time import sleep
import SocketServer
import sys
import threading

from reversal import Reversal

r = Reversal(client_id=1001)

errmsg = 'Failed to specify long or short for ticker %s, expiry %s, strike %s'

def gen_client_id():
    d = datetime.now().isoformat().split('T')[-1]
    d = ''.join(d.split(':'))
    d = ''.join(d.split('.'))
    return int(d[:-3])

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        reversal_position = self.request.recv(1024).strip()
        data = [x.strip() for x in reversal_position.split(',')]
        ticker, expiry, strike, qty, long = data
        if long.lower() == 'long': long = True
        elif long.lower() == 'short': long = False
        else: raise Exception(errmsg % (ticker, expiry, strike))
        client_id = gen_client_id()
        order_id = r.enter_position(ticker, expiry, strike, qty=qty, long=long)

if __name__ == '__main__':
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    server.serve_forever()
    r.client.disconnect()
