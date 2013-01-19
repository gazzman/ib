#!/usr/local/bin/jython
import java.util.Vector as Vector

from com.ib.client import ComboLeg, Contract, Order

from ib.contractkeys import ContractId

LEG_BASE = {'m_exchange': 'SMART', 'm_openClose': 0, 
            'm_shortSaleSlot': 0, 'm_designatedLocation': ''}
COMBO_BASE = {'m_symbol': 'USD', 'm_secType': 'BAG', 'm_exchange': 'SMART',
                'm_currency': 'USD'}

class OrderGen():
    def order(self, qty, action, order_type, limit_price=0):
        qty = int(qty)
        action = action.upper()
        order_type = order_type.upper()
        order_args = {'m_totalQuantity': qty, 'm_action': action, 
                        'm_orderType': order_type, 'm_lmtPrice': limit_price}
        return Order(**order_args)

class Box(OrderGen):
    def __init__(self, call1_id,  put1_id, call2_id,  put2_id):
        self.call1_id, self.put1_id = (call1_id, put1_id) 
        self.call2_id, self.put2_id = (call2_id, put2_id) 
        self.contract = self.gen_contract()

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

class Butterfly(OrderGen)
    def __init__(self, lwing_id,  body_id,  rwing_id):
        self.lwing_id, self.rwing_id = (lwing_id, rwing_id)) 
        self.body_id = body_id
        self.contract = self.gen_contract()

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

class ButterflyCalls(Butterfly):
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
        if lwing_con.m_right != 'C': raise Exception('LWing is not a call')
        if body_con.m_right != 'C': raise Exception('Body is not a call')
        if rwing_con.m_right != 'C': raise Exception('Rwing is not a call')
        if not (lwing_con.m_expiry == body_con.m_expiry == rwing_con.m_expiry):
            raise Exception("Expirys don't match")
        if not (lwing_con.m_symbol == body_con.m_symbol == rwing_con.m_symbol):
            raise Exception("Underlyings don't match")
        if (lwing_con.m_strike + rwing_con.m_strike)/2.0 != body_con.m_strike: 
            raise Exception("Body strike not in between wings")

class ButterflyPuts(Butterfly):
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
        if lwing_con.m_right != 'P': raise Exception('LWing is not a put')
        if body_con.m_right != 'P': raise Exception('Body is not a put')
        if rwing_con.m_right != 'P': raise Exception('Rwing is not a put')
        if not (lwing_con.m_expiry == body_con.m_expiry == rwing_con.m_expiry):
            raise Exception("Expirys don't match")
        if not (lwing_con.m_symbol == body_con.m_symbol == rwing_con.m_symbol):
            raise Exception("Underlyings don't match")
        if (lwing_con.m_strike + rwing_con.m_strike)/2.0 != body_con.m_strike: 
            raise Exception("Body strike not in between wings")

class CalendarSpread(OrderGen):
    def __init__(self, Exp1_id, Exp2_id):
        self.Exp1_id, self.Exp2_id = (Exp1_id, Exp2_id) 
        self.contract = self.gen_contract()

    def gen_contract(self):
        Exp1 = {'m_conId': self.call_id, 'm_ratio': 1, 'm_action': 'BUY'}
        Exp1.update(LEG_BASE)
        Exp1 = {'m_conId': self.call_id, 'm_ratio': 1, 'm_action': 'SELL'}
        Exp1.update(LEG_BASE)

        legs = Vector()
        legs.add(ComboLeg(**Exp1))
        legs.add(ComboLeg(**Exp2))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(COMBO_BASE)
        return Contract(**combo_args)

    def is_sane(self, client):
        Exp1_cd = client.request_contract_details(ContractId(self.Exp1_id))
        Exp2_cd = client.request_contract_details(ContractId(self.Exp2_id))
        Exp1_con = Exp1_cd.m_summary
        Exp2_con = Exp2_cd.m_summary
        if Exp1_con.m_secType != 'OPT': raise Exception("Exp1 is not 'OPT'")
        if Exp2_con.m_secType != 'OPT': raise Exception("Exp1 is not 'OPT'")
        if Exp1_con.m_expiry == Exp2_con.m_expiry:
            raise Exception("Expirys need to be different")
        if Exp1_con.m_right != Exp2_con.m_right:
            raise Exception("Rights don't match")
        if Exp1_con.m_strike != Exp2_con.m_strike: 
            raise Exception("Strikes don't match")
        if Exp1_con.m_symbol != Exp2_con.m_symbol:
            raise Exception("Underlyings don't match")

class Conversion(OrderGen):
    pass

class DeltaNeutral(OrderGen):
    pass

class DiagonalSpread(OrderGen):
    pass

class IronCorridor(OrderGen):
    pass

class Reversal(OrderGen):
    def __init__(self, call_id, stock_id, put_id):
        self.call_id, self.stock_id, self.put_id = (call_id, stock_id, put_id) 
        self.contract = self.gen_contract()

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

class RiskReversal(OrderGen):
    pass

class SFFOPT(OrderGen):
    pass

class Straddle(OrderGen):
    pass

class Strangle(OrderGen):
    pass

class StkOpt(OrderGen):
    pass

class Synthetic(OrderGen):
    pass

class SyntheticPut(OrderGen):
    pass

class SyntheticCall(OrderGen):
    pass

class VerticalSpread(OrderGen):
    pass
