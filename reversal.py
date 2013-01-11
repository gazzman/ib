#!/usr/local/bin/jython
from time import sleep
from decimal import Decimal
import java.util.Vector as Vector
import sys

from com.ib.client import ComboLeg, Contract, Order

from ib.client import Client

class Reversal():
    action_base = {'m_exchange': 'SMART', 'm_openClose': 0, 
                   'm_shortSaleSlot': 0, 'm_designatedLocation': ''}
    option_base = {'m_secType': 'OPT', 'm_exchange': 'SMART',
                   'm_currency': 'USD'}
    stock_base = {'m_secType': 'STK', 'm_exchange': 'SMART', 
                  'm_currency': 'USD'}
    combo_base = {'m_symbol': 'USD', 'm_secType': 'BAG', 'm_exchange': 'SMART',
                  'm_currency': 'USD'}

    def __init__(self, host='', port=7496, client_id=101):
        self.client = Client()
        self.client.connect(host, port, client_id)

    def enter_position(self, ticker, expiry, strike, qty=1, long=True):
        ''' ticker, strike, and expiry are all strings.
            expiry should be in the form YYMMDD.
        '''
        self.request_contract_ids(ticker, expiry, strike)
        if self.get_contract_ids():
            self.gen_combo_contract()
            self.gen_order(qty, long=long)
            order_id = self.client.nextId
            self.place_order()
            return order_id
        else:
            errmsg = 'Not all legs exist for ticker %s expiry %s strike %s'
            errmsg = errmsg % (ticker, expiry, str(strike))
            print >> sys.stderr, '*'*60, errmsg, '*'*60

    def request_contract_ids(self, ticker, expiry, strike):
        if len(expiry) != 6: raise Exception('Expiry format should be YYMMDD')
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

        self.c_req = self.client.generate_contract(call)
        self.s_req = self.client.generate_contract(stock)
        self.p_req = self.client.generate_contract(put)

    def get_contract_ids(self):
        while (self.c_req not in (self.client.requested_contracts.keys()
                                  + self.client.errs_dict.keys())
               or self.s_req not in (self.client.requested_contracts.keys()
                                     + self.client.errs_dict.keys())
               or self.p_req not in (self.client.requested_contracts.keys()
                                     + self.client.errs_dict.keys())
              ): sleep(.1)

        if (self.c_req or self.s_req or self.p_req) in self.client.errs_dict:
            return False

        self.c_con_id = self.client.requested_contracts[self.c_req].m_conId 
        self.s_con_id = self.client.requested_contracts[self.s_req].m_conId 
        self.p_con_id = self.client.requested_contracts[self.p_req].m_conId 
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

    def gen_order(self, qty, long=True):
        qty = int(qty)
        self.order = Order()
        order_params = {'m_totalQuantity': qty, 'm_orderType': 'MKT'}
        if long: order_params['m_action'] = 'BUY'
        else: order_params['m_action'] = 'SELL'
        [setattr(self.order, m, order_params[m]) for m in dir(self.order)
            if m in order_params]

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
    long_or_short = sys.argv[5]

    r = Reversal()
    if long_or_short.lower().strip() == 'long': long=True
    elif long_or_short.lower().strip() == 'short': long=False
    else: raise Exception('You have to specify long or short.')
    order_id = r.enter_position(ticker, expiry, strike, qty, long=long)
    
    while order_id not in r.client.orders: sleep(.5)
    
    r.client.disconnect()
