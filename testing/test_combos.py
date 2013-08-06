#!/usr/local/bin/jython
import logging
import signal
import sys

from ib.client import Client
from ib.contractkeys import Stock, Option, OptionLocal, Currency
from com.ib.client import Contract, ExecutionFilter
import ib.client
import ib.combo_orders as co

ib.client.LOGLEVEL = logging.DEBUG

def cleanup(signal, frame):
	c.disconnect()
	sys.exit(0)

c = Client()
c.connect()


spot_prices = [x*.01 for x in range(800, 1301)]

symbol = 'BAC'
expirys = ('20130201', '20130215')
strikes = range(9, 13)
keys = [Stock(symbol)]
keys += [Option(symbol, x, y, z) for x in expirys for y in ['C', 'P'] for z in strikes]
contracts = [c.request_contract_details(x)[0].m_summary.m_conId for x in keys]
id_to_key = dict(zip(contracts, keys))

pairs = [(x, y) for x in contracts for y in contracts if x != y]
triples = [(x, y, z) for x in contracts for y in contracts for z in contracts 
           if not (x == y == z)]
quartets = [(w, x, y, z) for w in contracts for x in contracts 
                         for y in contracts for z in contracts 
                         if not (w == x == y == z)]
#buttertest = [ x + ('P',) for x in triples]
#buttertest += [ x + ('C',) for x in triples]
#buttertest += [triples[0] + ('Nope',)]

#irontest = [ x + ('PPCC',) for x in quartets]
#irontest += [ x + ('CCPP',) for x in quartets]
#irontest += [quartets[0] + ('Nope',)]

# Start testing
action = 'BUY'
b = open('butter.txt', 'w')
for x in triples:
    cons = [id_to_key[i] for i in x]
    try:
        t = co.Butterfly(*x)
        t.is_sane(c)
        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
        b.write('%i %s\n' % (oid, str(cons)))
        print t.conId
        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
        payoffs.sort()
        print 'max payoff is', t.max_payoff(c), 'min payoff is', t.min_payoff(c)
    except Exception, err:
#        b.write('%s %s\n' % (str(err), str(cons)))
#       print err
        pass
b.close()

b = open('iron.txt', 'w')
action = 'BUY'
for x in quartets:
    cons = [id_to_key[i] for i in x]
    try:
        t = co.IronCondor(*x)
        t.is_sane(c)
        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
        b.write('%i %s\n' % (oid, str(cons)))
        print t.conId
        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
        payoffs.sort()
        print 'max payoff is', t.max_payoff(c), 'min payoff is', t.min_payoff(c)
    except Exception, err:
#        b.write('%s %s\n' % (str(err), str(cons)))
#       print err
        pass
b.close()

#b = open('box.txt', 'w')
#action = 'BUY'
#for x in quartets:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.Box(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]
#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('buywrite.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.BuyWrite(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('calendar.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.CalendarSpread(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('conv.txt', 'w')
#action = 'BUY'
#for x in triples:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.Conversion(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('delta.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    x = x + (.5,)
#    try:
#        t = co.DeltaNeutral(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

###b = open('diag.txt', 'w')
###action = 'BUY'
###for x in pairs:
###    cons = [id_to_key[i] for i in x]
###    try:
###        t = co.DiagonalSpread(*x)
###        t.is_sane(c)
###        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
###        b.write('%i %s\n' % (oid, str(cons)))
###        print t.conId
###        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
###    except Exception, err:
####        b.write('%s %s\n' % (str(err), str(cons)))
###       print err
###b.close()

#b = open('revers.txt', 'w')
#action = 'BUY'
#for x in triples:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.Reversal(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('riskrevers.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.RiskReversal(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('straddle.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.Straddle(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('strangle.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.Strangle(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('stkopt.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.StkOpt(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('synth.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.Synthetic(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('syntput.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.SyntheticPut(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('syntcall.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.SyntheticCall(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

#b = open('vertical.txt', 'w')
#action = 'BUY'
#for x in pairs:
#    cons = [id_to_key[i] for i in x]
#    try:
#        t = co.VerticalSpread(*x)
#        t.is_sane(c)
#        oid = c.place_order(t.contract, t.order(1, action, 'MKT'))
#        b.write('%i %s\n' % (oid, str(cons)))
#        print t.conId
#        payoffs = [(t.payoff_at_expiry(x, c), x) for x in spot_prices]
#        payoffs.sort()
#        print 'max payoff is', payoffs[-1], 'min payoff is', payoffs[0]

#    except Exception, err:
##        b.write('%s %s\n' % (str(err), str(cons)))
##       print err
#        pass
#b.close()

signal.signal(signal.SIGINT, cleanup)
