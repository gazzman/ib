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
HISTARGS = ['end_time', 'duration', 'bar_size', 'show', 'fname']

class HistBarsClient(Client):
    symbol = None
    dbinfo = None
    host = None
    port = None

    def historicalData(self, reqId, date, open_, high, low, close, volume, 
                       count, WAP, hasGaps):
        bar = [('timestamp', date), ('open', open_), ('high', high), 
               ('low', low), ('close', close), ('hasgaps', hasGaps), 
               ('volume', volume), ('count', count), ('wap', WAP)]
        data = ['symbol=%s' % self.symbol]
        data += ['%s=%s' % (name, data) for name, data in bar]

        if not args.port and not args.fname:
            print >> sys.stderr, data
        else:
            if args.port is not None:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
                sock.sendall('%s,%s\n' % (self.dbinfo, ','.join(data)))
                sock.close()
            if args.fname is not None:
                f = open(args.fname, 'a')
                f.write('%s\n' % data)
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
    description = 'Pull historical bar data from Interactive Brokers.\n'
    description += 'Currently supports '
    description += 'indexes, equities, equity options, and forex.'

    default_cid = 68
    default_api_port = 7496
    default_show = 'TRADES'
    default_bar_size = ['1', 'min']
    default_duration = ['1', 'D']

    idx_help = 'For indexes, the format is "symbol exchange", eg. SPX CBOE.' 
    eq_help = 'For equities, enter the ticker symbol, eg. AA.'
    eqop_help = 'For equity options, enter the 21 character OSI code.'
    forex_help = 'For forex, the format is base.price, eg. EUR.USD.' 
    symbol_help = '%s\n%s\n%s\n%s' % (idx_help, eq_help, eqop_help, forex_help)

    end_time_help = DTFMT.replace('%', '%%')
    duration_help = '<integer> <unit>, unit is either S, D, W, M, Y.'
    duration_help += ' Default is %s.' % ' '.join(default_duration)
    bar_size_help = 'either 1 secs, 5 secs, 10 secs, 15 secs, 30 secs, 1 min, '
    bar_size_help += '2 mins, 3 mins, 5 mins, 10 mins, 15 mins, 20 mins, '
    bar_size_help += '30 mins, 1 hour, 2 hours, 3 hours, 4 hours, 8 hours, '
    bar_size_help += '1 day, 1W, 1M'
    bar_size_help += '. Default is %s.' % ' '.join(default_bar_size)
    show_help = 'TRADES, MIDPOINT, BID, ASK, BID_ASK' 
    show_help += ', HISTORICAL_VOLATILITY, OPTION_IMPLIED_VOLATILITY' 
#    show_help += ', OPTION_VOLUME, OPTION_OPEN_INTEREST'
    show_help += '. Defaults to %s' % default_show
    outfile_help = 'name of file in which to store data'

    client_id_help = 'TWS client id. Default is %i.' % default_cid
    api_port_help = 'TWS API port. Default is %i.' % default_api_port

    dbcommon = 'when writing directly to database'
    dbhelp = 'name of the database %s' % dbcommon
    tablename_help = 'Default is [show]_[bar_size]'

    schemahelp = 'name of the schema %s' % dbcommon
    hosthelp = ('name of the host on which the ib_bars_server is running %s'
                % dbcommon)
    porthelp = ('name of the port the ib_bars_server is listening on %s'               
                % dbcommon)

    p = argparse.ArgumentParser(description=description)
    p.add_argument('--fname', help=outfile_help)

    baropts = p.add_argument_group('Bar Size Options')
    baropts.add_argument('symbol', type=str, help=symbol_help, nargs='+')
    baropts.add_argument('-v', '--version', action='version', 
                   version='%(prog)s ' + __version__)
    baropts.add_argument('--end_time', help=end_time_help, nargs='+')
    baropts.add_argument('--duration', help=duration_help, nargs='+',
                   default=default_duration)
    baropts.add_argument('--bar_size', help=bar_size_help, nargs='+', 
                   default=default_bar_size)
    baropts.add_argument('--show', help=show_help, default=default_show)

    db = p.add_argument_group('Database Settings')
    db.add_argument('--database', default='database', help=dbhelp)
    db.add_argument('--schema', default='public', help=schemahelp)
    db.add_argument('--tablename', help=tablename_help)

    bars2db = p.add_argument_group('BAR2DB Server Settings')
    bars2db.add_argument('--host', default='localhost', help=hosthelp)
    bars2db.add_argument('--port', type=int, help=porthelp)

    bc = p.add_argument_group('HistBarsClient Settings')
    bc.add_argument('--client_id', type=int, default=default_cid,
                    help=client_id_help)
    bc.add_argument('--api_port', type=int, default=default_api_port,
                    help=api_port_help)

    args = p.parse_args()
    c = HistBarsClient(client_id=args.client_id)
    if args.end_time: args.end_time = ' '.join(args.end_time)
    if args.duration: args.duration = ' '.join(args.duration)
    if args.bar_size: args.bar_size = ' '.join(args.bar_size)
    if not args.tablename:
        args.tablename = '%s_%s' % (args.show.lower(), args.bar_size.lower())
        args.tablename = args.tablename.replace(' ', '_')
    c.dbinfo = '%s,%s,%s' % (args.database, args.schema, args.tablename)

    c.host = args.host
    c.port = args.port

    c.connect(port=args.api_port)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    c.symbol, conkey = conkey_generator(args.symbol)
    details = c.request_contract_details(conkey)

    try:
        if len(details) != 1: 
            c.disconnect()
            raise Exception('More than one contract found')
    except TypeError:
        c.disconnect()
        raise Exception('No contract found for this symbol')
    contract = details[0].m_summary

    req_args = dict([(k, v) for k, v in args._get_kwargs() 
                            if k in HISTARGS and v])
    req_id = c.request_historical_data(contract, **req_args)
    while req_id not in c.satisfied_requests.keys() + c.req_errs.keys():
        sleep(.25)
    if req_id in c.req_errs.keys(): print >> sys.stderr, c.req_errs[req_id]

    c.disconnect()
