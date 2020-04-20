import sys
import argparse
from retirement_age_calculator import RetirementAgeCalculator, Series

try:
    import tabulate
    have_tabulate = True
except ImportError:
    have_tabulate = False

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
post_retirement_growth_rate = parsed_args[POST_GROWTH_RATE_KEY]
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
        print("ERROR: Two contrib changes defined with the same year '%s'" % years_out)
        sys.exit(1)
    if years_out < 0 or years_out >= years_to_live:
        print("ERROR: Invalid contrib change year '%s'; must be between [0,%s)" % years_out, years_to_live)
        sys.exit(1)
    contrib_changes[years_out] = (contrib, contrib_rate)

# =============== Main Code ====================================
retirement_calculator = RetirementAgeCalculator(
            current_retirement_savings,
            annual_contribution,
            annual_contribution_increase_rate,
            pre_retirement_growth_rate,
            post_retirement_growth_rate,
            inflation_rate,
            years_to_live,
            desired_net_retirement_income_todays_dollars,
            retirement_tax_rate,
            manual_contrib_changes=contrib_changes,
            manual_net_worth_changes=net_worth_changes)

years_to_retirement = retirement_calculator.get_earliest_retirement()
if years_to_retirement is None:
    print("You can't retire with the current parameters!")
    sys.exit(1)
else:
    print(" ===> YEARS TO RETIREMENT: %s <===" % years_to_retirement)

# Double-check the user hasn't added any networth changes AFTER retirement, as we don't handle these
for key in net_worth_changes.keys():
    if key > years_to_retirement:
        print("ERROR: You've set a net worth change that happens AFTER projected retirement - this script currently can't handle this")
        sys.exit(1)
for key in contrib_changes.keys():
    if key >= years_to_retirement:
        print("WARN: You've set a contribution change that happens on or after projected retirement - this will be ignored")

serieses = [
    retirement_calculator.get_series_data(Series.ACCOUNT_VALUE),
    retirement_calculator.get_series_data(Series.ACTUAL_WITHDRAWALS),
    retirement_calculator.get_series_data(Series.ALL_WITHDRAWALS),
    retirement_calculator.get_series_data(Series.MIN_RETIREMENT_WORTH),
    retirement_calculator.get_series_data(Series.NO_RETIREMENT),
    retirement_calculator.get_series_data(Series.CONTRIBUTIONS),
]


print("NOTE: withdrawal is taken out at the start of the year, i.e. immediately after the bank_statement")
headers = [
    "years",
    "acct",
    "withdrw",
    "all_wd",
    "minimum",
    "noretir",
    "contrib",
]

if have_tabulate:
    data = []
    for i in range(0, years_to_live):
        data.append([str(i)] + ['{:,}'.format(int(series[i])) for series in serieses])
    print(tabulate.tabulate(data, headers=headers, tablefmt='presto'))
else:
    print("   ".join(headers))
    for i in range(0, years_to_live):
        row = [str(i)] + [str(int(series[i])) for series in serieses]
        print("   ".join(row))
    print("INFO: tabulate module was not found so resorting to ugly tables; do 'pip install tabulate' to get prettier tables")
