#!/usr/local/bin/jython
__version__ = ".00"
__author__ = "gazzman"
__copyright__ = "(C) gazzman GNU GPL 3."
__contributors__ = []
import java.util.Vector as Vector

from com.ib.client import ComboLeg, Contract, Order

from ib.contractkeys import ContractId

LEG_BASE = {'m_exchange': 'SMART', 'm_openClose': 0, 
            'm_shortSaleSlot': 0, 'm_designatedLocation': ''}
COMBO_BASE = {'m_symbol': 'USD', 'm_secType': 'BAG', 'm_exchange': 'SMART',
                'm_currency': 'USD'}

# Mixins
class OrderGen():
    def order(self, qty, action, order_type, limit_price=0):
        qty = int(qty)
        action = action.upper()
        order_type = order_type.upper()
        order_args = {'m_totalQuantity': qty, 'm_action': action, 
                        'm_orderType': order_type, 'm_lmtPrice': limit_price}
        return Order(**order_args)

class OptPair(OrderGen):
    def __init__(self, opt1_id, opt2_id):
        self.opt1_id, self.opt2_id = (opt1_id, opt2_id) 
        self.contract = self.gen_contract()
        self.conId = self.gen_conId()

class OptUnder(OrderGen):
    def __init__(self, stk_id, opt_id):
        self.stk_id, self.opt_id = (stk_id, opt_id) 
        self.contract = self.gen_contract()
        self.conId = self.gen_conId()

class Spread(OptPair):
    def gen_contract(self):
        opt1 = {'m_conId': self.opt1_id, 'm_ratio': 1, 'm_action': 'BUY'}
        opt1.update(LEG_BASE)
        opt2 = {'m_conId': self.opt2_id, 'm_ratio': 1, 'm_action': 'SELL'}
        opt2.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**opt1))
        legs.add(ComboLeg(**opt2))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

class SameSide(OptPair):
    def gen_contract(self):
        opt1 = {'m_conId': self.opt1_id, 'm_ratio': 1, 'm_action': 'BUY'}
        opt1.update(LEG_BASE)
        opt2 = {'m_conId': self.opt2_id, 'm_ratio': 1, 'm_action': 'BUY'}
        opt2.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**opt1))
        legs.add(ComboLeg(**opt2))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

# Combo classes
class Box(OrderGen):
    def __init__(self, call1_id,  put1_id, call2_id,  put2_id):
        self.call1_id, self.put1_id = (call1_id, put1_id) 
        self.call2_id, self.put2_id = (call2_id, put2_id) 
        self.contract = self.gen_contract()
        self.conId = 'Box_%i_%i_%i_%i' % (call1_id, put1_id, call2_id, put2_id)

    def gen_contract(self):
        call1 = {'m_conId': self.call1_id, 'm_ratio': 1, 'm_action': 'BUY'}
        call1.update(LEG_BASE)
        put1 = {'m_conId': self.put1_id, 'm_ratio': 1, 'm_action': 'SELL'}
        put1.update(LEG_BASE)
        call2 = {'m_conId': self.call2_id, 'm_ratio': 1, 'm_action': 'SELL'}
        call2.update(LEG_BASE)
        put2 = {'m_conId': self.put2_id, 'm_ratio': 1, 'm_action': 'BUY'}
        put2.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**call1))
        legs.add(ComboLeg(**put1))
        legs.add(ComboLeg(**call2))
        legs.add(ComboLeg(**put2))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        call1_cd = client.request_contract_details(ContractId(self.call1_id))
        put1_cd = client.request_contract_details(ContractId(self.put1_id))
        call2_cd = client.request_contract_details(ContractId(self.call2_id))
        put2_cd = client.request_contract_details(ContractId(self.put2_id))
        call1_con = call1_cd.m_summary
        put1_con = put1_cd.m_summary
        call2_con = call2_cd.m_summary
        put2_con = put2_cd.m_summary
        if call1_con.m_secType != 'OPT': raise Exception("Call1 is not 'OPT'")
        if put1_con.m_secType != 'OPT': raise Exception("Put1 is not 'OPT'")
        if call2_con.m_secType != 'OPT': raise Exception("Call2 is not 'OPT'")
        if put2_con.m_secType != 'OPT': raise Exception("Put2 is not 'OPT'")
        if call1_con.m_right != 'C': raise Exception('Call1 is not a call')
        if put1_con.m_right != 'P': raise Exception('Put1 is not a put')
        if call2_con.m_right != 'C': raise Exception('Call2 is not a call')
        if put2_con.m_right != 'P': raise Exception('Put2 is not a put')
        if not (call1_con.m_expiry == put1_con.m_expiry 
                == call2_con.m_expiry == put2_con.m_expiry):
            raise Exception("Expirys don't match")
        if not (call1_con.m_symbol == put1_con.m_symbol 
                == call2_con.m_symbol == put2_con.m_symbol):
            raise Exception("Underlyings don't match")
        if call1_con.m_strike != put1_con.m_strike: 
            raise Exception("Synthetic1 strikes don't match")
        if call2_con.m_strike != put2_con.m_strike: 
            raise Exception("Synthetic2 strikes don't match")
        if call1_con.m_strike == call2_con.m_strike: 
            raise Exception("Synthetic strikes match")
        return True

