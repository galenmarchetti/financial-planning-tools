from datetime import datetime
from dateutil import relativedelta as rd


class Grant:
    """
        Defines an equity grant with a constant number of shares vesting per month.
    """
    def __init__(self, total_shares, shares_per_month, end_date, strike_price, execution_fee=0):
        """
            total_shares is the total number of shares in the grant
            shares_per_month is the number of shares that vest per month
            end_date is a string in format YYYY-mm, for example '2020-04', representing when all shares are vested
            strike_price is the strike price of the options in the grant
            execution_fee is the predicted fee taken by a financial institution to assist you executing your options
        """
        self.total_shares = total_shares
        self.shares_per_month = shares_per_month
        self.end_date = datetime.strptime(end_date, '%Y-%m')
        self.strike_price = strike_price
        self.execution_fee = execution_fee
        
    def get_shares_remaining(self, at_date):
        at_date = datetime.strptime(at_date, '%Y-%m')
        delta = rd.relativedelta(self.end_date, at_date)
        months_left = max(delta.years * 12 + delta.months, 0)
        return (months_left * self.shares_per_month)
    
    def get_shares_vested(self, at_date):
        return self.total_shares - self.get_shares_remaining(at_date)
    
    def get_total_shares(self):
        return self.total_shares
    