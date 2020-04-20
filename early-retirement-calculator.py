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
desired_net_retirement_income_todays_dollars = parsed_args[NET_RETIREMENT_INCOME_KEY]
retirement_tax_rate = parsed_args[RETIREMENT_TAX_RATE_KEY]

net_worth_changes = { int(years_out): int(change) for years_out, change in parsed_args[NET_WORTH_CHANGE_KEY] }
contrib_changes = { int(years_out): (int(contrib), float(contrib_rate)) for years_out, contrib, contrib_rate in parsed_args[CONTRIB_CHANGE_KEY] }
# TODO use this^^^


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
            annual_contribution * (1 + annual_contribution_increase_rate) ** (i - 1)
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

print("years_from_now bank_statement needed withdrawal")
print("NOTE: withdrawal is taken out at the start of the year, i.e. immediately after the bank_statement")
for i in range(0, years_to_live):
    print("%s %s %s %s" % (i, int(final_bank_account[i]), int(bank_account_needed_if_retiring_in_x_years[i]), int(withdrawal[i])))