class Butterfly(OrderGen):
    def __init__(self, lwing_id,  body_id,  rwing_id):
        self.lwing_id, self.rwing_id = (lwing_id, rwing_id)
        self.body_id = body_id
        self.contract = self.gen_contract()
        self.conId = 'Butterfly_%i_%i_%i' % (lwing_id, body_id, rwing_id)

    def gen_contract(self):
        lwing = {'m_conId': self.lwing_id, 'm_ratio': 1, 'm_action': 'BUY'}
        lwing.update(LEG_BASE)
        body = {'m_conId': self.body_id, 'm_ratio': 2, 'm_action': 'SELL'}
        body.update(LEG_BASE)
        rwing = {'m_conId': self.rwing_id, 'm_ratio': 1, 'm_action': 'BUY'}
        rwing.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**lwing))
        legs.add(ComboLeg(**body))
        legs.add(ComboLeg(**rwing))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        lwing_cd = client.request_contract_details(ContractId(self.lwing_id))
        body_cd = client.request_contract_details(ContractId(self.body_id))
        rwing_cd = client.request_contract_details(ContractId(self.rwing_id))
        lwing_con = lwing_cd.m_summary
        body_con = body_cd.m_summary
        rwing_con = rwing_cd.m_summary
        if lwing_con.m_secType != 'OPT': raise Exception("LWing is not 'OPT'")
        if body_con.m_secType != 'OPT': raise Exception("Body is not 'OPT'")
        if rwing_con.m_secType != 'OPT': raise Exception("RWing is not 'OPT'")
        if not (lwing_con.m_right == body_con.m_right == rwing_con.m_right):
            raise Exception('Options have different rights.')
        if not (lwing_con.m_expiry == body_con.m_expiry == rwing_con.m_expiry):
            raise Exception("Expirys don't match")
        if not (lwing_con.m_symbol == body_con.m_symbol == rwing_con.m_symbol):
            raise Exception("Underlyings don't match")
        if (lwing_con.m_strike + rwing_con.m_strike)/2.0 != body_con.m_strike: 
            raise Exception("Body strike not in between wings")
        return True

class BuyWrite(OptUnder):
    def gen_conId(self):
        return 'BuyWrite_%i_%i' % (self.stk_id, self.opt_id)
        
    def gen_contract(self):
        opt = {'m_conId': self.opt_id, 'm_ratio': 1, 'm_action': 'SELL'}
        opt.update(LEG_BASE)
        stk = {'m_conId': self.stk_id, 'm_ratio': 100, 'm_action': 'BUY'}
        stk.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**opt))
        legs.add(ComboLeg(**stk))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        opt_cd = client.request_contract_details(ContractId(self.opt_id))
        stk_cd = client.request_contract_details(ContractId(self.stk_id))
        opt_con = opt_cd.m_summary
        stk_con = stk_cd.m_summary
        if opt_con.m_secType != 'OPT': raise Exception("Option is not 'OPT'")
        if stk_con.m_secType != 'STK': raise Exception("Stock is not 'STK'")
        if opt_con.m_right != 'C': raise Exception("Call is not a call")
        if opt_con.m_symbol != stk_con.m_symbol:
            raise Exception("Option is on wrong underlying, or wrong Stock")
        return True

