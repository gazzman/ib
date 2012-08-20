#!/usr/local/bin/jython
from datetime import datetime
from time import sleep
import csv
import sys

from com.ib.client import EWrapper, EWrapperMsgGenerator, EClientSocket
from com.ib.client import ComboLeg, Contract, Order

from _helpers import _DateHelpers

class ClientData():
    contracts_dict = dict()
    errs_dict = dict()
    satisfied_requests = dict()

class CallbackBase(ClientData):
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
        m_conId = contractDetails.m_summary.m_conId
        self.contracts_dict[m_conId] = contractDetails
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

class Requestor(_DateHelpers):
    request_id = 0
    fmt = '%Y%m%d %H:%M:%S GMT'

    def _contract_builder(self, contract_dict):
        contract = Contract()
        for m in dir(contract):
            if m in contract_dict: setattr(contract, m, contract_dict[m])
        return contract

    def _import_contract_list(self, csvfile):
        contract_list = list()
        cdata = csv.DictReader(csvfile)
        for row in cdata:
            contract_list.append(self._contract_builder(row))
        return contract_list

    def load_contract_list(self, contract_list, refresh=False):
        if not self.m_client.isConnected():
            raise BaseException('Try connecting first.')

        while type(contract_list) is not list:
            if type(contract_list) is file:
                contract_list = self._import_contract_list(contract_list)
            elif type(contract_list) is dict:
                contract_list = [contract_list]
            else:
                raise TypeError('Valid types are file, dict, and list.')

        first_request = self.request_id + 1
        for contract in contract_list:
            if type(contract) is not Contract:
                contract = self._contract_builder(contract)
            self.request_id += 1
            self.m_client.reqContractDetails(self.request_id, contract)
        last_request = self.request_id
        lil = set(range(first_request, last_request + 1))
        big = set(self.errs_dict.keys() + self.satisfied_requests.keys())
        count = 0
        while not lil.issubset(big):
            count += 1
            big = set(self.errs_dict.keys() + self.satisfied_requests.keys())
            if count % 10 == 0:
                print >> sys.stderr, 'Waiting for responses...'
                sleep(.01)

    def get_contract_list(self, cd_match=dict(), c_match=dict()):
        sub_contract_dict = dict()
        for m_conId in self.contracts_dict:
            con_det = self.contracts_dict[m_conId]
            if m_conId not in sub_contract_dict and len(cd_match) > 0:
                for m in cd_match:
                    if getattr(con_det, m) == cd_match[m]: 
                        sub_contract_dict[m_conId] = con_det
                        break
            if m_conId not in sub_contract_dict and len(c_match) > 0:
                con = self.contracts_dict[m_conId].m_summary
                for m in c_match:
                    if getattr(con, m) == c_match[m]: 
                        sub_contract_dict[m_conId] = con_det
                        break
        return sub_contract_dict

    def get_mkt_data(self, contract_list):
        for contract in contract_list:
            self.request_id += 1
            self.m_client.reqMktData(self.request_id, contract, None, True)

    def get_historical_data(self, contract_list, date=None, duration='1 D', 
                            bar_sz='5 mins', show='TRADES', useRTH=1):
        if date is None:
            to_date = self._convert_to_gmt(datetime.now()).strftime(self.fmt)
        else:
            to_date = self._convert_to_gmt(date).strftime(self.fmt)

        for contract in contract_list:
            self.request_id += 1
            self.m_client.reqHistoricalData(self.request_id, contract, to_date, 
                                            duration, bar_sz, show, useRTH, 1)

    def get_rt_bar(self, contract_list, bar_sz=5, show='TRADES', 
                   useRTH=1):
        for contract in contract_list:
            self.request_id += 1
            self.m_client.reqRealTimeBars(self.request_id, contract, bar_sz, 
                                          show, useRTH)

class OrderEntry():
    def order_builder(self, order_dict):
        order = Order()
        for m in order:
            if m in order_dict: setattr(order, m, order_dict[m])
        return order

    def gen_combo_contract(self, primitive_contracts_dict):
        combo_contract = Contract()
        combo_contract.m_symbol = 'USD'
        combo_contract.m_secType = 'BAG'
        combo_contract.m_currency = 'USD'
        for pc in primitive_contracts_dict:
            leg = ComboLeg()
            leg.m_conId = pc.m_conId
            leg.m_exchange = pc.m_exchange
            leg.m_action = primitive_contracts_dict[pc]['m_action']
            leg.m_ratio = primitive_contracts_dict[pc]['m_ratio']
            combo_contract.m_comboLegs.add(leg)
        return combo_contract            
            

class Client(Requestor, OrderEntry, CallbackBase, EWrapper):
    def __init__(self):
        self.m_client = EClientSocket(self)

    def connect(self, host='', port=7496, client_id=101):
        self.client_id = client_id
        self.m_client.eConnect(host, port, client_id)

    def disconnect(self):
        self.m_client.eDisconnect()
