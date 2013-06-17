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
import signal
import socket
import sys
import time as timemod

from com.ib.client import EWrapperMsgGenerator

from ib.client import Client
from ib.contractkeys import CurrencyLocal, Index, Stock, OptionLocal

DTFMT = '%Y%m%d %H:%M:%S' 

class HistBarsClient(Client):
    def historicalData(self, reqId, date, open_, high, low, close, volume, 
                       count, WAP, hasGaps):
        msg = EWrapperMsgGenerator.historicalData(reqId, date, open_, high, 
                                                  low, close, volume, count, 
                                                  WAP, hasGaps)
        if not args.port and not args.fname:
            print >> sys.stderr, msg
        else:
            if args.port is not None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((args.host, args.port))
                sock.sendall('%s,%s,%s,0 %s\n' % (args.database, args.schema, 
                                                  show_size_symbol, msg))
                sock.close()
            if args.fname is not None:
                f = open(args.fname, 'a')
                f.write('%s %s\n' % (datetime.now().isoformat(), msg))
                f.close()

        if 'finished' in date:
            self.satisfied_requests[req_id] = datetime.now()
            self.logger.info('Historical data request %s finished', req_id)

def cleanup(signal, frame):
    c.cancel_all_realtime_bars()
    print >> sys.stderr, "Historical bars stopped."
    c.disconnect()
    sys.exit(0)

def conkey_generator(symbol):
    if len(symbol) == 1:
        symbol = symbol[0]
        if re.match('(CAD|CHF|EUR|GBP|USD)\.[A-Z]{3}', symbol):
            return symbol, CurrencyLocal(symbol)
        else:
            return symbol, Stock(symbol)
    elif re.match('[0-9]{6}[CP][0-9]{8}', symbol[1]):
        symbol = (' '*(6 - len(symbol[0]))).join(symbol)
        return symbol, OptionLocal(symbol)
    elif re.match('[A-Z]{1,6} [A-Z]{4,5}', ' '.join(symbol)):
        return symbol[0], Index(symbol[0], symbol[1])
    else:
        c.logger.error('Unknown symbol format: %s', ' '.join(symbol))

if __name__ == "__main__":
    description = 'Pull historical contract data from Interactive Brokers.\n'
    description += 'Currently supports '
    description += 'indexes, equities, equity options, and forex.'

    idx_help = 'For indexes, the format is "symbol exchange", eg. SPX CBOE.' 
    eq_help = 'For equities, enter the ticker symbol, eg. AA.'
    eqop_help = 'For equity options, enter the 21 character OSI code.'
    forex_help = 'For forex, the format is base.price, eg. EUR.USD.' 
    symbol_help = '%s\n%s\n%s\n%s' % (idx_help, eq_help, eqop_help, forex_help)

    end_time_help = DTFMT.replace('%', '%%')
    duration_help = '<integer> <unit>, unit is either S, D, W, M, Y.'
    bar_size_help = 'either 1 secs, 5 secs, 10 secs, 15 secs, 30 secs, 1 min, '
    bar_size_help += '2 mins, 3 mins, 5 mins, 10 mins, 15 mins, 20 mins, '
    bar_size_help += '30 mins, 1 hour, 2 hours, 3 hours, 4 hours, 8 hours, '
    bar_size_help += '1 day, 1W, 1M'
    show_help = 'TRADES, MIDPOINT, BID, ASK, BID_ASK, ' 
    show_help += 'HISTORICAL_VOLATILITY, OPTION_IMPLIED_VOLATILITY, ' 
    show_help += 'OPTION_VOLUME, OPTION_OPEN_INTEREST'
    outfile_help = 'name of file in which to store data'

    dbcommon = 'when writing directly to database'
    dbhelp = 'name of the database %s' % dbcommon
    schemahelp = 'name of the schema %s' % dbcommon
    hosthelp = ('name of the host on which the ib_bars_server is running %s'
                % dbcommon)
    porthelp = ('name of the port the ib_bars_server is listening on %s'               
                % dbcommon)

    p = argparse.ArgumentParser(description=description)
    p.add_argument('symbol', type=str, help=symbol_help, nargs='+')
    p.add_argument('-v', '--version', action='version', 
                   version='%(prog)s ' + __version__)
    p.add_argument('--end_time', help=end_time_help, nargs='+')
    p.add_argument('--duration', help=duration_help, nargs='+')
    p.add_argument('--bar_size', help=bar_size_help, nargs='+', default=['1', 'min'])
    p.add_argument('--show', help=show_help, default='TRADES')
    p.add_argument('--fname', help=outfile_help)

    p.add_argument('--database', default='database', help=dbhelp)
    p.add_argument('--schema', default='public', help=schemahelp)
    p.add_argument('--host', default='localhost', help=hosthelp)
    p.add_argument('--port', type=int, help=porthelp)

    args = p.parse_args()
    symbol = [x.upper() for x in args.symbol]
    symbol, conkey = conkey_generator(symbol)

    if args.end_time: args.end_time = ' '.join(args.end_time)
    if args.duration: args.duration = ' '.join(args.duration)
    if args.bar_size: args.bar_size = ' '.join(args.bar_size)

    show_size_symbol = '%s_%s_%s' % (args.show, args.bar_size, symbol)

    req_args = dict([x for x in args._get_kwargs() if x[1]])
    for k in  ['symbol', 'database', 'schema', 'host', 'port']:
        if k in req_args: del req_args[k]

    c = HistBarsClient(client_id=72)
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

    req_id = c.request_historical_data(contract, **req_args)
    while req_id not in c.satisfied_requests.keys() + c.req_errs.keys():
        sleep(.25)
    if req_id in c.req_errs.keys(): print >> sys.stderr, c.req_errs[req_id]

    c.disconnect()