class CalendarSpread(Spread):
    def gen_conId(self):
        return 'CalendarSpread_%i_%i' % (self.opt1_id, self.opt2_id)

    def is_sane(self, client):
        opt1_cd = client.request_contract_details(ContractId(self.opt1_id))
        opt2_cd = client.request_contract_details(ContractId(self.opt2_id))
        opt1_con = opt1_cd.m_summary
        opt2_con = opt2_cd.m_summary
        if opt1_con.m_secType != 'OPT': raise Exception("Option1 is not 'OPT'")
        if opt2_con.m_secType != 'OPT': raise Exception("Option2 is not 'OPT'")
        if opt1_con.m_right != opt2_con.m_right: 
            raise Exception('Options are different rights')
        if opt1_con.m_expiry == opt2_con.m_expiry:
            raise Exception("Expirys match")
        if opt1_con.m_strike != opt2_con.m_strike: 
            raise Exception("Strikes don't match")
        if opt1_con.m_symbol != opt2_con.m_symbol:
            raise Exception("Options are on different underlyings")
        return True

class Conversion(OrderGen):
    def __init__(self, call_id, stock_id, put_id):
        self.call_id, self.stock_id, self.put_id = (call_id, stock_id, put_id) 
        self.contract = self.gen_contract()
        self.conId = 'Conversion_%i_%i_%i' % (call_id, stock_id, put_id)

    def gen_contract(self):
        call = {'m_conId': self.call_id, 'm_ratio': 1, 'm_action': 'SELL'}
        call.update(LEG_BASE)
        stock = {'m_conId': self.stock_id, 'm_ratio': 100, 'm_action': 'BUY'}
        stock.update(LEG_BASE)
        put = {'m_conId': self.put_id, 'm_ratio': 1, 'm_action': 'BUY'}
        put.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**call))
        legs.add(ComboLeg(**stock))
        legs.add(ComboLeg(**put))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        call_cd = client.request_contract_details(ContractId(self.call_id))
        stock_cd = client.request_contract_details(ContractId(self.stock_id))
        put_cd = client.request_contract_details(ContractId(self.put_id))
        call_con = call_cd.m_summary
        stock_con = stock_cd.m_summary
        put_con = put_cd.m_summary
        if call_con.m_secType != 'OPT': raise Exception("Call is not 'OPT'")
        if stock_con.m_secType != 'STK': raise Exception("Stock is not 'STK'")
        if put_con.m_secType != 'OPT': raise Exception("Put is not 'OPT'")
        if call_con.m_right != 'C': raise Exception('Call is not a call')
        if put_con.m_right != 'P': raise Exception('Put is not a put')
        if call_con.m_expiry != put_con.m_expiry:
            raise Exception("Expirys don't match")
        if call_con.m_strike != put_con.m_strike: 
            raise Exception("Strikes don't match")
        if call_con.m_symbol != stock_con.m_symbol:
            raise Exception("Call is on wrong underlying, or wrong Stock")
        if put_con.m_symbol != stock_con.m_symbol:
            raise Exception("Put is on wrong underlying, or wrong Stock")
        return True

class DeltaNeutral(OrderGen):
    pass
#    def __init__(self, opt_id, stk_id, delta):
#        self.stk_id, self.opt_id, self.delta = (stk_id, opt_id, delta) 
#        self.contract = self.gen_contract()

#    def gen_contract(self):
#        opt = {'m_conId': self.opt_id, 'm_ratio': 1, 'm_action': 'BUY'}
#        opt.update(LEG_BASE)
#        stk = {'m_conId': self.stk_id, 'm_ratio': int(100*self.delta), 'm_action': 'SELL'}
#        stk.update(LEG_BASE)

#        legs = Vector()
#        legs.add(ComboLeg(**opt))
#        legs.add(ComboLeg(**stk))

#        combo_args = {'m_comboLegs': legs}
#        combo_args.update(COMBO_BASE)
#        return Contract(**combo_args)

#    def is_sane(self, client):
#        opt_cd = client.request_contract_details(ContractId(self.opt_id))
#        stk_cd = client.request_contract_details(ContractId(self.stk_id))
#        opt_con = opt_cd.m_summary
#        stk_con = stk_cd.m_summary
#        if opt_con.m_secType != 'OPT': raise Exception("Option is not 'OPT'")
#        if stk_con.m_secType != 'STK': raise Exception("Stock is not 'STK'")
#        if opt_con.m_symbol != stk_con.m_symbol:
#            raise Exception("Option is on wrong underlying, or wrong Stock")
#        return True

