#!/usr/local/bin/jython
__version__ = ".00"
__author__ = "gazzman"
__copyright__ = "(C) 2013 gazzman GNU GPL 3."
__contributors__ = []
from decimal import Decimal
from time import sleep
import signal
import socket
import time as timemod

from com.ib.client import EWrapperMsgGenerator

from ib.get_ib_data import *
from ib.combo_orders import Butterfly
from ib.contractkeys import Index, OptionLocal, Stock

class BDClient(Client):
    SHOWS = ('BID', 'ASK', 'TRADES')
    FIELDS = ['timestamp', 'last_open', 'last_high', 'last_low', 'last_close',
              'volume', 'wap', 'count', 'bid', 'ask']
    BUTTERFLIES = 20
    BUFFER = 1

    bars = {}
    expiry = int()
    interval = float()
    show_req = {}
    strikerange = []
    strikes = []
    symbol = str()
    osi_underlying = str()

    def compute_fly_prices(self):
        butter_strikes = self.strikes[self.BUFFER:-self.BUFFER]
        flies = ()
        for right in ['C', 'P']:
            for i in range(0, len(butter_strikes) - 2):
                try:
                    bid = (self.bars[(butter_strikes[i], right, 'BID')][4]
                           - 2*self.bars[(butter_strikes[i+1], right, 'ASK')][4]
                           + self.bars[(butter_strikes[i+2], right, 'BID')][4])
                    bid = Decimal(str(bid))
                except IndexError:
                    bid = None
                try:
                    ask = (self.bars[(butter_strikes[i], right, 'ASK')][4]
                           - 2*self.bars[(butter_strikes[i+1], right, 'BID')][4]
                           + self.bars[(butter_strikes[i+2], right, 'ASK')][4])
                    ask = Decimal(str(ask))
                except IndexError:
                    ask = None
                flies += (bid, ask)
        return flies

    def gen_fields(self):
        pids = range(0, self.BUTTERFLIES/2)
        nids = list(pids)
        nids.reverse()
        for i in nids: self.FIELDS += ['bc_l%02i_bid' % i, 'bc_l%02i_ask' % i]
        for i in pids: self.FIELDS += ['bc_r%02i_bid' % i, 'bc_r%02i_ask' % i]
        for i in nids: self.FIELDS += ['bp_l%02i_bid' % i, 'bp_l%02i_ask' % i]
        for i in pids: self.FIELDS += ['bp_r%02i_bid' % i, 'bp_r%02i_ask' % i]

    def gen_osi_symbol(self, strike, right):
        return '%-6s%i%s%08i' % (c.osi_underlying, c.expiry, right, strike*1000)

    def gen_strikerange(self):
        self.strikerange = range(0-self.BUTTERFLIES/2-self.BUFFER, 
                                 self.BUTTERFLIES/2+2+self.BUFFER)

    def gen_strikes(self, bid, interval):
        n1 = self.neg1(bid, interval)
        self.strikes = tuple([n1 + interval * x for x in self.strikerange])

    def neg1(self, bid, interval): return bid - bid % interval

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, 
                    count):
        msg = EWrapperMsgGenerator.realtimeBar(reqId, time, open_, high, low, 
                                               close, volume, wap, count)
        timestamp = timemod.strftime('%Y%m%d %H:%M:%S', 
                                     timemod.localtime(time))

        strike, right, show = self.show_req[reqId]        
        self.bars[(strike, right, show)] = (timestamp, open_, high, low, close, 
                                            volume, wap, count)

        if strike == -1 and show == 'TRADES':
            self.gen_strikes(close, self.interval)

        self.l = [self.bars[x][0] for x in self.show_req.values()]
        if self.l.count(timestamp) + self.l.count(None) == len(self.l):
            try:
                flies = self.compute_fly_prices()

                try:                
                    spot = self.bars[(-1, None, 'TRADES')]\
                           + (self.bars[(-1, None, 'BID')][4], 
                              self.bars[(-1, None, 'ASK')][4])
                except IndexError:
                    spot = self.bars[(-1, None, 'TRADES')] + (None, None)
                row = ['underlying=%s' % c.symbol, 'interval=%f' % c.interval]
                for field, data in zip(self.FIELDS, spot + flies):
                    row += ['%s=%s' % (field, str(data))]
                if not c.port:
                    for datapoint in row:
                        print datapoint
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect((c.host, c.port))
                    sock.sendall('%s,%s,%s,%s\n' % (c.database, 
                                                    c.schema, 
                                                    c.tablename, 
                                                    ','.join(row)))
                    sock.close()
            except KeyError, err:
                self.logger.warn('Realtime bars (%f, %s, %s) not started yet', 
                                 *err.args[0])
                pass

    def start_option_bars(self, initial_bid, interval):
        self.gen_strikerange()
        self.gen_strikes(initial_bid, interval)
        self.gen_fields()
        for strike in self.strikes:
            for right in ['C', 'P']:
                conkey = OptionLocal(self.gen_osi_symbol(strike, right))
                contract = self.request_contract_details(conkey)[0].m_summary
                for show in self.SHOWS[:-1]:
                    req_id = self.start_realtime_bars(contract, show=show)
                    self.show_req[req_id] = (strike, right, show)
                    self.bars[self.show_req[req_id]] = (None, )
                    sleep(10.01)

