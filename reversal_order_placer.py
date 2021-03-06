#!/usr/local/bin/jython
from time import sleep
from decimal import Decimal
import java.util.Vector as Vector
import logging
import sys

from com.ib.client import ComboLeg, Contract, Order

from ib.client import Client

logger = logging.getLogger('ib.client')

class Reversal():
    action_base = {'m_exchange': 'SMART', 'm_openClose': 0, 
                   'm_shortSaleSlot': 0, 'm_designatedLocation': ''}
    option_base = {'m_secType': 'OPT', 'm_exchange': 'SMART',
                   'm_currency': 'USD'}
    stock_base = {'m_secType': 'STK', 'm_exchange': 'SMART', 
                  'm_currency': 'USD'}
    combo_base = {'m_symbol': 'USD', 'm_secType': 'BAG', 'm_exchange': 'SMART',
                  'm_currency': 'USD'}

    def __init__(self, host='', port=7496, client_id=82, paper_trader=False):
        self.client = Client(client_id)
        self.client.connect(host, port)
        self.paper_trader = paper_trader

    def enter_position(self, ticker, expiry, strike, qty=1, longshort=True):
        ''' ticker, strike, and expiry are all strings.
            expiry should be in the form YYMMDD.
        '''
        self.request_contract_ids(ticker, expiry, strike)
        if self.get_contract_ids():
            if self.paper_trader:
                self.gen_separate_orders(qty, longshort)
                order_ids = self.place_separate_orders()
                return order_ids
            else:                
                self.gen_combo_contract()
                self.gen_order(qty, longshort=longshort)
                order_id = self.client.nextId
                self.place_order()
                return order_id
        else:
            errmsg = 'Not all legs exist for ticker %s expiry %s strike %s'
            errmsg = errmsg % (ticker, expiry, str(strike))
            logger.error('%s %s %s' % ('*'*3, errmsg, '*'*3))
            return False

    def request_contract_ids(self, ticker, expiry, strike):
        if len(expiry) != 6:
            msg = 'Expiry format should be YYMMDD, not %s' % str(expiry)
            logger.fatal(msg)
            raise Exception(msg)
        ticker = ticker.upper().strip()
        strike = Decimal(str(strike))*1000

        call_id = '%-6s%s%s%08i' %(ticker, expiry, 'C', strike)
        put_id = '%-6s%s%s%08i' %(ticker, expiry, 'P', strike)

        call = dict(self.option_base.items() 
                    + {'m_localSymbol': call_id}.items())
        stock = dict(self.stock_base.items() 
                     + {'m_symbol': ticker}.items())
        put = dict(self.option_base.items() 
                   + {'m_localSymbol': put_id}.items())

        self.c_req = self.client.request_contract(call)
        self.s_req = self.client.request_contract(stock)
        self.p_req = self.client.request_contract(put)

    def get_contract_ids(self):
        all_requests = (self.client.req_contracts.keys()
                        + self.client.failed_contracts.keys())
        count = 0
        while (self.c_req not in all_requests
            or self.s_req not in all_requests
            or self.p_req not in all_requests):
            count += 1
            if count % 10 == 0: 
                msg = 'On iteration %i for requests %i, %i, %i'
                msgdata = (count, self.c_req, self.s_req, self.p_req)
                logger.debug(msg, *msgdata)
            sleep(.1)
            all_requests = (self.client.req_contracts.keys()
                            + self.client.failed_contracts.keys())
        msg = 'Took %0.1f seconds to get contract info for requests %i, %i, %i'
        msgdata = (count*0.1, self.c_req, self.s_req, self.p_req)
        logger.debug(msg, *msgdata)
        if (self.c_req 
         or self.s_req 
         or self.p_req) in self.client.failed_contracts: return False

        self.c_con_id = self.client.req_contracts[self.c_req][0].m_conId 
        self.s_con_id = self.client.req_contracts[self.s_req][0].m_conId 
        self.p_con_id = self.client.req_contracts[self.p_req][0].m_conId 
        return True

    def gen_combo_contract(self):
        c_action = dict({'m_conId': self.c_con_id, 'm_action': 'BUY',
                         'm_ratio': 1}.items() + self.action_base.items())
        s_action = dict({'m_conId': self.s_con_id, 'm_action': 'SELL', 
                         'm_ratio': 100}.items() + self.action_base.items())
        p_action = dict({'m_conId': self.p_con_id, 'm_action': 'SELL', 
                         'm_ratio': 1}.items() + self.action_base.items())
        legs = Vector()
        legs.add(ComboLeg(**c_action))
        legs.add(ComboLeg(**s_action))
        legs.add(ComboLeg(**p_action))
        combo_params = dict({'m_comboLegs': legs}.items()
                           + self.combo_base.items())
        self.combo_contract = Contract()
        [setattr(self.combo_contract, m, combo_params[m]) 
            for m in dir(self.combo_contract) if m in combo_params]

    def gen_separate_orders(self, qty=1, longshort=True):
        qty = int(qty)
        c_order = {'m_totalQuantity': 1*qty, 'm_orderType': 'MKT'}
        s_order = {'m_totalQuantity': 100*qty, 'm_orderType': 'MKT'}
        p_order = {'m_totalQuantity': 1*qty, 'm_orderType': 'MKT'}
        if longshort:
            c_order['m_action'] = 'BUY'
            s_order['m_action'] = 'SELL'
            p_order['m_action'] = 'SELL'
        else:
            c_order['m_action'] = 'SELL'
            s_order['m_action'] = 'BUY'
            p_order['m_action'] = 'BUY'

        self.c_order = Order(**c_order)
        self.s_order = Order(**s_order)
        self.p_order = Order(**p_order)

    def gen_order(self, qty, longshort=True):
        qty = int(qty)
        self.order = Order()
        order_params = {'m_totalQuantity': qty, 'm_orderType': 'MKT'}
        if longshort: order_params['m_action'] = 'BUY'
        else: order_params['m_action'] = 'SELL'
        [setattr(self.order, m, order_params[m]) for m in dir(self.order)
            if m in order_params]

    def place_separate_orders(self):
        order_ids = [self.client.nextId]
        self.client.m_client.placeOrder(self.client.nextId,
                                        self.client.req_contracts[self.c_req][0],
                                        self.c_order)
        self.client.m_client.reqIds(1)
        while order_ids[-1] == self.client.nextId: 
            logger.debug('order %i still processing', order_ids[-1])
            sleep(.025)
            self.client.m_client.reqIds(1)

        order_ids.append(self.client.nextId)
        self.client.m_client.placeOrder(self.client.nextId,
                                        self.client.req_contracts[self.s_req][0],
                                        self.s_order)
        self.client.m_client.reqIds(1)
        while order_ids[-1] == self.client.nextId: 
            logger.debug('order %i still processing', order_ids[-1])
            sleep(.025)
            self.client.m_client.reqIds(1)

        order_ids.append(self.client.nextId)
        self.client.m_client.placeOrder(self.client.nextId,
                                        self.client.req_contracts[self.p_req][0],
                                        self.p_order)
        self.client.m_client.reqIds(1)
        while order_ids[-1] == self.client.nextId: 
            sleep(.02)
            self.client.m_client.reqIds(1)
        return order_ids

    def place_order(self):
        self.client.m_client.placeOrder(self.client.nextId, 
                                        self.combo_contract,
                                        self.order)
        self.client.m_client.reqIds(1)

if __name__ == "__main__":
    ticker = sys.argv[1]
    expiry = sys.argv[2]
    strike = sys.argv[3]
    qty = sys.argv[4]
    longshort = sys.argv[5]

    r = Reversal()
    if longshort.lower().strip() == 'long': ls=True
    elif longshort.lower().strip() == 'short': ls=False
    else: raise Exception('You have to specify long or short.')
    order_id = r.enter_position(ticker, expiry, strike, qty, longshort=ls)

    while order_id not in r.client.orders: sleep(.5)

    r.client.disconnect()