class DiagonalSpread(Spread):
    def gen_conId(self):
        return 'DiagonalSpread_%i_%i' % (self.opt1_id, self.opt2_id)

    def is_sane(self, client):
        opt1_cd = client.request_contract_details(ContractId(self.opt1_id))
        opt2_cd = client.request_contract_details(ContractId(self.opt2_id))
        opt1_con = opt1_cd.m_summary
        opt2_con = opt2_cd.m_summary
        if opt1_con.m_secType != 'OPT': raise Exception("Option1 is not 'OPT'")
        if opt2_con.m_secType != 'OPT': raise Exception("Option2 is not 'OPT'")
        if opt1_con.m_right != opt2_con.m_right: 
            raise Exception('Options are different rights')
        if opt1_con.m_expiry == opt2_con.m_expiry:
            raise Exception("Expirys match")
        if opt1_con.m_strike == opt2_con.m_strike: 
            raise Exception("Strikes match")
        if opt1_con.m_symbol != opt2_con.m_symbol:
            raise Exception("Options are on different underlyings")
        return True

class IronCondor(OrderGen):
    def __init__(self, wingcall_id, bodycall_id, bodyput_id, wingput_id):
        self.wingcall_id, self.bodycall_id = (wingcall_id, bodycall_id)
        self.bodyput_id, self.wingput_id = (bodyput_id, wingput_id)
        self.contract = self.gen_contract()
        self.conId = 'IronCondor_%i_%i_%i_%i' % (wingcall_id, bodycall_id,
                                                 bodyput_id, wingput_id)

    def gen_contract(self):
        wingcall = {'m_conId': self.wingcall_id, 'm_ratio': 1, 'm_action': 'BUY'}
        wingcall.update(LEG_BASE)
        bodycall = {'m_conId': self.bodycall_id, 'm_ratio': 1, 'm_action': 'SELL'}
        bodycall.update(LEG_BASE)
        bodyput = {'m_conId': self.bodyput_id, 'm_ratio': 1, 'm_action': 'SELL'}
        bodyput.update(LEG_BASE)
        wingput = {'m_conId': self.wingput_id, 'm_ratio': 1, 'm_action': 'BUY'}
        wingput.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**wingcall))
        legs.add(ComboLeg(**bodycall))
        legs.add(ComboLeg(**bodyput))
        legs.add(ComboLeg(**wingput))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        wingcall_cd = client.request_contract_details(ContractId(self.wingcall_id))
        bodycall_cd = client.request_contract_details(ContractId(self.bodyput_id))
        bodyput_cd = client.request_contract_details(ContractId(self.bodycall_id))
        wingput_cd = client.request_contract_details(ContractId(self.wingput_id))
        wingcall_con = wingcall_cd.m_summary
        bodycall_con = bodycall_cd.m_summary
        bodyput_con = bodyput_cd.m_summary
        wingput_con = wingput_cd.m_summary
        if wingcall_con.m_secType != 'OPT': raise Exception("wingcall is not 'OPT'")
        if bodycall_con.m_secType != 'OPT': raise Exception("bodycall is not 'OPT'")
        if bodyput_con.m_secType != 'OPT': raise Exception("bodyput is not 'OPT'")
        if wingput_con.m_secType != 'OPT': raise Exception("wingput is not 'OPT'")
        if wingcall_con.m_right != 'P': raise Exception('wingput is not a put')
        if bodycall_con.m_right != 'P': raise Exception('bodycall is not a put')
        if bodyput_con.m_right != 'C': raise Exception('bodyput is not a call')
        if wingput_con.m_right != 'C': raise Exception('wingput is not a call')
        if not (wingcall_con.m_expiry == bodycall_con.m_expiry 
                == bodyput_con.m_expiry == wingput_con.m_expiry):
            raise Exception("Expirys don't match")
        if not (wingcall_con.m_symbol == bodycall_con.m_symbol 
                == bodyput_con.m_symbol == wingput_con.m_symbol):
            raise Exception("Underlyings don't match")
        if not ((wingcall_con.m_strike < bodycall_con.m_strike
                 < bodyput_con.m_strike < wingput_con.m_strike)
               or (wingcall_con.m_strike > bodycall_con.m_strike
                   > bodyput_con.m_strike > wingput_con.m_strike)):
            raise Exception("Strikes are wrong")
        return True

class Reversal(Conversion):
    def __init__(self, call_id, stock_id, put_id):
        self.call_id, self.stock_id, self.put_id = (call_id, stock_id, put_id) 
        self.contract = self.gen_contract()
        self.conId = 'Reversal_%i_%i_%i' % (call_id, stock_id, put_id)

    def gen_contract(self):
        call = {'m_conId': self.call_id, 'm_ratio': 1, 'm_action': 'BUY'}
        call.update(LEG_BASE)
        stock = {'m_conId': self.stock_id, 'm_ratio': 100, 'm_action': 'SELL'}
        stock.update(LEG_BASE)
        put = {'m_conId': self.put_id, 'm_ratio': 1, 'm_action': 'SELL'}
        put.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**call))
        legs.add(ComboLeg(**stock))
        legs.add(ComboLeg(**put))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

