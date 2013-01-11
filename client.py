#!/usr/local/bin/jython
from datetime import datetime
from time import sleep
import csv
import sys

from com.ib.client import EWrapper, EWrapperMsgGenerator, EClientSocket
from com.ib.client import Contract

from helpers._helpers import _DateHelpers

class CallbackBase():
    satisfied_requests = dict()
    errs_dict = dict()
    requested_contracts = dict()
    orders = dict()

    def _errmsghandler(self, errmsg):
        print >> sys.stderr, errmsg

    def error(self, *args):
        if len(args) == 3 and args[0] >= 0:
            (req_id, err_code, err_msg) = args
            self.errs_dict[req_id] = (err_code, err_msg)
        errmsg = EWrapperMsgGenerator.error(*args)
        self._errmsghandler(errmsg)

    def _msghandler(self, msg, req_id=None, order_id=None):
        if req_id is not None:
            self.satisfied_requests[req_id] = datetime.now()
        print >> sys.stderr, msg

    def tickPrice(self, tickerId, field, price, canAutoExecute):
        msg = EWrapperMsgGenerator.tickPrice(tickerId, field, price, 
                                             canAutoExecute)
        self._msghandler(msg)

    def tickSize(self, tickerId, field, size):
        msg = EWrapperMsgGenerator.tickSize(tickerId, field, size)
        self._msghandler(msg)

    def tickOptionComputation(self, tickerId, field, impliedVol, delta, 
                              optPrice, pvDividend, gamma, vega, theta, 
                              undPrice):
        msg = EWrapperMsgGenerator.tickOptionComputation(tickerId, field, 
                                                         impliedVol, delta, 
                                                         optPrice, pvDividend, 
                                                         gamma, vega, theta, 
                                                         undPrice)
        self._msghandler(msg)

    def tickGeneric(self, tickerId, tickType, value):
        msg = EWrapperMsgGenerator.tickGeneric(tickerId, tickType, value)
        self._msghandler(msg)

    def tickString(self, tickerId, tickType, value):
        msg = EWrapperMsgGenerator.tickString(tickerID, tickType, value)
        self._msghandler(msg)

    def tickEFP(self, tickerId, tickType, basisPoints, formattedBasisPoints, 
                impliedFuture, holdDays, futureExpiry, dividendImpact, 
                dividendsToExpiry):
        msg = EWrapperMsgGenerator.tickEFP(tickerId, tickType, basisPoints, 
                                           formattedBasisPoints, impliedFuture, 
                                           holdDays, futureExpiry, 
                                           dividendImpact, dividendsToExpiry) 
        self._msghandler(msg)

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, 
                    permId, parentId, lastFillPrice, clientId, whyHeld):

        self.orders[orderId] = {'status': status, 'filled': filled, 
                                'remaining': remaining, 
                                'avgFillPrice': avgFillPrice, 'permId': permId,
                                'parentId': parentId, 
                                'lastFillPrice': lastFillPrice,
                                'clientId': clientId, 'whyHeld': whyHeld}

        msg = EWrapperMsgGenerator.orderStatus(orderId, status, filled, 
                                               remaining, avgFillPrice, permId, 
                                               parentId, lastFillPrice, 
                                               clientId, whyHeld)
        self._msghandler(msg)

    def openOrder(self, orderId, contract, order, orderState):
        msg = EWrapperMsgGenerator.openOrder(orderId, contract, order, 
                                             orderState)
        self._msghandler(msg)

    def openOrderEnd(self):
        msg = EWrapperMsgGenerator.openOrderEnd()
        self._msghandler(msg)

    def updateAccountValue(self, key, value, currency, accountName):
        msg = EWrapperMsgGenerator.updateAccountValue(key, value, currency, 
                                                      accountName)
        self._msghandler(msg)

    def updatePortfolio(self, contract, position, marketPrice, marketValue, 
                        averageCost, unrealizedPNL, realizedPNL, accountName):
        msg = EWrapperMsgGenerator.updatePortfolio(contract, position, 
                                                   marketPrice, marketValue, 
                                                   averageCost, unrealizedPNL, 
                                                   realizedPNL, accountName)
        self._msghandler(msg)

    def updateAccountTime(self, timeStamp):
        msg = EWrapperMsgGenerator.updateAccountTime(timeStamp)
        self._msghandler(msg)

    def accountDownloadEnd(self, accountName):
        msg = EWrapperMsgGenerator.accountDownloadEnd(accountName)
        self._msghandler(msg)

    def nextValidId(self, orderId):
        self.nextId = orderId
        msg = EWrapperMsgGenerator.nextValidId(orderId)
        self._msghandler(msg)

    def contractDetails(self, reqId, contractDetails):
        self.requested_contracts[reqId] = contractDetails.m_summary
        msg = EWrapperMsgGenerator.contractDetails(reqId, contractDetails)
        self._msghandler(msg, req_id=reqId)

    def contractMsg(self, contract):
        msg = EWrapperMsgGenerator.contractMsg(contract)
        self._msghandler(msg)

    def bondContractDetails(self, reqId, contractDetails):
        msg = EWrapperMsgGenerator.bondContractDetails(reqId, contractDetails)
        self._msghandler(msg, req_id=reqId)

    def contractDetailsEnd(self, reqId):
        msg = EWrapperMsgGenerator.contractDetailsEnd(reqId)
        self._msghandler(msg, req_id=reqId)

    def execDetails(self, reqId, contract, execution):
        msg = EWrapperMsgGenerator.execDetails(reqId, contract, execution)
        self._msghandler(msg, req_id=reqId)

    def execDetailsEnd(self, reqId):
        msg = EWrapperMsgGenerator.execDetailsEnd(reqId)
        self._msghandler(msg, req_id=reqId)

    def updateMktDepth(self, tickerId, position, operation, side, price, size):
        msg = EWrapperMsgGenerator.updateMktDepth(tickerId, position, 
                                                  operation, side, price, size)
        self._msghandler(msg)

    def updateMktDepthL2(self, tickerId, position, marketMaker, operation, 
                         side, price, size):
        msg = EWrapperMsgGenerator.updateMktDepthL2(tickerId, position, 
                                                    marketMaker, operation, 
                                                    side, price, size)
        self._msghandler(msg)

    def updateNewsBulletin(self, msgId, msgType, message, origExchange):
        msg = EWrapperMsgGenerator.updateNewsBulletin(msgId, msgType, message, 
                                                      origExchange)
        self._msghandler(msg)

    def managedAccounts(self, accountsList):
        msg = EWrapperMsgGenerator.managedAccounts(accountsList)
        self._msghandler(msg)

    def receiveFA(self, faDataType, xml):
        msg = EWrapperMsgGenerator.receiveFA(faDataType, xml)
        self._msghandler(msg)

    def historicalData(self, reqId, date, open_, high, low, close, volume, 
                       count, WAP, hasGaps):
        msg = EWrapperMsgGenerator.historicalData(reqId, date, open_, high, 
                                                  low, close, volume, count, 
                                                  WAP, hasGaps)
        self._msghandler(msg, req_id=reqId)

    def scannerParameters(self, xml):
        msg = EWrapperMsgGenerator.scannerParameters(xml)
        self._msghandler(msg)

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, 
                    projection, legsStr):
        msg = EWrapperMsgGenerator.scannerData(reqId, rank, contractDetails, 
                                               distance, benchmark, 
                                               projection, legsStr)
        self._msghandler(msg, req_id=reqId)

    def scannerDataEnd(self, reqId):
        msg = EWrapperMsgGenerator.scannerDataEnd(reqId)
        self._msghandler(msg, req_id=reqId)

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, 
                    count):
        msg = EWrapperMsgGenerator.realtimeBar(reqId, time, open_, high, low, 
                                               close, volume, wap, count)
        self._msghandler(msg, req_id=reqId)

    def currentTime(self, time):
        msg = EWrapperMsgGenerator.currentTime(time)
        self._msghandler(msg)

    def fundamentalData(self, reqId, data):
        msg = EWrapperMsgGenerator.fundamentalData(reqId, data)
        self._msghandler(msg, req_id=reqId)

    def deltaNeutralValidation(self, reqId, underComp):
        msg = EWrapperMsgGenerator.deltaNeutralValidation(reqId, underComp)
        self._msghandler(msg, req_id=reqId)

    def tickSnapshotEnd(self, tickerId):
        msg = EWrapperMsgGenerator.tickSnapshotEnd(tickerId)
        self._msghandler(msg)

    def marketDataType(self, reqId, marketDataType):
        msg = EWrapperMsgGenerator.marketDataType(reqId, marketDataType)
        self._msghandler(msg, req_id=reqId)

class Client(CallbackBase, EWrapper):
    def __init__(self):
        self.req_id = 0
        self.m_client = EClientSocket(self)

    def connect(self, host='', port=7496, client_id=101):
        self.client_id = client_id
        self.m_client.eConnect(host, port, client_id)

    def disconnect(self):
        self.m_client.eDisconnect()

    def generate_contract(self, key_dic, show_detail=False):
        contract = Contract()
        for m in dir(contract):
            if m in key_dic: setattr(contract, m, key_dic[m])
        self.req_id += 1
        self.m_client.reqContractDetails(self.req_id, contract)
        return self.req_id
