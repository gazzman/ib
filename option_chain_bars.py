#!/usr/local/bin/jython
__version__ = ".00"
__author__ = "gazzman"
__copyright__ = "(C) 2013 gazzman GNU GPL 3."
__contributors__ = []
from datetime import datetime
from decimal import Decimal
from time import sleep
import signal
import socket
import time as timemod

from com.ib.client import EWrapperMsgGenerator

from ib.get_ib_data import *
from ib.contractkeys import Index, OptionLocal, Stock

SHOWS = ('trades', 'bid', 'ask')

class ChainClient(Client):
    underconkey = None
    contracts = None
    req_map = dict()
    dbinfo = None
    host = None
    port = None
    finished_hist_req = False
    mdata = {'underlying': None,
             'osi_underlying': None,
             'strike_interval': None,
             'strike_start': None,
             'expiry': None}

    def osi_symbol(self, right, strike):
        return '%-6s%i%s%08i' % (self.mdata['osi_underlying'], 
                                 self.mdata['expiry'], 
                                 right.upper(), strike*1000)

    def gen_option_contracts(self, right, links):
        if right.lower() == 'b': rights = ['C', 'P']
        else: rights = [right.upper()]

        conkeys = [(OptionLocal(self.osi_symbol(r, 
                                                self.mdata['strike_start'] 
                                            + i*self.mdata['strike_interval'])),
                    '%s_%02i' % (r.lower(), i))
                   for r in rights for i in xrange(0, links)]
        self.contracts = [(self.request_contract_details(conkey)[0].m_summary,
                           colnamebase)
                          for conkey, colnamebase in conkeys]
        self.mdatastring = ['%s=%s' % x for x in self.mdata.items()]


    def get_data(self, historical=False, end_time=None, duration='7200 S', 
                 bar_size='5 secs'):
        try:
            assert type(self.contracts) is not tuple
        except AssertionError:
            msg1 = "ChainClient contracts tuple not created."
            msg2 = "Try running 'gen_option_contracts' first."
            logger.error('%s %s', msg1, msg2)

        for contract, colnamebase in self.contracts:
            for show in SHOWS:
                s = datetime.now()
                if historical:
                    self.finished_hist_req = False
                    req_id = self.request_historical_data(contract, 
                                                          end_time=end_time, 
                                                          duration=duration, 
                                                          bar_size=bar_size, 
                                                          show=show.upper())
                else:
                    self.finished_hist_req = True
                    req_id = self.start_realtime_bars(contract, 
                                                      show=show.upper())
                self.req_map[req_id] = (colnamebase, show)
                while not (self.finished_hist_req or req_id in self.req_errs):
                    sleep(1)
                time_to_wait = 10.01 - (datetime.now() - s).seconds
                sleep(max(0, time_to_wait))

    def data_handler(self, reqId, date, open_, high, low, close, volume, count, 
                     WAP, hasGaps=False):
        showbase = self.req_map[reqId]
        try:
            base = '%s_%s' % showbase
        except TypeError:
            base = showbase

        if self.port is None:
            msg = EWrapperMsgGenerator.historicalData(reqId, date, open_, high, 
                                                      low, close, volume, 
                                                      count, WAP, hasGaps)
            print self.mdata['underlying'], base, msg
        else:
            bar = [('open', open_), ('high', high), ('low', low), 
                   ('close', close), ('hasgaps', hasGaps)]
            if 'trade' in base:
                bar += [('volume', volume), ('count', count), ('wap', WAP)]
            data = self.mdatastring + ['timestamp=%s' % date]
            data += ['%s_%s=%s' % (base, name, data) for name, data in bar]

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            sock.sendall('%s,%s\n' % (self.dbinfo, ','.join(data)))
            sock.close()

    def historicalData(self, reqId, date, open_, high, low, close, volume, 
                       count, WAP, hasGaps):
        assert type(hasGaps) is int
        if hasGaps == 0: hasGaps = False
        else: hasGaps = True
        self.data_handler(reqId, date, open_, high, low, close, volume, 
                            count, WAP, hasGaps)
        if 'finished' in date: self.finished_hist_req = True

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, 
                    count):
        timestamp = timemod.strftime('%Y%m%d %H:%M:%S', 
                                     timemod.localtime(time))
        self.data_handler(reqId, timestamp, open_, high, low, close, volume, 
                          count, wap)

def cleanup(signal, frame):
    c.cancel_all_realtime_bars()
    print >> sys.stderr, "Option Chain bars stopped."
    c.disconnect()
    sys.exit(0)

