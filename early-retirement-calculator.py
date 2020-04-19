import sys

current_retirement_savings = int(sys.argv[1])

annual_contribution = int(sys.argv[2])

annual_contribution_increase_rate = float(sys.argv[3])

#  NOTE: this is the growth rate you expect BEFORE retirement! In retirement, we switch to more conservative securities that only get inflation rate
market_growth_rate = float(sys.argv[4])
inflation_rate = float(sys.argv[5])

years_to_live = int(sys.argv[6])

desired_net_retirement_income_todays_dollars = int(sys.argv[7])

retirement_tax_rate = float(sys.argv[8])

gross_retirement_income_todays_dollars = desired_net_retirement_income_todays_dollars / (1.0 - retirement_tax_rate)

def calculate_balance_after_working_year(previous_balance, market_growth_rate, annual_contribution):
    return previous_balance * (1 + market_growth_rate) + annual_contribution

# To be conservative, we set growth rate in retirement to be inflation rate
growth_rate_in_retirement = inflation_rate





# TODO make this a nice math formula
# We assume:
# 1. This money is withdrawn at the start of the year, with the Nth entry being how much you'd need if you were to retire RIGHT NOW
# 2. The amount you'd withdraw to last you this year doesn't have inflation applied (it will only increase the amount of next year)
# E.g. if I have 2 years to live, this array will look like [gross_retirement_income * (1 + inflation), gross_retirement_income]
money_needed_per_last_x_year_of_life = []
for last_x_year_of_life in range(0, years_to_live):
    # We subract one year from the exponentiation because inflation will only kick in one year from now
    money_needed_per_last_x_year_of_life.append( gross_retirement_income_todays_dollars * (1.0 + inflation_rate) ** (years_to_live - last_x_year_of_life - 1))

# This is a super stupid, but super clear, way to do this
bank_account_needed_per_last_x_year_of_life = []
for i, elem in enumerate(money_needed_per_last_x_year_of_life):
    if i == 0:
        bank_account_needed_per_last_x_year_of_life.append(elem)
    else:
        # Our bank account can be a little lower because we'll get in-year growth
        remaining_balance_needed = bank_account_needed_per_last_x_year_of_life[i - 1] / (1 + growth_rate_in_retirement)
        bank_account_needed_per_last_x_year_of_life.append(elem + remaining_balance_needed)

# Assumes you constantly contribute and grow forever
bank_account = []
for i in range(0, years_to_live):
    value_to_append = None
    if i == 0:
        value_to_append = current_retirement_savings
    else:
        # Growth from your balance, and then add your annual contribution afterwards (this is conservative)
            value_to_append = calculate_balance_after_working_year(
                bank_account[i - 1],
                market_growth_rate,
                annual_contribution * (1 + annual_contribution_increase_rate) ** (i - 1)
            )
    bank_account.append(value_to_append)

# Flip so we can now talk about years-from-now
bank_account_needed_if_retiring_in_x_years = bank_account_needed_per_last_x_year_of_life[::-1]
retirement_withdrawal_in_x_years = money_needed_per_last_x_year_of_life[::-1]

years_to_retirement = None
for i in range(0, years_to_live):
    if bank_account[i] >= bank_account_needed_if_retiring_in_x_years[i]:
        years_to_retirement = i
        break

if years_to_retirement is None:
    print("You can't retire with the current parameters!")
    sys.exit()
else:
    print("Years to retirement: %s" % years_to_retirement)

# Because we're a little cautious in that we'll only say you can retire when your bank account is >= the amount you'd need for the rest of your life, re-calculate to get exact values of your bank account after you retire
final_bank_account = []
withdrawal = [] # At start of year
for i in range(0, years_to_live):
    account_value = None
    withdrawal_value = None
    if i == 0:
        account_value = bank_account[0]
        if i >= years_to_retirement:
            withdrawal_value = retirement_withdrawal_in_x_years[i]
        else:
            withdrawal_value = 0
    else:
        last_year_value = final_bank_account[i - 1]
        if i < years_to_retirement:
            account_value = calculate_balance_after_working_year(
                last_year_value,
                market_growth_rate,
                annual_contribution * (1 + annual_contribution_increase_rate) ** (i - 1)
            )
            withdrawal_value = 0
        elif i == years_to_retirement:
            account_value = calculate_balance_after_working_year(
                last_year_value,
                market_growth_rate,
                annual_contribution * (1 + annual_contribution_increase_rate) ** (i - 1)
            )
            withdrawal_value = retirement_withdrawal_in_x_years[i]
        else:
            # To be conservative, we assume you take out your retirement income at the start of the year (i.e. no growth on it)
            last_year_withdrawal = retirement_withdrawal_in_x_years[i - 1]
            account_value = (last_year_value - last_year_withdrawal) * (1 + growth_rate_in_retirement)
            withdrawal_value = retirement_withdrawal_in_x_years[i]
    final_bank_account.append(account_value)
    withdrawal.append(withdrawal_value)

print("years_from_now bank_statement withdrawal")
print("NOTE: withdrawal is taken out at the start of the year, i.e. immediately after the bank_statement")
for i in range(0, years_to_live):
    print("%s %s %s" % (i, int(final_bank_account[i]), int(withdrawal[i])))


"""
print("<Years From Now> <Bank Account> <Retirement Withdrawal")
for i in range(0, len(money_needed_per_last_x_year_of_life)):
    print('%s,%s,%s,%s' % (i, bank_account[i], bank_account_needed_if_retiring_in_x_years[i], retirement_withdrawal_in_x_years[i]))
"""
