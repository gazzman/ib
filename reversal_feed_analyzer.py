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
            self.logger.debug('Processing %s: %s', str(reversal), str(data))
            times = [x[1] for x in data]
            if times[0] == times[1] == times[2]: 
                prices = [x[0] for x in data]
                self.evaluate_and_enter_reversal(rev_id, prices)

        msg = EWrapperMsgGenerator.realtimeBar(reqId, time, open_, high, low, 
                                               close, volume, wap, count)
        fnm = '%i_%s.csv' % (self.realtime_bars[reqId]['contract'].m_conId,
                             self.realtime_bars[reqId]['show'])
        self.datahandler(fnm, reqId, msg)

class ReversalAnalyzer(Client, Callback):
    timeslots = [dict()]*((datetime(1900, 1, 1, 16, 0)
                           -datetime(1900, 1, 1, 9, 30)).seconds/5)
    req_to_rev = dict()
    rev_to_data = dict()
    stk_opt_pairs = dict()
    
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

    def evaluate_and_enter_reversal(self, rev_id, prices):
        ticker, expiry, strike, qty, longshort = rev_id
        strike = Decimal(str(strike))
        call, stock, put = [Decimal(str(x)) for x in prices]
        result = call + strike - stock - put
        if (longshort == 'long'):
            self.logger.debug(self.eval_msg, rev_id, call, strike, stock, put, 
                              longshort, result)
            if strike < (stock + put) and result < self.threshold:
                message = self.gen_trade(ticker, expiry, strike, qty, 
                                         longshort, result)
                self.send_message(message)
                self.logger.info(enter_msg, message, result)
        elif (longshort == 'short'):
            result *= -1
            self.logger.debug(self.eval_msg, rev_id, call, strike, stock, put, 
                              longshort, result)
            if result < self.threshold:
                message = self.gen_trade(ticker, expiry, strike, qty, 
                                         longshort, result)
                self.send_message(message)
                self.logger.info(enter_msg, message, result)

    def gen_trade(self, symbol, expiry, strike, qty, longshort, limit):
        return '%s,%s,%f,%i,%s' % (symbol, expiry, strike, qty, longshort)

    def m_to_expiry(self, m_expiry):
        expiry = datetime.strptime(m_expiry, '%Y%m%d')
        expiry += timedelta(days=1)
        return expiry.strftime('%y%m%d')

    def gather_contracts(self, symbols, max_dte=30):
        self.max_dte = max_dte
        if type(symbols) == list:
            self.symbols = dict()
            for x in symbols: self.symbols[x] = {'qty': 1, 'low': Decimal('0'),
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
            while (s_req and o_req) not in self.fulfilled_con_reqs: sleep(.5)
            self.stk_opt_pairs[symbol] = (s_req, o_req)
        return self.stk_opt_pairs

    def gen_reversal_ids(self, symbol):
        expirys = [self.m_to_expiry(x.m_expiry) 
                   for x in self.req_contracts[self.stk_opt_pairs[symbol][1]]]
        strikes = [str(x.m_strike) 
                   for x in self.req_contracts[self.stk_opt_pairs[symbol][1]]]
        self.long_reversals = [(symbol, x, y, self.symbols[symbol]['qty'], 
                                'long') for x in expirys for y in strikes]
        self.short_reversals = [(symbol, x, y, self.symbols[symbol]['qty'], 
                                 'short') for x in expirys for y in strikes]
        for x in self.long_reversals + self.short_reversals: 
            self.rev_to_data[x] = [(None,None), (None,None), (None,None)]
        return self.rev_to_data

    def start_analyzing_reversal(self, symbol, qty=1):
        these_bar_ids = []
        # Start the realtime bars and generate the id maps
        s_bid_id = self.start_realtime_bars(self.req_contracts[\
                                            self.stk_opt_pairs[symbol][0]][0], 
                                            show='BID')
        s_ask_id = self.start_realtime_bars(self.req_contracts[\
                                            self.stk_opt_pairs[symbol][0]][0], 
                                            show='ASK')
        these_bar_ids += [s_bid_id, s_ask_id]
        self.req_to_rev[s_bid_id] = [(x, 1) for x in self.long_reversals]
        self.req_to_rev[s_ask_id] = [(x, 1) for x in self.short_reversals]
        for opt_con in self.req_contracts[self.stk_opt_pairs[symbol][1]]:
            expiry = self.m_to_expiry(opt_con.m_expiry)
            strike = opt_con.m_strike
            self.logger.debug(self.rtbars_opt_msg, symbol, expiry,
                              opt_con.m_right, Decimal(str(strike))*1000)
            opt_bid_id = self.start_realtime_bars(opt_con, show='BID')
            opt_ask_id = self.start_realtime_bars(opt_con, show='ASK')
            these_bar_ids += [opt_bid_id, opt_ask_id]
            if opt_con.m_right == 'C':
                self.req_to_rev[opt_bid_id] = [((symbol, expiry, strike, 
                                                self.symbols[symbol]['qty'],
                                                'short'), 0)]
                self.req_to_rev[opt_ask_id] = [((symbol, expiry, strike, 
                                                self.symbols[symbol]['qty'],
                                                'long'), 0)]
            elif opt_con.m_right == 'P':
                self.req_to_rev[opt_bid_id] = [((symbol, expiry, strike, 
                                                self.symbols[symbol]['qty'],
                                                'long'), 2)]
                self.req_to_rev[opt_ask_id] = [((symbol, expiry, strike, 
                                                self.symbols[symbol]['qty'],
                                                'short'), 2)]
        return these_bar_ids