def cleanup(signal, frame):
    c.cancel_all_realtime_bars()
    print >> sys.stderr, "Butterfly density bars stopped."
    c.disconnect()
    sys.exit(0)

if __name__ == "__main__":
    description = 'Start Interactive Brokers butterfly combo rt bars.'
    description += ' This script starts realtime bars for butterfly chains'
    description += ' both below and above the current spot price.'
    description += ' It automatically detects the butterfly combos whose'
    description += ' body strikes are immediately above and immediately below'
    description += ' the current spot price.'

    default_cid = 82
    default_api_port = 7496
    symbol_help = 'The underlying\'s ticker symbol.'
    osi_underlying_help = 'The symbol used for the OSI code. This can differ'
    osi_underlying_help += ' from the underlying ticker for various reasons,'
    osi_underlying_help += ' like option contract size'
    osi_underlying_help += ' (eg SPY vs SPY7 vs SPYJ)'
    osi_underlying_help += ' or option contract expiry frequency'
    osi_underlying_help += ' (eg SPX vs SPXW vs SPXQ). If not specified, then'
    osi_underlying_help += ' the \'symbol\' argument is used.'
    
    start_price_help = 'The initial spot price for determining the'
    start_price_help += ' starting butterfly body strikes.'
    interval_help = 'The strike interval used to create the butterfly combos.'
    expiry_help = 'The butterfly expiry. Format is %%y%%m%%d'

    butterflies_help = 'Total number of butterfly combos to track,'
    butterflies_help += ' half on each side of the spot.'
    butterflies_help += ' Default is %i' % BDClient.BUTTERFLIES
    buffer_help = 'Number of extra butterly combos to track on each side'
    buffer_help += ' beyond that specified in the --butterflies argument.'
    buffer_help += ' This is to help ensure that there are enough combos being'
    buffer_help += ' tracked in the event that the spot price moves beyond an' 
    buffer_help += ' adjacent body strike. Should be increased if the spot'
    buffer_help += ' is very volatile. Default is %i' % BDClient.BUFFER
    client_id_help = 'TWS client id. Default is %i' % default_cid
    api_port_help = 'TWS API port. Default is %i' % default_api_port
    host_help = 'Default is localhost'
    tablename_help = 'Default is butterfly_chains_[expiry]'

    p = argparse.ArgumentParser(description=description)
    p.add_argument('symbol', type=str, help=symbol_help, nargs='+')
    p.add_argument('start_price', type=float, help=start_price_help)
    p.add_argument('interval', type=float, help=interval_help)
    p.add_argument('expiry', type=int, help=expiry_help)
    p.add_argument('--osi_underlying', type=str, help=osi_underlying_help)
    p.add_argument('-v', '--version', action='version', 
                   version='%(prog)s ' + __version__)

    ds = p.add_argument_group('BDClient Settings')
    ds.add_argument('--butterflies', type=int, choices=xrange(2, 42, 2), 
                    help=butterflies_help)
    ds.add_argument('--buffer', type=int, choices=xrange(1, 6),
                    help=buffer_help)
    ds.add_argument('--client_id', type=int, default=default_cid,
                    help=client_id_help)
    ds.add_argument('--api_port', type=int, default=default_api_port,
                    help=api_port_help)

    db = p.add_argument_group('Database Settings')
    db.add_argument('--database')
    db.add_argument('--schema')
    db.add_argument('--tablename', help=tablename_help)

    bd2db = p.add_argument_group('BD2DB Server Settings')
    bd2db.add_argument('--host', default='localhost', help=host_help)
    bd2db.add_argument('--port', type=int)

    args = p.parse_args()
    if not args.tablename: args.tablename = 'butterfly_chains_%i' % args.expiry

    today = datetime.now().date().isoformat()
    mkt_close = datetime.strptime('%s%s' % (today, '16:00:30'),
                                  '%Y-%m-%d%H:%M:%S')

    # Set client parameters and connect
    c = BDClient(client_id=args.client_id)
    c.symbol, underconkey = conkey_generator(args.symbol)
    if args.osi_underlying: c.osi_underlying = args.osi_underlying.upper()
    else: c.osi_underlying = c.symbol
    c.expiry = args.expiry
    if args.butterflies: c.BUTTERFLIES = args.butterflies
    if args.buffer: c.BUFFER = args.buffer
    c.database = args.database
    c.schema = args.schema
    c.tablename = args.tablename
    c.host = args.host
    c.port = args.port
    c.interval = args.interval
    c.connect(port=args.api_port)

    # Start bars for the underlying
    undercon = c.request_contract_details(underconkey)[0].m_summary
    for show in c.SHOWS:
        req_id = c.start_realtime_bars(undercon, show=show)
        c.show_req[req_id] = (-1, None, show)
        c.bars[c.show_req[req_id]] = (None, )
        sleep(10.01)

    # Start bars for the option chain
    c.start_option_bars(args.start_price, c.interval)
    
    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    # Sleep until the end of the day
    seconds_to_finish = (mkt_close - datetime.now()).seconds
    c.logger.info('Started BD bars. Waiting %i seconds for mkt close',
                  seconds_to_finish)
    timemod.sleep(seconds_to_finish)
    c.cancel_all_realtime_bars()
    print >> sys.stderr, "Day complete."
    c.disconnect()
    sys.exit(0)
