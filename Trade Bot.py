class DeterminedYellowMonkey(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)  # Set Start Date
        self.SetStartDate(2022, 4, 4)
        self.SetCash(100000)  # Set Strategy Cash
        
        self.gme = self.AddEquity("GME", Resolution.Minute).Symbol
        
        self.entryTicket = None
        self.stopMarketTicket = None
        self.entryTime = datetime.min
        self.stopMarketOrderFillTime = datetime.min
        self.highestPrice = 0


    def OnData(self, data: Slice):
        if (self.Time - self.stopMarketOrderFillTime).days < 30: # wait 30 days after trade to buy again
            return
        
        price = self.Securities[self.gme].Price
        
        # send limit order if stock not owned and no other orders are waiting
        if not self.Portfolio.Invested and not self.Transactions.GetOpenOrders(self.gme):
            quantity = self.CalculateOrderQuantity(self.gme, 0.9) # allocates 90% of portfolio to stock
            self.entryTicket = self.LimitOrder(self.gme, quantity, price, "Entry Order") # place limit order
            self.entryTime = self.Time
            
        # move price if not filled after 1 day
        if (self.Time - self.entryTime).days > 1 and self.entryTicket.Status != OrderStatus.Filled:
            self.entryTime = self.Time
            updateFields = UpdateOrderFields()
            updateFields.LimitPrice = price
            self.entryTicket.Update(updateFields)
            
        # move up trailing stop loss
        if self.stopMarketTicket is not None and self.Portfolio.Invested:
            if price > self.highestPrice:
                self.highestPrice = price
                updateFields = UpdateOrderFields()
                updateFields.StopPrice = price * 0.95
                self.stopMarketTicket.Update(updateFields)
        
    def OnOrderEvent(self, orderEvent):
        if orderEvent.Status != OrderStatus.Filled:
            return
        
        # send stop loss order if entry limit order is filled
        if self.entryTicket is not None and self.entryTicket.OrderId == orderEvent.OrderId:
            self.stopMarketTicket = self.StopMarketOrder(self.gme, -self.entryTicket.Quantity, 0.95 * self.entryTicket.AverageFillPrice)
            
        # save fill time of stop loss order
        if self.stopMarketTicket is not None and self.stopMarketTicket.OrderId == orderEvent.OrderId:
            self.stopMarketORderFillTime = self.Time
            self.highestPrice = 0