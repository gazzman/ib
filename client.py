#!/usr/local/bin/jython
__version__ = ".00"
__author__ = "gazzman"
__copyright__ = "(C) gazzman GNU GPL 3."
__contributors__ = []
from datetime import datetime, timedelta
from time import sleep
from logging.handlers import TimedRotatingFileHandler
import java.io.EOFException
import logging
import sys

from com.ib.client import EWrapper, EWrapperMsgGenerator, EClientSocket
from com.ib.client import Contract, ExecutionFilter

from ib.contractkeys import (ContractId, Currency, CurrencyLocal,
                             Option, OptionLocal, Stock)
from ib.tick_types import tick_types

LOGLEVEL = logging.DEBUG
CONKEYTYPES = [ContractId, Currency, CurrencyLocal, Option, OptionLocal, Stock]

class CallbackBase():
    realtime_bars = dict()
    historical_data = dict()
    mkt_data = dict()
    fundamentals = dict()
    satisfied_requests = dict()
    req_errs = dict()
    orders = dict()

    req_cds = dict()
    fulfilled_contracts = dict()
    fulfilled_open_orders_req = dict()
    fulfilled_execution_req = dict()
    fulfilled_tick_snapshots = dict()
    failed_contracts = dict()
    data_requests = dict()
    executions = dict()
    mkt_data_requests = dict()

    # Callback data handlers
    def error(self, *args):
        ''' We either get an (int, int, str), (Exception, ), or (str, )
        '''
        errmsg = EWrapperMsgGenerator.error(*args)
        errmsg = ' '.join(errmsg.split('\n'))
        if len(args) == 3:
            (req_id, err_code, err_msg) = args
            if err_code == 200:
                self.failed_contracts[req_id] = (err_code, err_msg)
            elif req_id >= 0: self.req_errs[req_id] = (err_code, err_msg)
            if err_code == 162: self.logger.warn(errmsg) # historical data
            elif err_code == 200: self.logger.warn(errmsg) # no contract
            elif err_code == 202: self.logger.info(errmsg) # cancel order
            elif err_code == 399: self.logger.warn(errmsg) # after-hours
            elif err_code < 1100: self.logger.error(errmsg)
            elif err_code < 2100: self.logger.critical(errmsg)
            else: self.logger.warn(errmsg)
        elif type(args[0]) is (Exception or java.io.EOFException):
            self.logger.error(args[0])
            raise args[0]
        elif type(args[0]) is str: self.logger.error(errmsg)
        else:
            m = 'Unexpected result from AnyWrapperMsgGenerator: %s, %s'
            self.logger.error(m, str(args[0]), str(type(args[0])))

    def msghandler(self, msg, req_id=None, order_id=None):
        if req_id is not None:
            self.satisfied_requests[req_id] = datetime.now()
        self.logger.info(msg)

    def datahandler(self, fnm, req_id, datamsg):
        self.logger.debug('Received datapoint for req_id %i' % req_id)
        f = open(fnm, 'a') 
        f.write('%s\n' % datamsg)
        f.close()
        self.logger.debug('Wrote datapoint for req_id %i to %s', req_id, fnm)

    def currentTime(self, time):
        msg = EWrapperMsgGenerator.currentTime(time)
        self.msghandler(msg)

    # Order callbacks
    def nextValidId(self, orderId):
        self.nextId = orderId
        msg = EWrapperMsgGenerator.nextValidId(orderId)
        self.logger.info('nextValidID: ' + msg)

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, 
                    permId, parentId, lastFillPrice, clientId, whyHeld):

        if clientId not in self.orders: self.orders[clientId] = dict()
        self.orders[clientId][orderId] = {'status': status, 'filled': filled, 
                                          'remaining': remaining, 
                                          'avgFillPrice': avgFillPrice,
                                          'permId': permId,
                                          'parentId': parentId, 
                                          'lastFillPrice': lastFillPrice,
                                          'clientId': clientId,
                                          'whyHeld': whyHeld}

#        msg = EWrapperMsgGenerator.orderStatus(orderId, status, filled, 
#                                               remaining, avgFillPrice, permId, 
#                                               parentId, lastFillPrice, 
#                                               clientId, whyHeld)
        msg = 'submitted by: %2i, oid: %2i, status: %s'
        self.msghandler(msg % (clientId, orderId, status))

    def openOrder(self, orderId, contract, order, orderState):
