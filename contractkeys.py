#!/usr/local/bin/jython
__version__ = ".00"
__author__ = "gazzman"
__copyright__ = "(C) 2013 gazzman GNU GPL 3."
__contributors__ = []
from collections import namedtuple

ContractId = namedtuple('ContractId', ['m_conId'])
Currency = namedtuple('Currency', ['m_currency', 'm_symbol'])
CurrencyLocal = namedtuple('CurrencyLocal', ['m_localSymbol'])
Option = namedtuple('Option', ['m_symbol', 'm_expiry', 'm_right', 'm_strike'])
OptionLocal = namedtuple('OptionLocal', ['m_localSymbol'])
Stock = namedtuple('Stock', ['m_symbol'])
