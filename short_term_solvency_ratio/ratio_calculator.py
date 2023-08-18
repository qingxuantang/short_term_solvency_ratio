
import pandas as pd
import time
import yfinance as yf
import re
import os
from importlib import reload
from short_term_solvency_ratio import utils
utils = reload(utils)

pkg_path = utils.pkg_path
filename = re.findall('(.*).py', os.path.basename(__file__)) #name excluding extension
utils.errorLog(pkg_path=pkg_path,filename=filename)

config = utils.config




class ShortTermSolvencyCalculator:
    '''This class is used to calculate short term solvency ratio for a list of stocks.'''
    def __init__(self, config, file_path):
        self.config = config
        self.file_path = file_path
        # Initialize other properties here
        self.fi_list_yfiance = config['fi_list_yfinance']
        self.data_path = config['data_path']
        self.broker_picked_stock_path = config['broker_picked_stock_path']


    def aShareSymbolIteration(self,file_path,st_column=1):
        stock_df = pd.read_excel(file_path)
        stock_df[st_column] = stock_df[st_column].astype(str)
        stock_df[st_column] = stock_df[st_column].str.zfill(6)
        return stock_df[st_column]


    def fiDataParsing(self, st):
        '''Retreive fundamental data from Yahoo Finance with yfinance package and parse it into a dataframe.'''
        e_yahooFinance = utils.listingSuffixForParsing(exchange=None,symbol=st)[1]
        if e_yahooFinance != '':
            stock = yf.Ticker(st+e_yahooFinance)
            for fi in self.fi_list_yfiance:
                try:
                    # use the getattr function to dynamically access an attribute of an object by its name
                    attribute = getattr(stock, fi)
                    df_name = attribute.reset_index()
                    utils.savingDfToCsv(path_head='tbl',exchange='',path_tail='.csv',df_name=df_name,data_path=self.data_path,mode='w',st=st,path_add=fi.lower(),folder_path='grpFiData/')
                except Exception as e:
                    utils.exceptionLog(pkg_path,filename,func_name=ShortTermSolvencyCalculator.fiDataParsing.__name__,error=e,loop_item=fi)
                    time.sleep(10)
                    continue


    def calcShortTermSolvencyRatioYFinance(self, st, report_type='quarterly'): #quarterly or annual
        '''Calculate short term solvency ratio with fi data from Yahoo Finance.'''    
        if report_type == 'quarterly':
            balance_sheet = utils.loadDfFromCsv(path_head='tbl',exchange='',path_tail='.csv',data_path=self.data_path,st=st,path_add='quarterly_balance_sheet',folder_path='grpFiData/')
            cashflow = utils.loadDfFromCsv(path_head='tbl',exchange='',path_tail='.csv',data_path=self.data_path,st=st,path_add='quarterly_cashflow',folder_path='grpFiData/')
        elif report_type == 'annual':
            balance_sheet = utils.loadDfFromCsv(path_head='tbl',exchange='',path_tail='.csv',data_path=self.data_path,st=st,path_add='balance_sheet',folder_path='grpFiData/')
            cashflow = utils.loadDfFromCsv(path_head='tbl',exchange='',path_tail='.csv',data_path=self.data_path,st=st,path_add='cashflow',folder_path='grpFiData/')
        
        # Retrieve the latest date of the financial statement
        latest_date = balance_sheet.columns[1]
        
        # Retrieve the operating cash flow and investing cash flow from cashflow statement
        operating_cash_flow = cashflow.loc[cashflow['index'] == 'Cash Flowsfromusedin Operating Activities Direct', latest_date].values[0]
        investing_cash_flow = cashflow.loc[cashflow['index'] == 'Investing Cash Flow', latest_date].values[0]
        
        # Retrieve balance sheet items
        short_term_debt_list = ['Current Debt And Capital Lease Obligation'] # This is the combination of current debt and current portion of noncurrent debt.
        if short_term_debt_list[0] in balance_sheet['index'].values: #THIS IS ALL: current debt + current portion of noncurrent debt.
            short_term_debt = balance_sheet.loc[balance_sheet['index'] == short_term_debt_list[0], latest_date].values[0]
        else: #Alternatively, calc current debt by subtracting long term debt from total debt.
            if 'Total Debt' in balance_sheet['index'].values:
                total_debt = balance_sheet.loc[balance_sheet['index'] == 'Total Debt', latest_date].values[0]
                long_term_debt_list = ['Long Term Debt','Long Term Debt And Capital Lease Obligation','Long Term Capital Lease Obligation']
                if long_term_debt_list[0] in balance_sheet['index'].values:
                    long_term_debt = balance_sheet.loc[balance_sheet['index'] == long_term_debt_list[0], latest_date].values[0]
                elif long_term_debt_list[1] in balance_sheet['index'].values:
                    long_term_debt = balance_sheet.loc[balance_sheet['index'] == long_term_debt_list[1], latest_date].values[0]
                elif long_term_debt_list[2] in balance_sheet['index'].values:
                    long_term_debt = balance_sheet.loc[balance_sheet['index'] == long_term_debt_list[2], latest_date].values[0]
                short_term_debt = total_debt - long_term_debt
            else:
                short_term_debt = None
        
        if short_term_debt != None:
            # Calculate total cash flow
            total_cash_flow = operating_cash_flow + investing_cash_flow
            #short_term_debt = current_debt + current_portion_of_noncurrent_debt
            # Calculate short term solvency ratio
            short_term_solvency_ratio = total_cash_flow / (short_term_debt + utils.epsilon)
        else:
            short_term_solvency_ratio = None
        return short_term_solvency_ratio


    def calculate(self):
        symbol_picked = self.aShareSymbolIteration(file_path=self.file_path)
        symbol_picked = list(set(symbol_picked)) # Getting rid of duplicates.
        print(utils.printoutHeader())
        print('Total Count of Broker picked Symbols: ',len(symbol_picked))
        st_column = 1
        #Load in the broker picked stock dataframe generated by eastmoney_parser.
        broker_picked_stock_df = pd.read_excel(self.file_path)
        broker_picked_stock_df[st_column] = broker_picked_stock_df[st_column].astype(str)
        broker_picked_stock_df[st_column] = broker_picked_stock_df[st_column].str.zfill(6)
        broker_picked_stock_df['short_term_solvency_ratio'] = float('NaN')

        for st in symbol_picked:
            try:
                self.fiDataParsing(st=st)
                short_term_solvency_ratio = self.calcShortTermSolvencyRatioYFinance(st=st, report_type='quarterly')
                if short_term_solvency_ratio != None:
                    # Assign the calculated ratio to the new column for the rows where the symbol matches st
                    broker_picked_stock_df.loc[broker_picked_stock_df[st_column] == st, 'short_term_solvency_ratio'] = short_term_solvency_ratio

            except Exception as e:
                utils.exceptionLog(pkg_path, filename, func_name=ShortTermSolvencyCalculator.calculate.__name__, error=e, loop_item=st)
                continue
        sorted_df = broker_picked_stock_df.sort_values(by=["short_term_solvency_ratio"], ascending=False)
        utils.savingDfToCsv(path_head='tbl', exchange='', path_tail='.csv', df_name=sorted_df, data_path=self.config['data_path'], mode='w', path_add='StockPickedWithSolvencyR', suffix=utils.timestamp) # If generating date is different, will save to a new file.
