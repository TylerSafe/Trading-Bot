# Video link:
# https://www.youtube.com/watch?v=d3j2zYXKSUs&ab_channel=TradeOptionsWithMe
# https://www.quantconnect.com/forum/discussion/13125/options-trade-with-stop-loss-and-profit-taking/p1

class WellDressedAsparagusKoala(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 1, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        equity = self.AddEquity("AMD", Resolution.Minute) 
        equity.SetDataNormalizationMode(DataNormalizationMode.Raw) # options only support raw data
        self.equity = equity.Symbol
        self.SetBenchmark(self.equity) # set stock as the benchmark
        self.vwap = self.VWAP(self.equity, 390)
        
        option = self.AddOption("AMD", Resolution.Minute)
        option.SetFilter(-2, 2, timedelta(7), timedelta(14)) # get options contracts within 2 strikes that expire between 7 and 14 days from today
        
        self.high = self.MAX(self.equity, 120) # highest price in last 120 mins
        self.low = self.MIN(self.equity, 120) # lowest price in last 120 mins
        
        self.Schedule.On(self.DateRules.EveryDay(), self.TimeRules.At(16, 00, 00), Action(self.Resetting)) # at the end of the day reset vwap data

    
    def OnData(self, data: Slice):
        if not self.high.IsReady or not self.low.IsReady: # if high or low indicator is not ready to use return until it is
            return

        option_invested = [x.Key for x in self.Portfolio if x.Value.Invested and x.Value.Type == SecurityType.Option] # check if already invested
        
        #if option_invested:
        #    if self.Time + timedelta(4) > option_invested[0].ID.Date: # if there are 4 days left to expiration sell contract
        #        self.Liquidate(option_invested[0], "Too close to expiration")
        #    return
        
        #if self.Securities[self.equity].Price >= self.high.Current.Value: # if the price has reached the highest of last month
        #    for i in data.OptionChains:
        #        chains = i.Value
        #        self.BuyCall(chains)
                
        CurrentPrice = self.Securities[self.equity].Price # get the current price of stock
        
        if CurrentPrice == self.vwap.Current.Value: # if the price has reached the highest of last month
            for i in data.OptionChains:
                chains = i.Value
                self.BuyCall(chains)
        
        if option_invested:        
            if CurrentPrice >= self.BuyIn * 1.02 or CurrentPrice <= self.BuyIn * 0.99: # if stock price decreases by 1% or increases by 2% sell contract
                self.Liquidate() # need to make it specific to the contract in question or ticker
                
    def BuyCall(self, chains):
        expiry = sorted(chains, key = lambda x: x.Expiry, reverse = True)[0].Expiry # get the furthest expiration date (greater than 7, less than 14)
        calls = [i for i in chains if i.Expiry == expiry and i.Right == OptionRight.Call] # filter out only call options
        call_contracts = sorted(calls, key = lambda x: abs(x.Strike - x.UnderlyingLastPrice)) # sort contracts by closest to the money
        
        if len(call_contracts) == 0:
            return
        self.call = call_contracts[0] # contract with closest strike to current price (ATM)
        
        quantity = self.Portfolio.TotalPortfolioValue / self.call.AskPrice 
        quantity = int(0.05 * quantity / 100) # invest 5% of portfolio in option
        self.Buy(self.call.Symbol, quantity) # buy the contract
        self.BuyIn = CurrentPrice # set record of price the of the stock when the contract was purchased (need to work out option price)
        
    def OnOrderEvent(self, orderEvent): # handle options being assigned
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        if order.Type == OrderType.OptionExercise:
            self.Liquidate()
            
    def Resetting(self):
        self.vwap.Reset()