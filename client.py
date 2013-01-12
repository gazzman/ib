#!/usr/local/bin/jython
from datetime import datetime
from time import sleep
from logging.handlers import TimedRotatingFileHandler
import logging
import sys

from com.ib.client import EWrapper, EWrapperMsgGenerator, EClientSocket
from com.ib.client import Contract

class CallbackBase():
    hist_data = dict()
    realtime_bars = dict()
    fundamental_data = dict()
    satisfied_requests = dict()
    request_errors = dict()
    requested_contracts = dict()
    orders = dict()

    def error(self, *args):
        errmsg = EWrapperMsgGenerator.error(*args)
        if len(args) == 3: 
            (req_id, err_code, err_msg) = args
            if req_id >= 0: self.request_errors[req_id] = (err_code, err_msg)
            if err_code == 162: self.logger.warning(errmsg)
            elif err_code < 1100: self.logger.error(errmsg)
            elif err_code < 2100: self.logger.critical(errmsg)
            else: self.logger.warning(errmsg)
        else: self.logger.error(errmsg)

    def msghandler(self, msg, req_id=None, order_id=None):
        if req_id is not None:
            self.satisfied_requests[req_id] = datetime.now()
        self.logger.info(msg)

    def datahandler(self, fnm, req_id, datamsg):
        self.logger.debug('Received datapoint for req_id %i' % req_id)
        fnm = '%i_%s.csv' % (cid, show)
        f = open(fnm, 'a') 
        f.write('%s\n' % datamsg)
        f.close()
        self.logger.debug('Wrote datapoint for req_id %i to %s' % req_id, fnm)

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

        self.orders[orderId] = {'status': status, 'filled': filled, 
                                'remaining': remaining, 
                                'avgFillPrice': avgFillPrice, 'permId': permId,
                                'parentId': parentId, 
                                'lastFillPrice': lastFillPrice,
                                'clientId': clientId, 'whyHeld': whyHeld}

#        msg = EWrapperMsgGenerator.orderStatus(orderId, status, filled, 
#                                               remaining, avgFillPrice, permId, 
#                                               parentId, lastFillPrice, 
#                                               clientId, whyHeld)
        msg = 'cid: %i, oid: %i, status: %s'
        self.msghandler(msg % (clientId, orderId, status))

    def openOrder(self, orderId, contract, order, orderState):
#        msg = EWrapperMsgGenerator.openOrder(orderId, contract, order, 
#                                             orderState)
        msg = 'cid: %i, oid: %i, action: %s, type: %s, symbol: %s, secType: %s'
        msg_data = (order.m_clientId, orderId, order.m_action, 
                    order.m_orderType, contract.m_symbol, contract.m_secType)
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
#        self.msghandler(msg)

    def contractDetails(self, reqId, contractDetails):
        self.requested_contracts[reqId] = contractDetails.m_summary
#        msg = EWrapperMsgGenerator.contractDetails(reqId, contractDetails)
        msg = 'req_id = %i recived details for'
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
        fnm = '%i_%s.csv' % (self.hist_data[req_id]['contract'].m_conId,
                             self.hist_data[req_id]['show'])
        self.datahandler(fnm, req_id, msg)

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
        fnm = '%i_%s.csv' % (self.realtime_bars[req_id]['contract'].m_conId,
                             self.realtime_bars[req_id]['show'])
        self.datahandler(fnm, req_id, msg)

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
    logger_format = ('%(levelno)s, [%(asctime)s #%(process)d]'
                     + '%(levelname)6s: %(message)s')
    logger = logging.getLogger('IBClient')

    def __init__(self):
        self.init_logger()
        self.req_id = 0
        self.m_client = EClientSocket(self)

    def init_logger(self):
        hdlr = TimedRotatingFileHandler('ib_client.log', when='midnight')
        fmt = logging.Formatter(fmt=self.logger_format)
        hdlr.setFormatter(fmt)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)

    def connect(self, host='', port=7496, client_id=101):
        self.client_id = client_id
        self.m_client.eConnect(host, port, client_id)

    def disconnect(self):
        self.m_client.eDisconnect()

    def request_contract(self, key_dic, show_detail=False):
        contract = Contract()
        [setattr(contract, m, key_dic[m]) for m in dir(contract)
            if m in key_dic]
        self.req_id += 1
        self.m_client.reqContractDetails(self.req_id, contract)
        return self.req_id

    def request_historical_data(self, contract, end_time=None, 
                                duration='1 D', bar_size='1 min', 
                                show='TRADES'):
        if not end_time: end_time = datetime.now().strftext('%Y%m%d %H:%M:%S')
        self.req_id += 1
        self.hist_data[self.req_id] = {'contract': contract, 
                                       'end_time': end_time,
                                       'duration': duration,
                                       'bar_size': bar_size,
                                       'show': show}
        self.m_client.reqHistoricalData(self.req_id, contract, end_time,
                                        duration, bar_size, show, 1, 1)

    def cancel_historical_data(self, req_id):
        self.m_client.cancelHistoricalData(req_id)

    def cancel_all_historical_data(self):
        [self.cancel_historical_data(x) for x in self.hist_data]
        
    def start_realtime_bars(self, contract, show='TRADES'):
        self.req_id += 1
        self.realtime_bars[self.req_id] = {'contract': contract,
                                           'show': show}
        self.m_client.reqRealTimeBars(self.req_id, contract, 5, show, 0)

    def cancel_realtime_bars(self, req_id):
        self.m_client.cancelRealTimeBars(req_id)

    def cancel_all_realtime_bars(self):
        [self.cancel_realtime_bars(x) for x in self.realtime_bars]

    def request_fundamentals(self, contract, report_type):
        self.req_id += 1
        self.fundamental_data[self.req_id] = {'contract': contract,
                                              'report_type': report_type}
        self.m_client.requestFundamentalData(req_id, contract, report_type)

    def cancel_fundamentals(self, req_id):
        self.m_client.cancelFundamentalData(req_id)

    def cancel_all_fundamentals(self):
        [self.cancel_fundamentals(x) for x in self.fundamental_data]
