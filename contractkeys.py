#!/usr/local/bin/jython
from collections import namedtuple

ContractId = namedtuple('ContractId', ['m_conId'])
Currency = namedtuple('Currency', ['m_currency', 'm_symbol'])
CurrencyLocal = namedtuple('CurrencyLocal', ['m_localSymbol'])
Option = namedtuple('Option', ['m_symbol', 'm_expiry', 'm_right', 'm_strike'])
OptionLocal = namedtuple('OptionLocal', ['m_localSymbol'])
Stock = namedtuple('Stock', ['m_symbol'])
