#!/usr/local/bin/jython
__version__ = ".00"
__author__ = "gazzman"
__copyright__ = "(C) 2013 gazzman GNU GPL 3."
__contributors__ = []
import signal
import socket
import time as timemod

from com.ib.client import EWrapperMsgGenerator

from ib.get_ib_data import *

fnames = {}

class RTBarsClient(Client):
    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, 
                    count):
        msg = EWrapperMsgGenerator.realtimeBar(reqId, time, open_, high, low, 
                                               close, volume, wap, count)
        timestamp = timemod.strftime('%Y%m%d %H:%M:%S', 
                                     timemod.localtime(time))
        msg = msg.replace(str(time), timestamp)
        if not args.port:
            print >> sys.stderr, msg
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((args.host, args.port))
            sock.sendall('%s,%s,%s,0 %s\n' % (args.database, args.schema, 
                                              fnames[reqId], msg))
            sock.close()

def cleanup(signal, frame):
    c.cancel_all_realtime_bars()
    print >> sys.stderr, "Realtime bars stopped."
    c.disconnect()
    sys.exit(0)

if __name__ == "__main__":
    description = 'Start Interactive Brokers realtime bars. '
    description += 'Currently supports equities, equity options, '
    description += 'indexes, and forex.'

    eq_help = 'For equities, enter the ticker symbol, eg. AA.'
    eqop_help = 'For equity options, enter the 21 character OSI code.'
    index_help = 'For indexes, the format is "symbol exchange", eg. SPX CBOE.' 
    forex_help = 'For forex, the format is "base.price", eg. EUR.USD.' 
    symbolsfile_help = 'A space-delimited file of symbols and what to show '
    symbolsfile_help += '(BID, ASK, MID, TRADE), one per line, '
    symbolsfile_help += 'for which to start realtime bars. '
    symbolsfile_help += '%s %s %s %s' % (eq_help, eqop_help, index_help, 
                                                             forex_help)

    dbcommon = 'when writing directly to database'
    dbhelp = 'name of the database %s' % dbcommon
    schemahelp = 'name of the schema %s' % dbcommon
    hosthelp = ('name of the host on which the ib_rtbars_server is running %s'
                % dbcommon)
    porthelp = ('name of the port the ib_rtbars_server is listening on %s'               
                % dbcommon)

    p = argparse.ArgumentParser(description=description)
    p.add_argument('symbolsfile', type=str, help=symbolsfile_help)
    p.add_argument('-v', '--version', action='version', 
                   version='%(prog)s ' + __version__)
    p.add_argument('--database', default='database', help=dbhelp)
    p.add_argument('--schema', default='public', help=schemahelp)
    p.add_argument('--host', default='localhost', help=hosthelp)
    p.add_argument('--port', type=int, help=porthelp)

    args = p.parse_args()

    today = datetime.now().date().isoformat()
    mkt_close = datetime.strptime('%s%s' % (today, '20:00:00'),
                                  '%Y-%m-%d%H:%M:%S')

    c = RTBarsClient(client_id=82)
    c.connect()

    f = open(args.symbolsfile, 'r')
    for line in f:
        l = line.strip().split()
        symbol, show = l[0:-1], l[-1]
        symbol, conkey = conkey_generator(symbol)
        details = c.request_contract_details(conkey)
        try:
            if len(details) != 1: 
                c.logger.error('More than one contract found for %s', 
                                symbol)
            else:
                contract = details[0].m_summary
                req_id = c.start_realtime_bars(contract, show=show)
                fnames[req_id] = '%s_%s_%s.txt' % (show, '5 secs', symbol)
                timemod.sleep(10)
        except TypeError:
            c.logger.error('No contract found for %s', symbol)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    # Sleep until the end of the day
    seconds_to_finish = (mkt_close - datetime.now()).seconds
    c.logger.info('Started realtime bars. Waiting %i seconds for mkt close',
                  seconds_to_finish)
    timemod.sleep(seconds_to_finish)
    c.cancel_all_realtime_bars()
    print >> sys.stderr, "Day complete."
    c.disconnect()
    sys.exit(0)
