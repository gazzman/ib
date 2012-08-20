#!/usr/local/bin/jython
__version__ = ".00"
__author__ = "gazzman"
__copyright__ = "(C) 2012 gazzman GNU GPL 3."
__contributors__ = []
try: from collections import OrderedDict #>=2.7
except ImportError: from ordereddict import OrderedDict #2.6
import argparse
import csv
import pickle

import com.ib.client.Contract as Contract

def gen_picklefile(csvfile, picklefile):
    contract_list = list()
    cdata = csv.DictReader(open(csvfile, 'rb'))
    for row in cdata:
        contract = Contract()
        for m in dir(contract):
            if m in row: setattr(contract, m, row[m])
        contract_list.append(contract)
    pickle.dump(contract_list, open(picklefile, 'wb'), pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    desc = ' '.join(['A script to pickle a csv as a list of', 
                    'com.ib.client.Contract objects. The script calls the', 
                    'com.ib.client.Contract constructor, so the csv file', 
                    'headers must contain one or more of the fields used in', 
                    'the Contract constructor. You should include enough', 
                    'fields to uniquely id the contract you are interested', 
                    'in. Otherwise, you may end up using too many resources.'])

    p = argparse.ArgumentParser(description=desc)
    p.add_argument('inputfile', type=str, 
                   help='A csv of contract data. Not all fields need values.')

    p.add_argument('-o', metavar='outputfile', default=None, dest='outputfile', 
                   help='The destination file.')
    args = p.parse_args()

    if args.outputfile is None:
        args.outputfile = '.'.join([args.inputfile.partition('.')[0], 'pkl'])

    gen_picklefile(args.inputfile, args.outputfile)
