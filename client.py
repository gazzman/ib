#!/usr/local/bin/jython
try: from collections import OrderedDict #>=2.7
except ImportError: from ordereddict import OrderedDict #2.6
from datetime import datetime
from time import sleep
import csv
import sys

from com.ib.client import (Contract, EWrapper, EWrapperMsgGenerator, 
                           EClientSocket)
import java.util.Vector as Vector

class DataHelpers():
    headers = OrderedDict()
    headers['conId'] = int()
    headers['symbol'] = str()
    headers['secType'] = str()
    headers['expiry'] = str()
    headers['strike'] = float()
    headers['right'] = str()
    headers['multiplier'] = str()
    headers['exchange'] = str()
    headers['currency'] = str()
    headers['localSymbol'] = str()
    headers['comboLegs'] = Vector()
    headers['primaryExch'] = str()
    headers['includeExpired'] = bool()
    headers['secIdType'] = str()
    headers['secId'] = str()

    def gen_contract_list(self, csvfile):
        contract_list = list()
        cdata = csv.DictReader(open(csvfile, 'rb'))
        for row in cdata:
            for header in self.headers:
                if header not in row:
                    row[header] = self.headers[header]
            ordered_row = map(lambda x: row[x], self.headers)
            contract_list.append(Contract(*ordered_row))
        return contract_list

class CallbackBase(EWrapper):
    contracts_dict = dict()
    errs_dict = dict()
    satisfied_requests = dict()

    def __init__(self):
        self.m_client = EClientSocket(self)

    def connect(self, host='', port=7496, client_id=101):
        self.client_id = client_id
        self.m_client.eConnect(host, port, client_id)

    def disconnect(self):
        self.m_client.eDisconnect()

    def _errmsghandler(self, errmsg):
        print >> sys.stderr, errmsg

    def error(self, *args):
        if len(args) == 3 and args[0] >= 0:
            (request_id, err_code, err_msg) = args
            self.errs_dict[request_id] = (err_code, err_msg)
        errmsg = EWrapperMsgGenerator.error(*args)
        self._errmsghandler(errmsg)

    def _msghandler(self, msg, request_id=None, order_id=None):
        if request_id is not None:
            self.satisfied_requests[request_id] = datetime.now()
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
        msg = EWrapperMsgGenerator.openEnd()
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
        cn = contractDetails.m_summary
        self.contracts_dict[(cn.m_symbol, cn.m_secType, 
                             cn.m_currency, cn.m_exchange)] = cn
        msg = EWrapperMsgGenerator.contractDetails(reqId, contractDetails)
        self._msghandler(msg, request_id=reqId)

    def contractMsg(self, contract):
        msg = EWrapperMsgGenerator.contractMsg(contract)
        self._msghandler(msg)

    def bondContractDetails(self, reqId, contractDetails):
        msg = EWrapperMsgGenerator.bondContractDetails(reqId, contractDetails)
        self._msghandler(msg, request_id=reqId)

    def contractDetailsEnd(self, reqId):
        msg = EWrapperMsgGenerator.contractDetailsEnd(reqId)
        self._msghandler(msg, request_id=reqId)

    def execDetails(self, reqId, contract, execution):
        msg = EWrapperMsgGenerator.execDetails(reqId, contract, execution)
        self._msghandler(msg, request_id=reqId)

    def execDetailsEnd(self, reqId):
        msg = EWrapperMsgGenerator.execDetailsEnd(reqId)
        self._msghandler(msg, request_id=reqId)

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
        self._msghandler(msg, request_id=reqId)

    def scannerParameters(self, xml):
        msg = EWrapperMsgGenerator.scannerParameters(xml)
        self._msghandler(msg)

    def scannerData(self, reqId, rank, contractDetails, distance, benchmark, 
                    projection, legsStr):
        msg = EWrapperMsgGenerator.scannerData(reqId, rank, contractDetails, 
                                               distance, benchmark, 
                                               projection, legsStr)
        self._msghandler(msg, request_id=reqId)

    def scannerDataEnd(self, reqId):
        msg = EWrapperMsgGenerator.scannerDataEnd(reqId)
        self._msghandler(msg, request_id=reqId)

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, 
                    count):
        msg = EWrapperMsgGenerator.realtimeBar(reqId, time, open_, high, low, 
                                               close, volume, wap, count)
        self._msghandler(msg, request_id=reqId)

    def currentTime(self, time):
        msg = EWrapperMsgGenerator.currentTime(time)
        self._msghandler(msg)

    def fundamentalData(self, reqId, data):
        msg = EWrapperMsgGenerator.fundamentalData(reqId, data)
        self._msghandler(msg, request_id=reqId)

    def deltaNeutralValidation(self, reqId, underComp):
        msg = EWrapperMsgGenerator.deltaNeutralValidation(reqId, underComp)
        self._msghandler(msg, request_id=reqId)

    def tickSnapshotEnd(self, tickerId):
        msg = EWrapperMsgGenerator.tickSnapshotEnd(tickerId)
        self._msghandler(msg)

    def marketDataType(self, reqId, marketDataType):
        msg = EWrapperMsgGenerator.marketDataType(reqId, marketDataType)
        self._msghandler(msg, request_id=reqId)

class Requestor(CallbackBase, DataHelpers):
    request_id = 0

    def cache_contracts(self, contract_list):
        if type(contract_list) is str():
            contract_list = gen_contract_list(contract_list)
        
        first_request = self.request_id + 1
        for s in l:
            self.request_id += 1
            cn = Contract()
            (cn.m_symbol, cn.m_secType, cn.m_currency, cn.m_exchange) = s
            self.m_client.reqContractDetails(self.request_id, cn)
        last_request = self.request_id
        big = set(range(first_request, last_request + 1))
        lil = set(['pooper'])
        while not lil.issubset(big):
            print >> sys.stderr, big
            print >> sys.stderr, lil
            lil = set(self.errs_dict.keys() + self.satisfied_requests.keys())
            print >> sys.stderr, 'No there yet holmes!'
            sleep(1)

    def get_contract(self, *args, **kwargs):
        '''
        Make sure to pass args as a 4-tuple of 
            (symbol, secType, currency, exchange) if it's a stock
        
        '''
        if args not in self.contracts_dict:# or refresh:
            self.request_id += 1
            cn = Contract()
            (cn.m_symbol, cn.m_secType, cn.m_currency, cn.m_exchange) = args
            self.m_client.reqContractDetails(self.request_id, cn)
            while not (args in self.contracts_dict):
                if self.request_id in self.errs_dict:
                    (e_code, e_msg) = errs_dict[self.request_id]
                    del errs_dict[self.request_id]
                    raise BaseError(' | '.join([request_id, e_code, e_msg]))
                sleep(3)
        return self.contracts_dict[args]        
