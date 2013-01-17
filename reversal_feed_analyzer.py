#!/usr/local/bin/jython
from datetime import datetime, timedelta
from decimal import Decimal
from time import sleep  
import logging
import socket
import sys

from com.ib.client import EWrapper, EWrapperMsgGenerator, EClientSocket
from com.ib.client import Contract

from ib.client import Client, CallbackBase
import ib.client

ib.client.LOGLEVEL = logging.INFO

class Callback(CallbackBase):
    fulfilled_con_reqs = dict()

    mon_stk_msg = 'Monitoring STK contract %i: %-6s'
    opt_id = '%-6s%s%s%08i'
    rtbars_opt_msg = ' '.join(['Starting realtime bars for', opt_id])
    mon_opt_msg = ' '.join(['Monitoring OPT contract %i:', opt_id])
    eval_msg = 'Evaluating %s: '
    eval_msg += 'call %0.3f, strike %0.3f, stock %0.3f, put %0.3f, %s %0.3f'
    enter_msg = 'Sent trade: %s for %0.3f'

    def contractDetails(self, reqId, contractDetails):
        c = contractDetails.m_summary
        if reqId not in self.req_contracts:  self.req_contracts[reqId] = list()
        if c.m_secType == 'STK': 
            self.req_contracts[reqId].append(c)
            self.logger.debug(self.mon_stk_msg, c.m_conId, c.m_symbol)
        elif c.m_secType == 'OPT':
            expiry = datetime.strptime(c.m_expiry, '%Y%m%d')
            strike = Decimal(str(c.m_strike))
            low = self.symbols[c.m_symbol]['low']
            hi = self.symbols[c.m_symbol]['hi']
            dte = (expiry - datetime.now()).days
            if dte <= self.max_dte and low <= strike <= hi:
                self.logger.debug(self.mon_opt_msg, c.m_conId, c.m_symbol, 
                                  self.m_to_expiry(c.m_expiry), c.m_right,
                                  strike*1000)
                self.req_contracts[reqId].append(c)

        msg = 'reqId = %i received details for'
        msg = ' '.join([msg,  'con_id: %i symbol: %s, secType: %s'])
        msg_data = (reqId, c.m_conId, c.m_symbol, c.m_secType)
        self.msghandler(msg % msg_data, req_id=reqId)

    def contractDetailsEnd(self, reqId):
        self.fulfilled_con_reqs[reqId] = datetime.now()
        msg = EWrapperMsgGenerator.contractDetailsEnd(reqId)
        self.msghandler(msg)

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, 
                    count):
        for reversal in self.req_to_rev[reqId]:
            rev_id, pos = reversal
            self.rev_to_data[rev_id][pos] = (close, time)
            data = self.rev_to_data[rev_id]
            self.logger.debug('Processing %s: %s', reversal, str(data))
            times = [x[1] for x in data]
            if times[0] == times[1] == times[2]: 
                prices = [Decimal(str(x[0])) for x in data]
                self.evaluate_reversal(rev_id, prices)
        
        msg = EWrapperMsgGenerator.realtimeBar(reqId, time, open_, high, low, 
                                               close, volume, wap, count)
        fnm = '%i_%s.csv' % (self.realtime_bars[reqId]['contract'].m_conId,
                             self.realtime_bars[reqId]['show'])
        self.datahandler(fnm, reqId, msg)

