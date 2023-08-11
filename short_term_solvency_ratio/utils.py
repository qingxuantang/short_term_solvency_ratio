# -*- coding: UTF-8 -*-

import json
import re
import os
from datetime import datetime
import math
import pandas as pd

pkg_path = 'short_term_solvency_ratio/' #the python package's folder name
epsilon = math.exp(-10) #Add a small number to avoid zerodivisionerror.
timestamp = datetime.today()
timestamp = timestamp.strftime('%Y-%m-%d')

def loadJSON(json_name):
    import json
    with open('./'+pkg_path+json_name+'.json') as f:
        json_data = json.load(f)
    return json_data

config = loadJSON(json_name='config')


def printoutHeader():
    def returnTimeNow():
        return str(datetime.now())
    return "---------\n" + returnTimeNow() + "\n"


filename = re.findall('(.*).py', os.path.basename(__file__))
#Log stderr into file.
def errorLog(pkg_path,filename):
    import sys
    sys.stderr = open('./'+ pkg_path +'_log_/' + filename[0] + '_stderr.txt', 'w')  # redirect stderr to file

errorLog(pkg_path=pkg_path,filename=filename)

def exceptionLog(pkg_path,filename,func_name,error,loop_item): #230303update
    with open('./'+ pkg_path +'_log_/' + filename[0] + '_exceptions.txt', 'a') as f:
        # write the exception details to the file
        f.write(printoutHeader() + 'Caught exception in ' + func_name + ' during loop of ' + loop_item + ':' + '\n' + str(error) + '\n')
    return print("Caught exception in "+func_name+" during loop of "+loop_item+":", str(error))


with open('./'+pkg_path+'alphavantageapi.json') as f:
    alpha_api = json.load(f)['alpha_api']


def listingSuffixForParsing(exchange,symbol):
    '''Add corresponding suffix to the symbol for parsing via different APIs.'''
    if exchange != None and symbol == None:
        if exchange == 'hkex': #Hong Kong Stock Exchange
            e_alphaVantage = '.HKG'
            e_yahooFinance = '.HK'
        elif exchange == 'sh': #Shanghai Stock Exchange
            e_alphaVantage = '.SHH'
            e_yahooFinance = '.SS'
        elif exchange == 'sz': #Shenzhen Stock Exchange
            e_alphaVantage = '.SHZ'
            e_yahooFinance = '.SZ'
        elif exchange == 'nyse':
            e_alphaVantage = ''
            e_yahooFinance = ''
        elif exchange == 'nasdaq':
            e_alphaVantage = ''
            e_yahooFinance = ''
        elif exchange == '':
            e_alphaVantage = ''
            e_yahooFinance = ''

    if exchange == None and symbol != None:
        if symbol[0] == '0' or symbol[0] == '3':
            e_alphaVantage = '.SHZ'
            e_yahooFinance = '.SZ'
        elif symbol[0] == '6' or symbol[0] == '9':
            e_alphaVantage = '.SHH'
            e_yahooFinance = '.SS'
        elif symbol[0] == '8': # Beijing Stock Exchange
            e_alphaVantage = '' # Leave blank for the moment
            e_yahooFinance = ''    

    return e_alphaVantage,e_yahooFinance


def savingDfToCsv(path_head,exchange,path_tail,df_name,data_path,mode='w',st='',interval='',i_n_str='',path_add='',suffix='',folder_path=''):
    with open(data_path + pkg_path + folder_path + path_head + st + exchange + i_n_str + interval + path_add + suffix + path_tail,mode,encoding='GBK') as s:
        df_name.replace('\xa0', ' ', regex=True, inplace=True) #Replace characters that cannot be encoded by GBK.
        df_name.replace("", pd.NA, inplace=True)
        df_name.dropna(how='all', inplace=True) #Drop all nan rows.
        print(df_name)
        df_name.to_csv(s,index=False,encoding='GBK')


def loadDfFromCsv(path_head,exchange,path_tail,data_path,st='',interval='',i_n_str='',path_add='',suffix='',folder_path=''):
    df = pd.read_csv(data_path + pkg_path + folder_path + path_head + st + exchange + i_n_str + interval + path_add + suffix + path_tail, encoding='GBK')
    return df


