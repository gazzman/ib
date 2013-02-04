#!/usr/local/bin/jython
from collections import namedtuple
import glob
import os
import shutil
import signal
import sys

from ib.client import Client
from ib.contractkeys import ContractId

pattern = './Butterfly*.mkt'
newdirname = '%(symbol)s_%(expiry)s_%(right)s'
newfilename = '%(strike1)06.2f_%(strike2)06.2f_%(strike3)06.2f.mkt'

if __name__ == "__main__":
    c = Client(client_id=8)
    c.connect()
    filenames = glob.glob(pattern)
    for filename in filenames:
        conIds = filename.split('.mkt')[0].split('_')[1:]
        conIds = [int(x) for x in conIds]
        strikes = []
        for conId in conIds:
            contract = c.request_contract_details(ContractId(conId))[0].m_summary
            strikes.append(contract.m_strike)
        ndname = newdirname % {'symbol': contract.m_symbol, 
                              'expiry': contract.m_expiry,
                              'right': contract.m_right}
        if not os.path.exists(ndname): os.makedirs(ndname)
        nfname = newfilename % {'strike1': strikes[0],
                                'strike2': strikes[1],
                                'strike3': strikes[2]}
        shutil.copyfile(filename, '/'.join([ndname, nfname]))
    c.disconnect()
