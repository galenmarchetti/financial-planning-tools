import sys
import argparse

# ========================== Arg Parsing ===========================================================

CURRENT_SAVINGS_KEY = 'current_savings'
ANNUAL_CONTRIB_KEY = 'annual_contribution'
ANNUAL_CONTRIB_INCREASE_RATE_KEY = 'annual_contrib_increase_rate'
PRE_GROWTH_RATE_KEY = 'pre_growth_rate'
POST_GROWTH_RATE_KEY = 'post_growth_rate'
INFLATION_RATE_KEY = 'inflation_rate'
YEARS_TO_LIVE_KEY = 'years_to_live'
NET_RETIREMENT_INCOME_KEY = 'net_retirement_income'
RETIREMENT_TAX_RATE_KEY = 'retirement_tax_rate'

NET_WORTH_CHANGE_KEY = 'net_worth_change'
CONTRIB_CHANGE_KEY = 'contrib_change'

parser = argparse.ArgumentParser(description='Calculate when to retire.')
parser.add_argument(CURRENT_SAVINGS_KEY, type=int, help='Current retirement savings right now, in dollars')
parser.add_argument(ANNUAL_CONTRIB_KEY, type=int, help='Annual contribution, in dollars')
parser.add_argument(ANNUAL_CONTRIB_INCREASE_RATE_KEY, type=float, help='Annual contribution, in dollars')
parser.add_argument(PRE_GROWTH_RATE_KEY, type=float, help='Market growth rate before retirement, in the form 0.XX')
parser.add_argument(POST_GROWTH_RATE_KEY, type=float, help='Market growth rate during retirement, in the form 0.XX')
parser.add_argument(INFLATION_RATE_KEY, type=float, help='Inflation rate, in the form 0.XX')
parser.add_argument(YEARS_TO_LIVE_KEY, type=int, help='Planned years to live')
parser.add_argument(NET_RETIREMENT_INCOME_KEY, type=int, help='Desired net income in retirement, in dollars')
parser.add_argument(RETIREMENT_TAX_RATE_KEY, type=float, help='Estimated tax rate in retirement, in the form 0.XX')
parser.add_argument('-w', '--change-worth', dest=NET_WORTH_CHANGE_KEY, action='append', nargs=2, metavar=('years_out','value'), default=[], help='Indicates a one-time change in net worth in X years of Y value, applied immediately at the start of the year (before withdrawals, before any market growth)')
parser.add_argument('-c', '--change-contrib', dest=CONTRIB_CHANGE_KEY, action='append', nargs=3, metavar=('years_out','contrib', 'contrib_rate'), default=[], help='In X years in the future, sets the annual contrib value and increase rate going forward')
parsed_args = vars(parser.parse_args())

current_retirement_savings = parsed_args[CURRENT_SAVINGS_KEY]
annual_contribution = parsed_args[ANNUAL_CONTRIB_KEY]
annual_contribution_increase_rate = parsed_args[ANNUAL_CONTRIB_INCREASE_RATE_KEY]

#  NOTE: this is the growth rate you expect BEFORE retirement! In retirement, we switch to more conservative securities that only get inflation rate
pre_retirement_growth_rate = parsed_args[PRE_GROWTH_RATE_KEY]
growth_rate_in_retirement = parsed_args[POST_GROWTH_RATE_KEY]
inflation_rate = parsed_args[INFLATION_RATE_KEY]

years_to_live = parsed_args[YEARS_TO_LIVE_KEY]
if years_to_live < 1:
    print("ERROR: Invalid years to live; are you expecting to die today??")
    sys.exit(1)

desired_net_retirement_income_todays_dollars = parsed_args[NET_RETIREMENT_INCOME_KEY]
retirement_tax_rate = parsed_args[RETIREMENT_TAX_RATE_KEY]

# Validate no duplicates, for sanity
net_worth_changes = {}
for years_out_str, change_str in parsed_args[NET_WORTH_CHANGE_KEY]:
    years_out = int(years_out_str)
    change = int(change_str)
    if years_out in net_worth_changes:
        print("ERROR: Two net worth changes defined with the same year '%s'" % years_out)
        sys.exit(1)
    if years_out < 0 or years_out >= years_to_live:
        print("ERROR: Invalid net worth change year '%s'; must be between [0,%s)" % years_out, years_to_live)
        sys.exit(1)
    net_worth_changes[years_out] = change

contrib_changes = {}
for years_out_str, contrib_str, contrib_rate_str in parsed_args[CONTRIB_CHANGE_KEY]:
    years_out = int(years_out_str)
    contrib = int(contrib_str)
    contrib_rate = float(contrib_rate_str)
    if years_out in contrib_changes:
        print("ERROR: Two net worth changes defined with the same year '%s'" % years_out)
        sys.exit(1)
    if years_out < 0 or years_out >= years_to_live:
        print("ERROR: Invalid contrib change year '%s'; must be between [0,%s)" % years_out, years_to_live)
        sys.exit(1)
    contrib_changes[years_out] = (contrib, contrib_rate)

