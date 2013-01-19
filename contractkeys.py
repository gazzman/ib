#!/usr/local/bin/jython
from collections import namedtuple

Stock = namedtuple('Stock', ['m_symbol'])
Option = namedtuple('Option', ['m_symbol', 'm_expiry', 'm_right', 'm_strike'])
OptionLocal = namedtuple('OptionLocal', ['m_localSymbol'])
ContractId = namedtuple('ContractId', ['m_conId'])
