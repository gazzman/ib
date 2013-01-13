#!/usr/local/bin/jython
from datetime import datetime
from time import sleep
import SocketServer
import sys
import threading

from ib.reversal import Reversal

errbase = 'for ticker %s, expiry %s, strike %s, qty %s'
errmsg1 = ' '.join(['Failed to specify long or short', errbase])
errmsg2 = ' '.join(['%s REVERSAL position NOT entered', errbase])
infomsg = ' '.join(['%s REVERSAL position entered', errbase,
                    'with order id %i']) 

r = Reversal()

class TCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        reversal_position = self.request.recv(1024).strip()
        data = [x.strip() for x in reversal_position.split(',')]
        ticker, expiry, strike, qty, longshort = data
        if longshort.lower() == 'long': ls = True
        elif longshort.lower() == 'short': ls = False
        else: raise Exception(errmsg1 % (ticker, expiry, strike))
        oid = r.enter_position(ticker, expiry, strike, qty=qty, longshort=ls)
        if not oid:
            r.client.logger.error(errmsg2 % (longshort.upper(), ticker, expiry,
                                             strike, qty))
        else:
            r.client.logger.info(infomsg % (longshort.upper(), ticker, expiry,
                                            strike, qty, oid))

if __name__ == '__main__':
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
    server = SocketServer.TCPServer((HOST, PORT), TCPRequestHandler)
    server.serve_forever()