class ContributionCalculator:
    """
    Class that returns the yearly contribution amount for any given year in the future,
     taking into account contrib increases and changes.
    """
    def __init__(self, manual_contrib_changes, initial_contrib_amount, initial_contrib_rate):
        self.contribs = []
        current_base_contrib = initial_contrib_amount
        current_contrib_rate = initial_contrib_rate
        years_since_last_change = 0
        for i in range(0, years_to_live):
            if i in manual_contrib_changes:
                current_base_contrib, current_contrib_rate = manual_contrib_changes[i]
                years_since_last_change = 0
            self.contribs.append(current_base_contrib * (1 + current_contrib_rate) ** years_since_last_change)
            years_since_last_change = years_since_last_change + 1
        print(self.contribs)

    def get_contrib_for_year(self, years_in_future):
        return self.contribs[years_in_future]

# =============== Main Code ====================================


gross_retirement_income_todays_dollars = desired_net_retirement_income_todays_dollars / (1.0 - retirement_tax_rate)

def calculate_balance_after_working_year(previous_balance, pre_retirement_growth_rate, annual_contribution):
    return previous_balance * (1 + pre_retirement_growth_rate) + annual_contribution


# TODO make this a nice math formula
# We assume:
# 1. This money is withdrawn at the start of the year, with the 0th entry being how much you'd need if you were to retire RIGHT NOW
# 2. The amount you'd withdraw to last you this year doesn't have inflation applied (it will only increase the amount of next year)
# E.g. if I have 2 years to live, this array will look like [gross_retirement_income, gross_retirement_income * (1 + inflation)]
retirement_withdrawal_in_x_years = []
for i in range(0, years_to_live):
    # We subract one year from the exponentiation because inflation will only kick in one year from now
    retirement_withdrawal_in_x_years.append(gross_retirement_income_todays_dollars * (1.0 + inflation_rate) ** i)

# This is a super stupid, but super clear, way to do this
bank_account_needed_for_last_x_year = []
for i, elem in enumerate(reversed(retirement_withdrawal_in_x_years)):
    value_to_append = None
    if i == 0:
        value_to_append = elem
    else:
        # Our bank account can be a little lower because we'll get in-year growth
        remaining_balance_needed = bank_account_needed_for_last_x_year[i - 1] / (1 + growth_rate_in_retirement)
        value_to_append = elem + remaining_balance_needed
    bank_account_needed_for_last_x_year.append(value_to_append)

# Necessary to reverse so this makes sense
bank_account_needed_if_retiring_in_x_years = list(reversed(bank_account_needed_for_last_x_year))

# Assumes you constantly contribute and grow forever
contrib_calculator = ContributionCalculator(contrib_changes, annual_contribution, annual_contribution_increase_rate)
no_retirement_bank_account = []
for i in range(0, years_to_live):
    value_to_append = None
    if i == 0:
        value_to_append = current_retirement_savings
    else:
        # Growth from your balance, and then add your annual contribution afterwards (this is conservative)
        value_to_append = calculate_balance_after_working_year(
            no_retirement_bank_account[i - 1],
            pre_retirement_growth_rate,
            contrib_calculator.get_contrib_for_year(i)
        )
    value_with_net_worth_change = max(0, value_to_append + net_worth_changes.get(i, 0))
    no_retirement_bank_account.append(value_with_net_worth_change)

years_to_retirement = None
for i in range(0, years_to_live):
    if no_retirement_bank_account[i] >= bank_account_needed_if_retiring_in_x_years[i]:
        years_to_retirement = i
        break

if years_to_retirement is None:
    print("You can't retire with the current parameters!")
    sys.exit(1)
else:
    print("Years to retirement: %s" % years_to_retirement)

# TODO actually handle this (it's complex)
# Double-check the user hasn't added any networth changes AFTER retirement, as we don't handle these
for key in net_worth_changes.keys():
    if key > years_to_retirement:
        print("ERROR: You've set a net worth change that happens AFTER projected retirement - this script currently can't handle this")
        sys.exit(1)

# Because we're a little cautious in that we'll only say you can retire when your bank account is >= the amount you'd need for the rest of your life, re-calculate to get exact values of your bank account after you retire
# TODO this entire chunk is a bunch of spaghetti code; refactor it
final_bank_account = []
withdrawal = []
for i in range(0, years_to_live):
    account_value = None
    withdrawal_value = None
    if i == 0:
        account_value = no_retirement_bank_account[0]
        if i >= years_to_retirement:
            withdrawal_value = retirement_withdrawal_in_x_years[i]
        else:
            withdrawal_value = 0
    # Up to and including first retirement year
    elif i <= years_to_retirement:
        account_value = no_retirement_bank_account[i]

        # Before retirement
        if i < years_to_retirement:
            withdrawal_value = 0
        # First retirement year
        else:
            withdrawal_value = retirement_withdrawal_in_x_years[i]
    # After first retirement year
    else:
        # To be conservative, we assume you take out your retirement income at the start of the year (i.e. no market growth on it)
        last_year_value = final_bank_account[i - 1]
        last_year_withdrawal = retirement_withdrawal_in_x_years[i - 1]
        account_value = max(
            0,
            (last_year_value - last_year_withdrawal) * (1 + growth_rate_in_retirement)
        )
        withdrawal_value = retirement_withdrawal_in_x_years[i]
    final_bank_account.append(account_value)
    withdrawal.append(withdrawal_value)

print("years_from_now bank_statement retirement_limit withdrawal")
print("NOTE: withdrawal is taken out at the start of the year, i.e. immediately after the bank_statement")
for i in range(0, years_to_live):
    print("%s %s %s %s" % (i, int(final_bank_account[i]), int(bank_account_needed_if_retiring_in_x_years[i]), int(withdrawal[i])))
