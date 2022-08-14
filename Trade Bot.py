# region imports
from AlgorithmImports import *
# endregion

class FormalYellowGreenCaterpillar(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2022, 1, 1)  # Set Start Date
        self.SetCash(100000)  # Set Strategy Cash
        
        self.watch_list = ["SPY", "GOOGL", "AAPL", "AMZN"]
        PORTFOLIO = len(self.watch_list)
        self.symbols = []
        self.stocks = []
        self.current_price = [0] * PORTFOLIO # save the current price to compare to previous price to check movement
        self.previous_price = [0] * PORTFOLIO
        self.percent_change = [0] * PORTFOLIO

        for i in range(len(self.watch_list)):
            option = self.AddOption(self.watch_list[i])
            self.symbols.append(option.Symbol)
            option.SetFilter(-2, 2, timedelta(0), timedelta(8)) # get options contracts within 2 strikes that expire between 0 and 8 days from today

            stock = self.AddEquity(self.watch_list[i], Resolution.Minute).Symbol # also store stock information for price tracking
            self.stocks.append(stock)

        self.Schedule.On(self.DateRules.EveryDay(self.symbols[0]), self.TimeRules.BeforeMarketClose(self.symbols[0], 10), self.ExitPositions) # exit all positions 10 mins before close


    def OnData(self, data: Slice):
        if self.Time > self.Time.replace(hour=15, minute=50) or self.Time < self.Time.replace(hour=9, minute=35): # don't trade in the last 10 mins or first 5 of the day
            return

        option_invested = [x.Key for x in self.Portfolio if x.Value.Invested and x.Value.Type==SecurityType.Option]

        for i in range(len(self.stocks)):
            self.current_price[i] = data[self.watch_list[i]].Price # save current price of each stock

            if self.previous_price[i] != 0: # ensure it isn't the first minute where no data is available
                change = self.current_price[i] - self.previous_price[i] # calculate change in price over last minute
                self.percent_change[i] = change / self.previous_price[i] # calculate the percentage change (+ or -)
        
                if i != 0: # ensure SPY has its data
                    difference = abs(self.percent_change[0] - self.percent_change[i])

                    if difference > 0.005 and self.percent_change[i] > self.percent_change[0] and self.percent_change[i] > 0: # adjust this number, difference between SPY change and watchlist stock, currently 0.5%
                        for kvp in data.OptionChains: # initiate sequence to buy an ATM call
                            if kvp.Key == self.symbols[i]:
                                chains = kvp.Value
                                self.BuyCall(chains)

                    if difference > 0.005 and self.percent_change[i] < self.percent_change[0] and self.percent_change[i] < 0: # adjust this number, difference between SPY change and watchlist stock, currently 0.5%
                        for kvp in data.OptionChains: # initiate sequence to buy an ATM put
                            if kvp.Key == self.symbols[i]:
                                chains = kvp.Value
                                self.BuyPut(chains)
        
        for i in range(len(self.stocks)):
            self.previous_price[i] = self.current_price[i] # record price for next comparison

    def BuyCall(self, chains): # buy an ATM call (market order need to change to limit)
        expiry = sorted(chains, key = lambda x: x.Expiry)[0].Expiry # get the closest expiration date
        calls = [i for i in chains if i.Expiry == expiry and i.Right == OptionRight.Call] # filter out only call options
        call_contracts = sorted(calls, key = lambda x: abs(x.Strike - x.UnderlyingLastPrice)) # sort contracts by closest to the money
        
        if len(call_contracts) == 0:
            return
        
        self.call = call_contracts[0] # contract with closest strike to current price (ATM)
        quantity = self.Portfolio.TotalPortfolioValue / self.call.AskPrice 
        quantity = int(0.05 * quantity / 100) # invest 5% of portfolio in option
        
        self.Buy(self.call.Symbol, quantity) # buy the contract
        self.LimitOrder(self.call.Symbol, -quantity, (self.call.AskPrice * 1.1)) # take profit at 10%
        self.StopMarketOrder(self.call.Symbol, -quantity, (self.call.AskPrice * 0.95)) # cut losses at 5%

    def BuyPut(self, chains): # buy an ATM put (market order need to change to limit)
        expiry = sorted(chains, key = lambda x: x.Expiry)[0].Expiry # get the closest expiration date
        puts = [i for i in chains if i.Expiry == expiry and i.Right == OptionRight.Put] # filter out only put options
        put_contracts = sorted(puts, key = lambda x: abs(x.Strike - x.UnderlyingLastPrice)) # sort contracts by closest to the money
        
        if len(put_contracts) == 0:
            return
        
        self.put = put_contracts[0] # contract with closest strike to current price (ATM)
        quantity = self.Portfolio.TotalPortfolioValue / self.put.AskPrice 
        quantity = int(0.05 * quantity / 100) # invest 5% of portfolio in option
    
        self.Buy(self.put.Symbol, quantity) # buy the contract
        self.LimitOrder(self.put.Symbol, -quantity, (self.put.AskPrice * 1.1)) # take profit at 10%
        self.StopMarketOrder(self.put.Symbol, -quantity, (self.put.AskPrice * 0.95)) # cut losses at 5%

    def OnOrderEvent(self, orderEvent):
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        # Cancel remaining order if limit order or stop loss order is executed
        if order.Status == OrderStatus.Filled:
            if order.Type == OrderType.Limit or OrderType.StopMarket:
                self.Transactions.CancelOpenOrders(order.Symbol)
                
            if order.Status == OrderStatus.Canceled:
                self.Log(str(orderEvent))
        
        # Liquidate before options are exercised
        if order.Type == OrderType.OptionExercise:
            self.Liquidate()

    def ExitPositions(self):
        self.Liquidate() # exit all positions
        for i in range(len(self.stocks)):
            self.previous_price[i] = 0
            self.current_price[i] = 0