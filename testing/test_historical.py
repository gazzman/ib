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

symbol = 'EMC'
expiry = '20130125'
right = 'C'
details = c.request_contract_details(Option(symbol, expiry, right, None))
a = [(x.m_summary.m_conId, x.m_summary.m_strike) for x in details]  

[c.request_historical_data(x.m_summary, end_time='20130123 15:50:00', duration='1 D', bar_size='1 min', show='ASK') for x in details]


signal.signal(signal.SIGINT, cleanup)
