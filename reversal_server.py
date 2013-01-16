#!/usr/local/bin/jython
from datetime import datetime
from time import sleep
import SocketServer
import logging
import signal
import sys
import threading

from ib.reversal import Reversal

logger = logging.getLogger('ib.client')

errbase = 'for ticker %s, expiry %s, strike %s, qty %s'
errmsg1 = ' '.join(['Failed to specify long or short', errbase])
errmsg2 = ' '.join(['%s REVERSAL position NOT entered', errbase])
infomsg1 = ' '.join(['%s REVERSAL position entered', errbase,
                     'with order id %i']) 
infomsg2 = ' '.join(['%s REVERSAL position entered', errbase,
                     'with order ids %i, %i, %i']) 

r = Reversal()

class TCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        message = self.request.recv(1024).strip()
        data = [x.strip() for x in message.split(',')]
        if len(data) == 5:
            ticker, expiry, strike, qty, longshort = data
            if longshort.lower() == 'long': ls = True
            elif longshort.lower() == 'short': ls = False
            else: raise Exception(errmsg1 % (ticker, expiry, strike))
            oid = r.enter_position(ticker, expiry, strike, qty=qty, 
                                   longshort=ls)
            if not oid:
                logger.error(errmsg2 % (longshort.upper(), ticker, expiry,
                                        strike, qty))
            elif type(oid) == int:
                logger.info(infomsg1 % (longshort.upper(), ticker, expiry,
                                        strike, qty, oid))
            elif type(oid) == list:
                logger.info(infomsg2 % (longshort.upper(), ticker, expiry, 
                                        strike, qty, oid[0], oid[1], oid[2]))
            else: logger.error('Something is wrong with the returned order id')
        elif message == 'CANCEL OPEN ORDERS': r.client.cancel_open_orders()
        else: raise Exception("Message '%s' not recognized" % message)

if __name__ == '__main__':
    HOST = sys.argv[1]
    PORT = int(sys.argv[2])
    if len(sys.argv) == 4:  
        if sys.argv[3].strip("'").lower() == 'papertrader': r.paper_trader=True
        else: raise Exception("Arguments are: HOST PORT ['papertrader']")
    server = SocketServer.TCPServer((HOST, PORT), TCPRequestHandler)
    logger.warn('Reversal server started. Listeing on socket %s:%i' 
                         % (HOST, PORT))
    def cleanup(signal, frame):
        server.server_close()
        r.client.disconnect()
        logger.warn('Reversal server shutdown')
        sys.exit(0)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)
    server.serve_forever()
