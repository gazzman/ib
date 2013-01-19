#!/usr/local/bin/jython
import java.util.Vector as Vector

from com.ib.client import ComboLeg, Contract, Order

class Reversal():
    leg_base = {'m_exchange': 'SMART', 'm_openClose': 0, 
                'm_shortSaleSlot': 0, 'm_designatedLocation': ''}
    combo_base = {'m_symbol': 'USD', 'm_secType': 'BAG', 'm_exchange': 'SMART',
                  'm_currency': 'USD'}

    def contract(self, call_id, stock_id, put_id):
        call_leg = {'m_conId': call_id, 'm_ratio': 1, 'm_action': 'BUY'}
        call_leg.update(self.leg_base)
        stock_leg = {'m_conId': stock_id, 'm_ratio': 100, 'm_action': 'SELL'}
        stock_leg.update(self.leg_base)
        put_leg = {'m_conId': put_id, 'm_ratio': 1, 'm_action': 'SELL'}
        put_leg.update(self.leg_base)

        legs = Vector()
        legs.add(ComboLeg(**call_leg))
        legs.add(ComboLeg(**stock_leg))
        legs.add(ComboLeg(**put_leg))

        combo_args = {'m_comboLegs': legs}
        combo_args.update(self.combo_base)
        return Contract(**combo_args)

    def order(self, qty, action, order_type, limit_price=0):
        qty = int(qty)
        action = action.upper()
        order_type = order_type.upper()
        order_args = {'m_totalQuantity': qty, 'm_action': action, 
                      'm_orderType': order_type, 'm_lmtPrice': limit_price}
        return Order(**order_args)