#        msg = EWrapperMsgGenerator.openOrder(orderId, contract, order, 
#                                             orderState)
        msg = 'submitted by: %2i, oid: %2i, action: %s, type: %s, symbol: %s'
        msg = ', '.join([msg,  'secType: %s, qty: %3i'])
        msg_data = (order.m_clientId, orderId, order.m_action, 
                    order.m_orderType, contract.m_symbol, contract.m_secType,
                    order.m_totalQuantity)
        self.msghandler(msg % msg_data)

    def openOrderEnd(self):
        msg = EWrapperMsgGenerator.openOrderEnd()
        self.msghandler(msg)

    # Account callbacks
    def updateAccountValue(self, key, value, currency, accountName):
        msg = EWrapperMsgGenerator.updateAccountValue(key, value, currency, 
                                                      accountName)
        self.msghandler('updateAccVal: ' + msg)

    def updatePortfolio(self, contract, position, marketPrice, marketValue, 
                        averageCost, unrealizedPNL, realizedPNL, accountName):
        msg = EWrapperMsgGenerator.updatePortfolio(contract, position, 
                                                   marketPrice, marketValue, 
                                                   averageCost, unrealizedPNL, 
                                                   realizedPNL, accountName)
        self.msghandler('updatePort: ' + msg)

    def updateAccountTime(self, timeStamp):
        msg = EWrapperMsgGenerator.updateAccountTime(timeStamp)
        self.msghandler('updateAccTime: ' + msg)

    def accountDownloadEnd(self, accountName):
        msg = EWrapperMsgGenerator.accountDownloadEnd(accountName)
        self.msghandler('acctDLEnd: ' + msg)

    def managedAccounts(self, accountsList):
        msg = EWrapperMsgGenerator.managedAccounts(accountsList)
        self.logger.info(msg)

    def receiveFA(self, faDataType, xml):
        msg = EWrapperMsgGenerator.receiveFA(faDataType, xml)
        self.msghandler('receiveFA: ' + msg)

    # Contract callbacks
    def contractDetails(self, reqId, contractDetails):
        if reqId not in self.req_cds:  self.req_cds[reqId] = list()
        self.req_cds[reqId].append(contractDetails)
