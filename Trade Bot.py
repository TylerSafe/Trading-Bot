class SmoothApricotFox(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)  # Set Start Date
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)  # Set Strategy Cash
        
        spy = self.AddEquity("SPY", Resolution.Daily) # get data in Minute time frame (tick is lowest)
        
        spy.SetDataNormalizationMode(DataNormalizationMode.Raw)
        
        self.spy = spy.Symbol # remove ambiguity when referring to SPY
        
        self.SetBenchmark("SPY") # compare performance against the SPY
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin) # set to fee structure of IBKR
        
        self.entryPrice = 0
        self.period = timedelta(31) # only invest every 31 days
        self.nextEntryTime = self.Time
        

    def OnData(self, data):
        
        price = data[self.spy].Close # get closing price of spy yesterday
        
        if not self.Portfolio.Invested: # make sure we aren't already invested in the spy
            if self.nextEntryTime <= self.Time: # we are only investing every 31 days
                self.SetHoldings(self.spy, 1)
                # self.MarketOrder(self.spy, int(self.Portfolio.Cash / price))
                self.Log("Buy SPY @" + str(price)) # add data to log
                self.entryPrice = price
        elif self.entryPrice * 1.1 < price or self.entryPrice * 0.95 > price:
            self.Liquidate(self.spy) # liquidate all positions in spy
            self.Log("Sell SPY @" + str(price))
            self.nextEntryTime = self.Time + self.period # start timer until we can invest again