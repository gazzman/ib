#!/usr/local/bin/jython
import logging
import signal
import sys

from ib.client import Client
from ib.contractkeys import Currency, CurrencyLocal, Stock, Option, OptionLocal
from com.ib.client import Contract, ExecutionFilter
import ib.client
import ib.combo_orders as co

ib.client.LOGLEVEL = logging.DEBUG

def cleanup(signal, frame):
	c.disconnect()
	sys.exit(0)

c = Client()
c.connect()

expiry = '20130201'
cbkeys = [Option('BAC', expiry, 'C', 10), 
          Option('BAC', expiry, 'C', 11), 
          Option('BAC', expiry, 'C', 12)]
pbkeys = [Option('BAC', expiry, 'P', 10), 
          Option('BAC', expiry, 'P', 11), 
          Option('BAC', expiry, 'P', 12)]

cbinkeys = [Option('BAC', expiry, 'C', 10.5), 
              Option('BAC', expiry, 'C', 11), 
              Option('BAC', expiry, 'C', 11.5)]
pbinkeys = [Option('BAC', expiry, 'P', 10.5), 
              Option('BAC', expiry, 'P', 11), 
              Option('BAC', expiry, 'P', 11.5)]

cikeys = [Option('BAC', expiry, 'C', 10),
          Option('BAC', expiry, 'C', 10.5), 
          Option('BAC', expiry, 'P', 11.5),
          Option('BAC', expiry, 'P', 12)]
pikeys = [Option('BAC', expiry, 'C', 12),
          Option('BAC', expiry, 'C', 11.5), 
          Option('BAC', expiry, 'P', 10.5),
          Option('BAC', expiry, 'P', 10)]

box = [Option('BAC', expiry, 'C', 12),
       Option('BAC', expiry, 'C', 11.5), 
       Option('BAC', expiry, 'P', 10.5),
       Option('BAC', expiry, 'P', 10)]
       
cbids = [c.request_contract_details(x)[0].m_summary.m_conId for x in cbkeys]
pbids = [c.request_contract_details(x)[0].m_summary.m_conId for x in cbkeys]
cbinds = [c.request_contract_details(x)[0].m_summary.m_conId for x in cbinkeys]
pbinds = [c.request_contract_details(x)[0].m_summary.m_conId for x in cbinkeys]
ciids = [c.request_contract_details(x)[0].m_summary.m_conId for x in cikeys]
piids = [c.request_contract_details(x)[0].m_summary.m_conId for x in pikeys]

cb = co.Butterfly(*cbids)
pb = co.Butterfly(*pbids)
cbin = co.Butterfly(*cbinds)
pbin = co.Butterfly(*pbinds)
ci = co.IronCondor(*ciids)
pi = co.IronCondor(*piids)

c.request_mkt_data(cb.contract, snapshot=False, fname=('%s.txt' % cb.conId))
c.request_mkt_data(pb.contract, snapshot=False, fname=('%s.txt' % pb.conId))
c.request_mkt_data(cbin.contract, snapshot=False, fname=('%s.txt' % cbin.conId))
c.request_mkt_data(pbin.contract, snapshot=False, fname=('%s.txt' % pbin.conId))
c.request_mkt_data(ci.contract, snapshot=False, fname=('%s.txt' % ci.conId))
c.request_mkt_data(pi.contract, snapshot=False, fname=('%s.txt' % pi.conId))

print 'Call Butterfly max/min:', cb.max_payoff(c), cb.min_payoff(c)
print 'Put Butterfly max/min:', pb.max_payoff(c), pb.min_payoff(c)
print 'Call in Butterfly max/min:', cbin.max_payoff(c), cbin.min_payoff(c)
print 'Put in Butterfly max/min:', pbin.max_payoff(c), pbin.min_payoff(c)
print 'CCPP Condor max/min:', ci.max_payoff(c), ci.min_payoff(c)
print 'PPCC Condor max/min:', pi.max_payoff(c), pi.min_payoff(c)
print 'Call Butterfly min less CCPP min:', cb.min_payoff(c)-ci.min_payoff(c)
print 'Put Butterfly min less CCPP min:', pb.min_payoff(c)-ci.min_payoff(c)
print 'Call Butterfly min less PPCC min:', cb.min_payoff(c)-pi.min_payoff(c)
print 'Put Butterfly min less PPCC min:', pb.min_payoff(c)-pi.min_payoff(c)

signal.signal(signal.SIGINT, cleanup)
