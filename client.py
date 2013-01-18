#!/usr/local/bin/jython
from datetime import datetime
from time import sleep
from logging.handlers import TimedRotatingFileHandler
import java.io.EOFException
import logging
import sys

from com.ib.client import EWrapper, EWrapperMsgGenerator, EClientSocket
from com.ib.client import Contract

LOGLEVEL = logging.DEBUG

class CallbackBase():
    hist_data = dict()
    realtime_bars = dict()
    fundamental_data = dict()
    satisfied_requests = dict()
    req_errs = dict()
    req_contracts = dict()
    failed_contracts = dict()
    orders = dict()

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

    def tickPrice(self, tickerId, field, price, canAutoExecute):
        msg = EWrapperMsgGenerator.tickPrice(tickerId, field, price, 
                                             canAutoExecute)
        self.msghandler('tickPrice: ' + msg)

    def tickSize(self, tickerId, field, size):
        msg = EWrapperMsgGenerator.tickSize(tickerId, field, size)
        self.msghandler('tickSize: ' + msg)

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

    def nextValidId(self, orderId):
        self.nextId = orderId
        msg = EWrapperMsgGenerator.nextValidId(orderId)
        self.logger.info('nextValidID: ' + msg)

    def contractDetails(self, reqId, contractDetails):
        if reqId not in self.req_contracts:  self.req_contracts[reqId] = list()
        self.req_contracts[reqId].append(contractDetails.m_summary)
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
        self.msghandler(msg)

    def execDetails(self, reqId, contract, execution):
        msg = EWrapperMsgGenerator.execDetails(reqId, contract, execution)
        self.msghandler('execDetails: ' + msg, req_id=reqId)

    def execDetailsEnd(self, reqId):
        msg = EWrapperMsgGenerator.execDetailsEnd(reqId)
        self.msghandler('execDetEnd: ' + msg, req_id=reqId)

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

    def managedAccounts(self, accountsList):
        msg = EWrapperMsgGenerator.managedAccounts(accountsList)
        self.logger.info(msg)

    def receiveFA(self, faDataType, xml):
        msg = EWrapperMsgGenerator.receiveFA(faDataType, xml)
        self.msghandler('receiveFA: ' + msg)

    def historicalData(self, reqId, date, open_, high, low, close, volume, 
                       count, WAP, hasGaps):
        msg = EWrapperMsgGenerator.historicalData(reqId, date, open_, high, 
                                                  low, close, volume, count, 
                                                  WAP, hasGaps)
        fnm = '%i_%s.csv' % (self.hist_data[reqId]['contract'].m_conId,
                             self.hist_data[reqId]['show'])
        self.datahandler(fnm, reqId, msg)

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

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, 
                    count):
        msg = EWrapperMsgGenerator.realtimeBar(reqId, time, open_, high, low, 
                                               close, volume, wap, count)
        fnm = '%i_%s.csv' % (self.realtime_bars[reqId]['contract'].m_conId,
                             self.realtime_bars[reqId]['show'])
        self.datahandler(fnm, reqId, msg)

    def currentTime(self, time):
        msg = EWrapperMsgGenerator.currentTime(time)
        self.msghandler(msg)

    def fundamentalData(self, reqId, data):
        msg = EWrapperMsgGenerator.fundamentalData(reqId, data)
        fnm = '%i_%s.csv' % (self.fundamental_data[req_id]['contract'].m_conId,
                             self.fundamental_data[req_id]['show'])
        self.datahandler(fnm, req_id, msg)

    def deltaNeutralValidation(self, reqId, underComp):
        msg = EWrapperMsgGenerator.deltaNeutralValidation(reqId, underComp)
        self.msghandler('deltaNeutralValid: ' + msg, req_id=reqId)

    def tickSnapshotEnd(self, tickerId):
        msg = EWrapperMsgGenerator.tickSnapshotEnd(tickerId)
        self.msghandler('tickSnapShotEnd: ' + msg)

    def marketDataType(self, reqId, marketDataType):
        msg = EWrapperMsgGenerator.marketDataType(reqId, marketDataType)
        self.msghandler('marketDataType: ' + msg, req_id=reqId)

class Client(CallbackBase, EWrapper):
    def __init__(self, client_id=9):
        self.client_id = client_id
        self.init_logger()
        self.req_id = 0
        self.m_client = EClientSocket(self)

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

    def request_open_orders(self):
        self.m_client.reqOpenOrders()        

    def request_all_orders(self):
        self.m_client.reqAllOpenOrders()

    def cancel_order(self, order_id):
        self.m_client.cancelOrder(order_id)

    def cancel_open_orders(self):
        self.request_open_orders()
        if self.client_id not in self.orders:
            self.logger.error('Client has no open orders')
        else:
            [self.cancel_order(x) for x in self.orders[self.client_id] 
                if self.orders[self.client_id][x]['status'].lower()
                     != 'cancelled']

    def request_contract(self, key_dic):
        contract = Contract()
        [setattr(contract, m, key_dic[m]) for m in dir(contract)
            if m in key_dic]
        self.req_id += 1
        self.m_client.reqContractDetails(self.req_id, contract)
        return self.req_id

    def request_historical_data(self, contract, end_time=None, 
                                duration='1 D', bar_size='1 min', 
                                show='TRADES'):
        if not end_time: end_time = datetime.now().strftime('%Y%m%d %H:%M:%S')
        self.req_id += 1
        self.hist_data[self.req_id] = {'contract': contract, 
                                       'end_time': end_time,
                                       'duration': duration,
                                       'bar_size': bar_size,
                                       'show': show}
        self.m_client.reqHistoricalData(self.req_id, contract, end_time,
                                        duration, bar_size, show, 1, 1)
        return self.req_id

    def cancel_historical_data(self, req_id):
        self.m_client.cancelHistoricalData(req_id)

    def cancel_all_historical_data(self):
        [self.cancel_historical_data(x) for x in self.hist_data]

    def start_realtime_bars(self, contract, show='TRADES'):
        self.req_id += 1
        self.realtime_bars[self.req_id] = {'contract': contract,
                                           'show': show}
        self.m_client.reqRealTimeBars(self.req_id, contract, 5, show, 0)
        return self.req_id

    def cancel_realtime_bars(self, req_id):
        self.m_client.cancelRealTimeBars(req_id)
        del self.realtime_bars[req_id]
        self.logger.info('Realtime bars canceled for req_id %i', req_id)
        return True

    def cancel_all_realtime_bars(self):
        bar_ids = self.realtime_bars.keys()
        [self.cancel_realtime_bars(x) for x in bar_ids]

    def request_fundamentals(self, contract, report_type):
        self.req_id += 1
        self.fundamental_data[self.req_id] = {'contract': contract,
                                              'report_type': report_type}
        self.m_client.reqFundamentalData(self.req_id, contract, report_type)
        return self.req_id

    def cancel_fundamentals(self, req_id):
        self.m_client.cancelFundamentalData(req_id)

    def cancel_all_fundamentals(self):
        [self.cancel_fundamentals(x) for x in self.fundamental_data]