class RiskReversal(Spread):
    def gen_conId(self):
        return 'RiskReversal_%i_%i' % (self.opt1_id, self.opt2_id)

    def is_sane(self, client):
        opt1_cd = client.request_contract_details(ContractId(self.opt1_id))
        opt2_cd = client.request_contract_details(ContractId(self.opt2_id))
        opt1_con = opt1_cd.m_summary
        opt2_con = opt2_cd.m_summary
        if opt1_con.m_secType != 'OPT': raise Exception("Option1 is not 'OPT'")
        if opt2_con.m_secType != 'OPT': raise Exception("Option2 is not 'OPT'")
        if opt1_con.m_right != 'P': raise Exception('Put is not a put')
        if opt2_con.m_right != 'C': raise Exception('Call is not a call')
        if opt1_con.m_expiry != opt2_con.m_expiry:
            raise Exception("Expirys don't match")
        if not opt1_con.m_strike < opt2_con.m_strike:
            raise Exception("Put strike is not less than call strike")
        if opt1_con.m_symbol != opt2_con.m_symbol:
            raise Exception("Options are on different underlyings")
        return True

class SFFOPT(OrderGen):
    pass

class Straddle(SameSide):
    def gen_conId(self):
        return 'Straddle_%i_%i' % (self.opt1_id, self.opt2_id)

    def is_sane(self, client):
        opt1_cd = client.request_contract_details(ContractId(self.opt1_id))
        opt2_cd = client.request_contract_details(ContractId(self.opt2_id))
        opt1_con = opt1_cd.m_summary
        opt2_con = opt2_cd.m_summary
        if opt1_con.m_secType != 'OPT': raise Exception("Option1 is not 'OPT'")
        if opt2_con.m_secType != 'OPT': raise Exception("Option2 is not 'OPT'")
        if opt1_con.m_right == opt2_con.m_right: 
            raise Exception('Options have same rights')
        if opt1_con.m_expiry != opt2_con.m_expiry:
            raise Exception("Expirys don't match")
        if opt1_con.m_strike != opt2_con.m_strike: 
            raise Exception("Strikes don't match")
        if opt1_con.m_symbol != opt2_con.m_symbol:
            raise Exception("Options are on different underlyings")
        return True

class Strangle(SameSide):
    def gen_conId(self):
        return 'Strangle_%i_%i' % (self.opt1_id, self.opt2_id)

    def is_sane(self, client):
        opt1_cd = client.request_contract_details(ContractId(self.opt1_id))
        opt2_cd = client.request_contract_details(ContractId(self.opt2_id))
        opt1_con = opt1_cd.m_summary
        opt2_con = opt2_cd.m_summary
        if opt1_con.m_secType != 'OPT': raise Exception("Option1 is not 'OPT'")
        if opt2_con.m_secType != 'OPT': raise Exception("Option2 is not 'OPT'")
        if opt1_con.m_right == opt2_con.m_right: 
            raise Exception('Options have same rights')
        if opt1_con.m_expiry != opt2_con.m_expiry:
            raise Exception("Expirys don't match")
        if opt1_con.m_strike == opt2_con.m_strike: 
            raise Exception("Strikes match")
        if opt1_con.m_symbol != opt2_con.m_symbol:
            raise Exception("Options are on different underlyings")
        return True

class StkOpt(OptUnder):
    def gen_conId(self):
        return 'StkOpt_%i_%i' % (self.stk_id, self.opt_id)

    def gen_contract(self):
        opt = {'m_conId': self.opt_id, 'm_ratio': 1, 'm_action': 'BUY'}
        opt.update(LEG_BASE)
        stk = {'m_conId': self.stk_id, 'm_ratio': 100, 'm_action': 'BUY'}
        stk.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**opt))
        legs.add(ComboLeg(**stk))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        opt_cd = client.request_contract_details(ContractId(self.opt_id))
        stk_cd = client.request_contract_details(ContractId(self.stk_id))
        opt_con = opt_cd.m_summary
        stk_con = stk_cd.m_summary
        if opt_con.m_secType != 'OPT': raise Exception("Option is not 'OPT'")
        if stk_con.m_secType != 'STK': raise Exception("Stock is not 'STK'")
        if opt_con.m_symbol != stk_con.m_symbol:
            raise Exception("Option is on wrong underlying, or wrong Stock")
        return True