if __name__ == "__main__":
    description = 'Start Interactive Brokers option chain bars.'
    description += ' This script starts realtime or historical'
    description += ' option chain bars. It can output to stdout'
    description += ' or to a db.'

    default_cid = 67
    default_api_port = 7496
    default_links = 32
    default_right = 'b'
    end_time_help = DTFMT.replace('%', '%%')
    duration_help = '<integer> <unit>, unit is either S, D, W, M, Y.'
    symbol_help = 'The underlying\'s ticker symbol.'
    osi_underlying_help = 'The symbol used for the OSI code. This can differ'
    osi_underlying_help += ' from the underlying ticker for various reasons,'
    osi_underlying_help += ' like option contract size'
    osi_underlying_help += ' (eg SPY vs SPY7 vs SPYJ)'
    osi_underlying_help += ' or option contract expiry frequency'
    osi_underlying_help += ' (eg SPX vs SPXW vs SPXQ). If not specified, then'
    osi_underlying_help += ' the \'symbol\' argument is used.'
    
    strike_start_help = 'The lowest strike price in the chain.'
    strike_interval_help = 'The strike price interval.'
    links_help = 'The total number of links in the chain.'
    links_help += ' Defaults to %s' % default_links
    right_help = 'The right of the options, \'c\'all, \'p\'ut, or \'b\'oth.'
    right_help += ' Defaults to %s' % default_right
    expiry_help = 'The option expirys. Format is %%y%%m%%d'

    client_id_help = 'TWS client id. Default is %i' % default_cid
    api_port_help = 'TWS API port. Default is %i' % default_api_port
    host_help = 'Default is localhost'
    tablename_help = 'Default is chain_[EXPIRY]_links_[LINKS]_right_[RIGHT]'

    p = argparse.ArgumentParser(description=description)
    p.add_argument('symbol', type=str, help=symbol_help, nargs='+')
    p.add_argument('strike_start', type=float, help=strike_start_help)
    p.add_argument('strike_interval', type=float, help=strike_interval_help)
    p.add_argument('expiry', type=int, help=expiry_help)
    p.add_argument('--links', type=int, default=default_links, help=links_help)
    p.add_argument('--right', type=str, default=default_right, 
                    choices=['c', 'p', 'b'], help=right_help)
    p.add_argument('--osi_underlying', type=str, help=osi_underlying_help)
    p.add_argument('-v', '--version', action='version', 
                   version='%(prog)s ' + __version__)

    hist = p.add_argument_group('ChainClient Settings')
    hist.add_argument('--historical', action='store_true')
    hist.add_argument('--end_time', help=end_time_help, nargs='+')
    hist.add_argument('--duration', help=duration_help, nargs='+')

    cc = p.add_argument_group('ChainClient Settings')
    cc.add_argument('--client_id', type=int, default=default_cid,
                    help=client_id_help)
    cc.add_argument('--api_port', type=int, default=default_api_port,
                    help=api_port_help)

    db = p.add_argument_group('Database Settings')
    db.add_argument('--database')
    db.add_argument('--schema', default='public')
    db.add_argument('--tablename', help=tablename_help)

    chain2db = p.add_argument_group('CHAIN2DB Server Settings')
    chain2db.add_argument('--host', default='localhost', help=host_help)
    chain2db.add_argument('--port', type=int)

    args = p.parse_args()
    if not args.tablename: 
        args.tablename = 'chain_%i_links_%02i_right_%s' % (args.expiry, 
                                                            args.links,
                                                            args.right)

    today = datetime.now().date().isoformat()
    mkt_close = datetime.strptime('%s%s' % (today, '16:00:30'), 
                                  '%Y-%m-%d%H:%M:%S')

    # Set client parameters and connect
    c = ChainClient(client_id=args.client_id)

    c.dbinfo = '%s,%s,%s,%s,%s' % (args.database, args.schema, args.tablename, 
                                   args.links, args.right)
    c.host = args.host
    c.port = args.port

    c.mdata['underlying'], c.underconkey = conkey_generator(args.symbol)
    if args.osi_underlying: 
        c.mdata['osi_underlying'] = args.osi_underlying.upper()
    else: 
        c.mdata['osi_underlying'] = c.mdata['underlying']
    c.mdata['strike_start'] = args.strike_start
    c.mdata['strike_interval'] = args.strike_interval    
    c.mdata['expiry'] = args.expiry

    c.connect(port=args.api_port)
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    c.gen_option_contracts(args.right, args.links)

    # Start bars for the option chain
    if args.historical:
        hargs = dict([(k, ' '.join(args.__dict__[k]))
                      for k in ('end_time', 'duration') if args.__dict__[k]])
        c.get_data(historical=True, **hargs)

    # Sleep until the end of the day
    else:
        c.get_data()
        seconds_to_finish = (mkt_close - datetime.now()).seconds
        c.logger.info('Started CHAIN bars. Waiting %i seconds for mkt close',
                      seconds_to_finish)
        timemod.sleep(seconds_to_finish)
        c.cancel_all_realtime_bars()
        print >> sys.stderr, "Day complete."
    c.disconnect()
    sys.exit(0)
