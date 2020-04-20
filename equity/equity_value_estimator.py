class EquityValueEstimator:
    """
        A value estimator that takes into account a hypothetical share price and capital gains tax rate.
        The estimating method total_value allows you to define the date at which you leave the company,
        so that vesting stops on those grants.
    """
    
    def __init__(self, grants, share_price, capital_gains):
        self.grants = grants
        self.share_price = share_price
        self.capital_gains = capital_gains
        
    def total_value(self, date_of_leaving, pay_execution_fee=True, pay_capital_gains=True):
        val = 0
        for grant in self.grants:
            value_per_share = max(self.share_price - grant.strike_price, 0)
            total_value = grant.get_shares_vested(date_of_leaving) * value_per_share
            if (pay_execution_fee):
                val += total_value * (1 - grant.execution_fee)
            else:
                val += total_value
        if (pay_capital_gains):
            return val * (1 - self.capital_gains)
        else:
            return val