#        msg = EWrapperMsgGenerator.contractDetails(reqId, contractDetails)
        msg = 'reqId = %i received details for'
        msg = ' '.join([msg,  'con_id: %i symbol: %s, secType: %s'])
        msg_data = (reqId, contractDetails.m_summary.m_conId,
                    contractDetails.m_summary.m_symbol,
                    contractDetails.m_summary.m_secType)
        self.msghandler(msg % msg_data, req_id=reqId)

    def contractMsg(self, contract):
        msg = EWrapperMsgGenerator.contractMsg(contract)
        self.msghandler('contractMsg: ' + msg)

    def bondContractDetails(self, reqId, contractDetails):
        msg = EWrapperMsgGenerator.bondContractDetails(reqId, contractDetails)
        self.msghandler('bondConDet: ' + msg, req_id=reqId)

    def contractDetailsEnd(self, reqId):
        msg = EWrapperMsgGenerator.contractDetailsEnd(reqId)
        self.fulfilled_contracts[reqId] = datetime.now()
        self.msghandler(msg)

    # Execution callbacks
    def execDetails(self, reqId, contract, execution):
        msg = EWrapperMsgGenerator.execDetails(reqId, contract, execution)
        self.executions[execution.m_execId] = (reqId, contract, execution)
        if execution.m_orderId == sys.maxint: oid = 0
        else: oid = execution.m_orderId
        msg = 'Client %2i executed oid %4i: %s %3i %5s %s at price %7.3f,'
        msg += ' avgprice %7.3f'
        msg_data = (execution.m_clientId, oid, execution.m_side,
                    execution.m_cumQty, contract.m_symbol, contract.m_secType,
                    execution.m_price, execution.m_avgPrice)
        self.msghandler(msg % msg_data, req_id=reqId)

    def execDetailsEnd(self, reqId):
        msg = EWrapperMsgGenerator.execDetailsEnd(reqId)
        self.fulfilled_execution_req[reqId] = datetime.now()
        self.msghandler(msg, req_id=reqId)

    # Data callbacks
    def updateMktDepth(self, tickerId, position, operation, side, price, size):
        msg = EWrapperMsgGenerator.updateMktDepth(tickerId, position, 
                                                  operation, side, price, size)
        self.msghandler('updateMktDepth: ' + msg)

    def updateMktDepthL2(self, tickerId, position, marketMaker, operation, 
                         side, price, size):
        msg = EWrapperMsgGenerator.updateMktDepthL2(tickerId, position, 
                                                    marketMaker, operation, 
                                                    side, price, size)
        self.msghandler('updateMktDepthL2: ' + msg)

    def updateNewsBulletin(self, msgId, msgType, message, origExchange):
        msg = EWrapperMsgGenerator.updateNewsBulletin(msgId, msgType, message, 
                                                      origExchange)
        self.msghandler('updateNewsBull: ' + msg)

    def historicalData(self, reqId, date, open_, high, low, close, volume, 
                       count, WAP, hasGaps):
        msg = EWrapperMsgGenerator.historicalData(reqId, date, open_, high, 
                                                  low, close, volume, count, 
                                                  WAP, hasGaps)
        fnm = '%i_%s_HD.csv' % self.historical_data[reqId]
        self.datahandler(fnm, reqId, msg)

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, 
                    count):
        msg = EWrapperMsgGenerator.realtimeBar(reqId, time, open_, high, low, 
                                               close, volume, wap, count)
        fnm = '%i_%s_RTD.csv' % self.realtime_bars[reqId]
        self.datahandler(fnm, reqId, msg)

    def fundamentalData(self, reqId, data):
        msg = EWrapperMsgGenerator.fundamentalData(reqId, data)
        fnm = '%i_%s_FD.csv' % self.fundamentals[req_id]
        self.datahandler(fnm, req_id, msg)

    # Scanner callbacks
    def scannerParameters(self, xml):
        msg = EWrapperMsgGenerator.scannerParameters(xml)
        self.msghandler('scannerParams: ' + msg)

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, 
                    projection, legsStr):
        msg = EWrapperMsgGenerator.scannerData(reqId, rank, contractDetails, 
                                               distance, benchmark, 
                                               projection, legsStr)
        self.msghandler('scannerData: ' + msg, req_id=reqId)

    def scannerDataEnd(self, reqId):
        msg = EWrapperMsgGenerator.scannerDataEnd(reqId)
        self.msghandler('scannerDataEnd: ' + msg, req_id=reqId)

    # Market data Tick callbacks
    def tickPrice(self, tickerId, field, price, canAutoExecute):
        msg = EWrapperMsgGenerator.tickPrice(tickerId, field, price, 
                                             canAutoExecute)
        fnm = '%i_%s_TP.csv' % self.mkt_data[tickerId]
        self.msghandler(msg)
        msg = '%s %s' % (datetime.now().isoformat(), msg)
        self.datahandler(fnm, tickerId, msg)

    def tickSize(self, tickerId, field, size):
        msg = EWrapperMsgGenerator.tickSize(tickerId, field, size)
        fnm = '%i_%s_TS.csv' % self.mkt_data[tickerId]
        self.msghandler(msg)
        msg = '%s %s' % (datetime.now().isoformat(), msg)
        self.datahandler(fnm, tickerId, msg)

    def tickOptionComputation(self, tickerId, field, impliedVol, delta, 
                              optPrice, pvDividend, gamma, vega, theta, 
                              undPrice):
        msg = EWrapperMsgGenerator.tickOptionComputation(tickerId, field, 
                                                         impliedVol, delta, 
                                                         optPrice, pvDividend, 
                                                         gamma, vega, theta, 
                                                         undPrice)
        self.msghandler('tickOptComp: ' + msg)

    def tickGeneric(self, tickerId, tickType, value):
        msg = EWrapperMsgGenerator.tickGeneric(tickerId, tickType, value)
        self.msghandler('tickGen: ' + msg)

    def tickString(self, tickerId, tickType, value):
        msg = EWrapperMsgGenerator.tickString(tickerID, tickType, value)
        self.msghandler('tickString: ' + msg)

    def tickEFP(self, tickerId, tickType, basisPoints, formattedBasisPoints, 
                impliedFuture, holdDays, futureExpiry, dividendImpact, 
                dividendsToExpiry):
        msg = EWrapperMsgGenerator.tickEFP(tickerId, tickType, basisPoints, 
                                           formattedBasisPoints, impliedFuture, 
                                           holdDays, futureExpiry, 
                                           dividendImpact, dividendsToExpiry) 
        self.msghandler('tickEFP: ' + msg)

    def deltaNeutralValidation(self, reqId, underComp):
        msg = EWrapperMsgGenerator.deltaNeutralValidation(reqId, underComp)
        self.msghandler('deltaNeutralValid: ' + msg, req_id=reqId)

    def tickSnapshotEnd(self, tickerId):
        msg = EWrapperMsgGenerator.tickSnapshotEnd(tickerId)
        self.fulfilled_tick_snapshots[tickerId] = datetime.now()
        self.msghandler(msg)

    def marketDataType(self, reqId, marketDataType):
        msg = EWrapperMsgGenerator.marketDataType(reqId, marketDataType)
        self.msghandler('marketDataType: ' + msg, req_id=reqId)