class Synthetic(Spread):
    def gen_conId(self):
        return 'Synthetic_%i_%i' % (self.opt1_id, self.opt2_id)

    def is_sane(self, client):
        opt1_cd = client.request_contract_details(ContractId(self.opt1_id))
        opt2_cd = client.request_contract_details(ContractId(self.opt2_id))
        opt1_con = opt1_cd.m_summary
        opt2_con = opt2_cd.m_summary
        if opt1_con.m_secType != 'OPT': raise Exception("Option1 is not 'OPT'")
        if opt2_con.m_secType != 'OPT': raise Exception("Option2 is not 'OPT'")
        if opt1_con.m_right == opt2_con.m_right: 
            raise Exception('Options have same rights')
        if opt1_con.m_expiry != opt2_con.m_expiry:
            raise Exception("Expirys don't match")
        if opt1_con.m_strike != opt2_con.m_strike: 
            raise Exception("Strikes don't match")
        if opt1_con.m_symbol != opt2_con.m_symbol:
            raise Exception("Options are on different underlyings")
        return True

class SyntheticPut(OptUnder):
    def gen_conId(self):
        return 'SyntheticPut_%i_%i' % (self.stk_id, self.opt_id)

    def gen_contract(self):
        opt = {'m_conId': self.opt_id, 'm_ratio': 1, 'm_action': 'BUY'}
        opt.update(LEG_BASE)
        stk = {'m_conId': self.stk_id, 'm_ratio': 100, 'm_action': 'SELL'}
        stk.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**opt))
        legs.add(ComboLeg(**stk))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        opt_cd = client.request_contract_details(ContractId(self.opt_id))
        stk_cd = client.request_contract_details(ContractId(self.stk_id))
        opt_con = opt_cd.m_summary
        stk_con = stk_cd.m_summary
        if opt_con.m_secType != 'OPT': raise Exception("Option is not 'OPT'")
        if stk_con.m_secType != 'STK': raise Exception("Stock is not 'STK'")
        if opt_con.m_right != 'C': raise Exception("Call is not a call")
        if opt_con.m_symbol != stk_con.m_symbol:
            raise Exception("Option is on wrong underlying, or wrong Stock")
        return True

class SyntheticCall(OptUnder):
    def gen_conId(self):
        return 'SyntheticCall_%i_%i' % (self.stk_id, self.opt_id)

    def gen_contract(self):
        opt = {'m_conId': self.opt_id, 'm_ratio': 1, 'm_action': 'BUY'}
        opt.update(LEG_BASE)
        stk = {'m_conId': self.stk_id, 'm_ratio': 100, 'm_action': 'BUY'}
        stk.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**opt))
        legs.add(ComboLeg(**stk))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        opt_cd = client.request_contract_details(ContractId(self.opt_id))
        stk_cd = client.request_contract_details(ContractId(self.stk_id))
        opt_con = opt_cd.m_summary
        stk_con = stk_cd.m_summary
        if opt_con.m_secType != 'OPT': raise Exception("Option is not 'OPT'")
        if stk_con.m_secType != 'STK': raise Exception("Stock is not 'STK'")
        if opt_con.m_right != 'P': raise Exception("Put is not a put")
        if opt_con.m_symbol != stk_con.m_symbol:
            raise Exception("Option is on wrong underlying, or wrong Stock")
        return True

class VerticalSpread(Spread):
    def gen_conId(self):
        return 'VerticalSpread_%i_%i' % (self.opt1_id, self.opt2_id)

    def is_sane(self, client):
        opt1_cd = client.request_contract_details(ContractId(self.opt1_id))
        opt2_cd = client.request_contract_details(ContractId(self.opt2_id))
        opt1_con = opt1_cd.m_summary
        opt2_con = opt2_cd.m_summary
        if opt1_con.m_secType != 'OPT': raise Exception("Option1 is not 'OPT'")
        if opt2_con.m_secType != 'OPT': raise Exception("Option2 is not 'OPT'")
        if opt1_con.m_right != opt2_con.m_right: 
            raise Exception('Options are different rights')
        if opt1_con.m_expiry != opt2_con.m_expiry:
            raise Exception("Expirys don't match")
        if opt1_con.m_strike == opt2_con.m_strike: 
            raise Exception("Strikes match")
        if opt1_con.m_symbol != opt2_con.m_symbol:
            raise Exception("Options are on different underlyings")
        return True
