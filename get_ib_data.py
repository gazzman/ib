#!/usr/local/bin/jython
__version__ = ".00"
__author__ = "gazzman"
__copyright__ = "(C) 2013 gazzman GNU GPL 3."
__contributors__ = []
from datetime import datetime
from time import sleep
import argparse
import csv
import logging
import re
import sys

from ib.client import Client
from ib.contractkeys import CurrencyLocal, Stock, OptionLocal

DTFMT = '%Y%m%d %H:%M:%S' 

if __name__ == "__main__":
    description = 'Pull historical contract data from Interactive Brokers.\n'
    description += 'Currently supports equities, equity options, and forex.'
    eq_help = 'For equities, enter the ticker symbol, eg. AA.'
    eqop_help = 'For equity options, enter the 21 character OSI code.'
    forex_help = 'For forex, the format is base.price, eg. EUR.USD.' 
    symbol_help = '%s\n%s\n%s' % (eq_help, eqop_help, forex_help)

    end_time_help = DTFMT.replace('%', '%%')
    duration_help = '<integer> <unit>, unit is either S, D, W, M, Y.'
    outfile_help = 'name of file in which to store data'
    bar_sizes = ['1 secs', '5 secs', '10 secs', '15 secs', '30 secs', '1 min', 
                 '2 mins', '3 mins', '5 mins', '10 mins', '15 mins', '20 mins',
                 '30 mins', '1 hour', '2 hours', '3 hours', '4 hours',
                 '8 hours', '1 day', '1 week', '1 month']
    shows = ['TRADES', 'MIDPOINT', 'BID', 'ASK', 'BID_ASK', 
             'HISTORICAL_VOLATILITY', 'OPTION_IMPLIED_VOLATILITY', 
             'OPTION_VOLUME', 'OPTION_OPEN_INTEREST']

    p = argparse.ArgumentParser(description=description)
    p.add_argument('symbol', type=str, help=symbol_help, nargs='+')
    p.add_argument('-v', '--version', action='version', 
                   version='%(prog)s ' + __version__)
    p.add_argument('--end_time', help=end_time_help)
    p.add_argument('--duration', help=duration_help, default='1 D')
    p.add_argument('--bar_size', choices=bar_sizes, default='1 min')
    p.add_argument('--show', choices=shows, default='TRADES')
    p.add_argument('--outfile', help=outfile_help)

    args = p.parse_args()
    symbol = [x.upper() for x in args.symbol]

    if len(symbol) == 1:
        symbol = symbol[0]
        if re.match('CAD|CHF|EUR|GBP|USD.[A-Z]{3}', symbol[0]):
            conkey = CurrencyLocal(symbol)
        else:
            conkey = Stock(symbol)
    elif re.match('[0-9]{6}[CP][0-9]{8}', symbol[1]):
        symbol = (' '*(6 - len(symbol[0]))).join(symbol)
        conkey = OptionLocal(symbol)
    else:
        raise Exception('Unknown symbol format: %s' % ' '.join(symbol))

    if not args.outfile:
        args.outfile = '%s_%s_%s.txt' % (args.show, args.bar_size, symbol)

    c = Client(client_id=72)
    c.connect()

    details = c.request_contract_details(conkey)
    try:
        if len(details) != 1: 
            c.disconnect()
            raise Exception('More than one contract found')
    except TypeError:
        c.disconnect()
        raise Exception('No contract found for this symbol')
    contract = details[0].m_summary

    req_id = c.request_historical_data(contract, end_time=args.end_time, 
                                       duration=args.duration, 
                                       bar_size=args.bar_size,
                                       show=args.show, fname=args.outfile)
    while req_id not in c.satisfied_requests.keys() + c.req_errs.keys():
        sleep(.25)

    c.disconnect()
