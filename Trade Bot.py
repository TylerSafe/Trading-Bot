# - changed 4% at some point within the last 1.5 hours (high and low could be at any point within the last 1.5 hours)
# - Draw a line at 50% fibonacchi retracement (half way between low and high)
# - Draw a line at 61.8% fibonacchi retracement
# - Test using options, buying ATM calls/puts with expiries 7 - 14 days, taking profit at 5, 10, 15, 20, 25 and 50% profit
# - test 1: If price retraces to this band at some point during the day and touches vwap buy (vwap acts as support/resistance)
# - test 2: If price retraces to this band at some point during the day and is above/below vwap depending then buy
# - test 3: If price retraces to 50% fib at some point during the day buy, buy double if supported by vwap
# - also test selling once price returns back to vwap or at least setting the stop at vwap once it reaches
# - trailing stop 5%, 6%.... 10%
# - only buy once 
# - don't buy within last 2 hours of day
# - sell at eod (don't carry positions over night)
# - after a trade is made time out for 90 mins

class CreativeBrownViper(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2020, 1, 1)  # Set Start Date
        self.SetEndDate(2021, 1, 1) # Set End Date
        self.SetCash(100000)  # Set Strategy Cash
        self.amd = self.AddEquity("amd", Resolution.Minute).Symbol
        self.goog = self.AddEquity("goog", Resolution.Minute).Symbol
        self.AMD_VWAP = self.VWAP("AMD", 90)
        self.GOOG_VWAP = self.VWAP("GOOG", 90)
        
    def OnData(self, data: Slice):
        self.History([self.Symbol("AMD"), self.Symbol("GOOG")], 90, Resolution.Minute) # get the price each minute of the last 90 minutes
        
        