class ReversalAnalyzer(Client, Callback):
    timeslots = [dict()]*((datetime(1900, 1, 1, 16, 0)
                           -datetime(1900, 1, 1, 9, 30)).seconds/5)

    def __init__(self, rev_server_host, rev_server_port, client_id=70,
                 threshold=-0.04):
        self.rev_server_host = rev_server_host
        self.rev_server_port = rev_server_port
        self.threshold = Decimal(str(threshold))
        self.client_id = client_id
        self.init_logger()
        self.req_id = 0
        self.m_client = EClientSocket(self)

    def time_to_i(timestring):
        return (datetime.strptime(timestring, '%H:%M:%S') 
                - datetime(1900, 1, 1, 9, 30)).seconds/5

    def send_message(self, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.rev_server_host, self.rev_server_port))
        sock.sendall(message + '\n')
        sock.close()

    def evaluate_reversal(self, rev_id, rev_data):
        ticker, expiry, strike, qty, longshort = rev_id.split(',')
        strike = Decimal(strike)
        call, stock, put = rev_data
        result = call + strike - stock - put
        if (longshort == 'long'):
            self.logger.debug(self.eval_msg, rev_id, call, strike, stock, put, 
                              longshort, result)
            if strike < stock and result < self.threshold:
                self.send_message(rev_id)
                self.logger.info(enter_msg, rev_id, result)
        elif (longshort == 'short'):
            result *= -1
            self.logger.debug(self.eval_msg, rev_id, call, strike, stock, put, 
                              longshort, result)
            if result < self.threshold:            
                self.send_message(rev_id)
                self.logger.info(enter_msg, rev_id, result)

    def reversal_id(self, ticker, expiry, strike, qty, long_or_short):
        return ','.join([ticker, expiry, strike, qty, long_or_short])

    def m_to_expiry(self, m_expiry):
        expiry = datetime.strptime(m_expiry, '%Y%m%d')
        expiry += timedelta(days=1)
        return expiry.strftime('%y%m%d')

    def gather_contracts(self, symbols, max_dte=30):
        qty = '1'
        self.req_to_rev = dict()
        self.rev_to_data = dict()
        self.max_dte = max_dte
        if type(symbols) == list:
            self.symbols = dict()
            for x in symbols: self.symbols[x] = {'low': Decimal('0'),
                                                'hi': Decimal(str(sys.maxint))}
        else: self.symbols = symbols
        for symbol in self.symbols:
            # Get the contracts
            stock = {'m_symbol': symbol, 'm_secType': 'STK',
                     'm_currency': 'USD', 'm_exchange': 'SMART'}
            s_req = self.request_contract(stock)
            options = {'m_symbol': symbol, 'm_secType': 'OPT',
                       'm_currency': 'USD', 'm_exchange': 'SMART'}
            o_req = self.request_contract(options)
            while (s_req and o_req) not in self.fulfilled_con_reqs:
                print self.fulfilled_con_reqs.keys()
                sleep(.5)

            # Create the reversal ids and populate data map
            expirys = [self.m_to_expiry(x.m_expiry) 
                        for x in self.req_contracts[o_req]]
            strikes = [str(x.m_strike) for x in self.req_contracts[o_req]]
            long_reversals = [self.reversal_id(symbol, x, y, qty, 'long')
                                 for x in expirys for y in strikes]
            short_reversals = [self.reversal_id(symbol, x, y, qty, 'short')
                                  for x in expirys for y in strikes]
            for x in long_reversals + short_reversals: 
                self.rev_to_data[x] = [(None,None), (None,None), (None,None)] 

            # Start the realtime bars and generate the id maps
            s_bid_id = self.start_realtime_bars(self.req_contracts[s_req][0], 
                                                show='BID')
            s_ask_id = self.start_realtime_bars(self.req_contracts[s_req][0],
                                                show='ASK')
            self.req_to_rev[s_bid_id] = [(x, 1) for x in long_reversals]
            self.req_to_rev[s_ask_id] = [(x, 1) for x in short_reversals]
            for opt_con in self.req_contracts[o_req]:
                expiry = self.m_to_expiry(opt_con.m_expiry)
                strike = str(opt_con.m_strike)
                self.logger.debug(self.rtbars_opt_msg, symbol, expiry,
                                  opt_con.m_right, Decimal(strike)*1000)
                opt_bid_id = self.start_realtime_bars(opt_con, show='BID')
                opt_ask_id = self.start_realtime_bars(opt_con, show='ASK')
                if opt_con.m_right == 'C':
                    args = (symbol, expiry, strike, qty, 'short')
                    self.req_to_rev[opt_bid_id] = [(self.reversal_id(*args), 0)]
                    args = (symbol, expiry, strike, qty, 'long')
                    self.req_to_rev[opt_ask_id] = [(self.reversal_id(*args), 0)]
                elif opt_con.m_right == 'P':
                    args = (symbol, expiry, strike, qty, 'long')
                    self.req_to_rev[opt_bid_id] = [(self.reversal_id(*args), 2)]
                    args = (symbol, expiry, strike, qty, 'short')
                    self.req_to_rev[opt_ask_id] = [(self.reversal_id(*args), 2)]