class Client(CallbackBase, EWrapper):
    cached_cds = dict()
    id_to_cd = dict()
    stk_base = {'m_secType': 'STK', 'm_exchange': 'SMART', 'm_currency': 'USD'}
    opt_base = {'m_secType': 'OPT', 'm_exchange': 'SMART', 'm_currency': 'USD'}
    fx_base = {'m_secType': 'CASH'}

    def __init__(self, client_id=9):
        self.client_id = client_id
        self.init_logger()
        self.req_id = 0
        self.m_client = EClientSocket(self)
        tt = [x.strip() for x in tick_types.split('\n') if x.strip() != '']
        tt = [x.split(',') for x in tt]
        self.tick_types = dict([(int(x[0]), x[1]) for x in tt])

    def init_logger(self):
        cid = '%2i' % self.client_id
        logger_fmt = ' '.join(['%(levelno)s, [%(asctime)s #%(process)5i]',
                               'client', cid, '%(levelname)8s: %(message)s'])
        self.logger = logging.getLogger(__name__)
        hdlr = TimedRotatingFileHandler('ib_client.log', when='midnight')
        fmt = logging.Formatter(fmt=logger_fmt)
        hdlr.setFormatter(fmt)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(LOGLEVEL)

    def connect(self, host='', port=7496):
        self.m_client.eConnect(host, port, self.client_id)

    def disconnect(self):
        self.m_client.eDisconnect()
        self.logger.info('Client disconnected')

    def request_contract_details(self, key):
        if key not in self.cached_cds: 
            args = key._asdict()
            if type(key) == ContractId and key[0] in self.id_to_cd: 
                return self.id_to_cd[key[0]]
            elif type(key) in (Currency, CurrencyLocal):
                args.update(self.fx_base)
            elif type(key) in (Option, OptionLocal): 
                args.update(self.opt_base)
            elif type(key) == Stock: 
                args.update(self.stk_base)
            else:
                errmsg = 'Valid arg types are %s; not %s'
                raise TypeError(errmsg % (', '.join(CONKEYTYPES), str(type(key)))) 
            args = dict([(k, v) for (k, v) in args.items() if v])
            contract = Contract(**args)
            self.req_id += 1
            self.m_client.reqContractDetails(self.req_id, contract)
            while self.req_id not in self.fulfilled_contracts: sleep(.5)
            self.cached_cds[key] = self.req_cds[self.req_id]
            for cd in self.req_cds[self.req_id]: 
                self.id_to_cd[cd.m_summary.m_conId] = cd
        return self.cached_cds[key]

    # Request data methods
    def request_mkt_data(self, contract, gtick_list='', snapshot=True):
        if gtick_list != '': snapshot=False
        elif snapshot: gtick_list = ''
        self.req_id += 1
        self.data_requests[self.req_id] = datetime.now()
        self.mkt_data[self.req_id] = (contract.m_conId, gtick_list)
        self.m_client.reqMktData(self.req_id, contract, gtick_list, snapshot)
        return self.req_id

    def start_realtime_bars(self, contract, show='TRADES'):
        if self.too_many_requests(): return None
        self.req_id += 1
        self.data_requests[self.req_id] = datetime.now()
        self.realtime_bars[self.req_id] = (contract.m_conId, show)
        self.m_client.reqRealTimeBars(self.req_id, contract, 5, show, 0)
        return self.req_id

    def request_historical_data(self, contract, end_time=None, duration='1 D',
                                bar_size='1 min', show='TRADES'):
        if self.too_many_requests(): return None
        if not end_time: end_time = datetime.now().strftime('%Y%m%d %H:%M:%S')
        self.req_id += 1
        self.data_requests[self.req_id] = datetime.now()
        self.historical_data[self.req_id] = (contract.m_conId, show)
        self.m_client.reqHistoricalData(self.req_id, contract, end_time,
                                        duration, bar_size, show, 1, 1)
        return self.req_id

    def request_fundamentals(self, contract, report_type):
        if self.too_many_requests(): return None
        self.req_id += 1
        self.data_requests[self.req_id] = datetime.now()
        self.fundamentals[self.req_id] = (contract.m_conId, report_type)
        self.m_client.reqFundamentalData(self.req_id, contract, report_type)
        return self.req_id

    # Cancel data methods
    def cancel_mkt_data(self, req_id):
        self.m_client.cancelMktData(req_id)
        del self.mkt_data[req_id]
        self.logger.info('Market data canceled for req_id %i', req_id)
        return True

    def cancel_realtime_bars(self, req_id):
        self.m_client.cancelRealTimeBars(req_id)
        del self.realtime_bars[req_id]
        self.logger.info('Realtime bars canceled for req_id %i', req_id)
        return True

    def cancel_historical_data(self, req_id):
        self.m_client.cancelHistoricalData(req_id)
        del self.historical_data[req_id]
        self.logger.info('Historical data canceled for req_id %i', req_id)
        return True

    def cancel_fundamentals(self, req_id):
        self.m_client.cancelFundamentalData(req_id)
        del self.fundamentals[req_id]
        self.logger.info('Fundamentals canceled for req_id %i', req_id)
        return True

    # Cancel all data methods
    def cancel_all_mkt_data(self):
        bar_ids = self.mkt_data.keys()
        [self.cancel_mkt_data(x) for x in bar_ids]

    def cancel_all_realtime_bars(self):
        bar_ids = self.realtime_bars.keys()
        [self.cancel_realtime_bars(x) for x in bar_ids]

    def cancel_all_historical_data(self):
        historical_ids = self.historical_data.keys()
        [self.cancel_historical_data(x) for x in historical_ids]

    def cancel_all_fundamentals(self):
        fundamental_ids = self.fundamentals.keys()
        [self.cancel_fundamentals(x) for x in fundamental_ids]

    # Orders and Executions methods
    def place_order(self, contract, order):
        order_id = self.nextId
        self.m_client.placeOrder(self.nextId, contract, order)
        self.m_client.reqIds(1)
        while order_id == self.nextId: 
            self.logger.debug('Waiting for next order id')
            sleep(.1)
        return order_id

    def request_open_orders(self):
        self.m_client.reqOpenOrders()        

    def request_all_orders(self):
        self.m_client.reqAllOpenOrders()

    def cancel_order(self, order_id):
        self.m_client.cancelOrder(order_id)
        del self.orders[self.client_id][order_id]

    def cancel_open_orders(self):
        self.request_open_orders()
        if self.client_id not in self.orders:
            self.logger.error('Client has no open orders')
        else:
            order_ids = self.orders[self.client_id].keys()
            [self.cancel_order(x) for x in order_ids
            if self.orders[self.client_id][x]['status'].lower() != 'cancelled']

    def request_executions(self, client_id=None, time=None, symbol=None,
                           sec_type=None, side=None, exchange=None):
        args = {'m_clientId': client_id, 'm_time': time, 'm_symbol': symbol,
                'm_secType': sec_type, 'm_side': side, 'm_exchange': exchange}
        args = dict([(k, v) for (k, v) in args.items() if v])
        self.req_id += 1
        self.m_client.reqExecutions(self.req_id, ExecutionFilter(**args))

    # Helper methods
    def too_many_requests(self):
        since = datetime.now() - timedelta(seconds=600)
        count =len([x for x in self.data_requests.values() if x > since])
        if count >= 60: return True
        else: return False
