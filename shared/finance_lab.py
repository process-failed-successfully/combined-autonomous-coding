import sys
from typing import List


class FinanceLabManager:
    """Manages Finance Lab operations: financial calculations."""

    def calculate_loan_payment(self, principal: float, annual_rate: float, term_years: int) -> str:
        """Calculates monthly loan payment (Amortization)."""
        if principal <= 0 or annual_rate < 0 or term_years <= 0:
            return "Error: Principal and term must be positive, rate must be non-negative."

        monthly_rate = (annual_rate / 100) / 12
        num_payments = term_years * 12

        if monthly_rate == 0:
            monthly_payment = principal / num_payments
        else:
            monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)

        total_payment = monthly_payment * num_payments
        total_interest = total_payment - principal

        return (
            f"Loan Summary:\n"
            f"  Principal:      ${principal:,.2f}\n"
            f"  Annual Rate:    {annual_rate}%\n"
            f"  Term:           {term_years} years\n"
            f"  Monthly Payment: ${monthly_payment:,.2f}\n"
            f"  Total Payment:  ${total_payment:,.2f}\n"
            f"  Total Interest: ${total_interest:,.2f}"
        )

    def calculate_compound_interest(self, principal: float, annual_rate: float, time_years: int, frequency: int) -> str:
        """Calculates compound interest."""
        if principal < 0 or annual_rate < 0 or time_years < 0 or frequency <= 0:
            return "Error: Inputs must be non-negative, frequency must be positive."

        rate_decimal = annual_rate / 100
        amount = principal * (1 + rate_decimal / frequency) ** (frequency * time_years)
        interest = amount - principal

        freq_map = {1: "Annually", 12: "Monthly", 4: "Quarterly", 365: "Daily"}
        freq_str = freq_map.get(frequency, f"{frequency} times/year")

        return (
            f"Compound Interest Summary:\n"
            f"  Principal:      ${principal:,.2f}\n"
            f"  Annual Rate:    {annual_rate}%\n"
            f"  Time:           {time_years} years\n"
            f"  Frequency:      {freq_str}\n"
            f"  Future Value:   ${amount:,.2f}\n"
            f"  Total Interest: ${interest:,.2f}"
        )

    def calculate_npv(self, rate: float, cash_flows: List[float]) -> str:
        """Calculates Net Present Value (NPV)."""
        if rate < 0:
            return "Error: Discount rate must be non-negative."

        rate_decimal = rate / 100
        npv = 0.0
        for i, flow in enumerate(cash_flows):
            npv += flow / ((1 + rate_decimal) ** i)

        return (
            f"NPV Analysis:\n"
            f"  Discount Rate:  {rate}%\n"
            f"  Cash Flows:     {cash_flows}\n"
            f"  Net Present Value: ${npv:,.2f}"
        )

    def calculate_roi(self, initial_investment: float, final_value: float) -> str:
        """Calculates Return on Investment (ROI)."""
        if initial_investment == 0:
            return "Error: Initial investment cannot be zero."

        roi = ((final_value - initial_investment) / initial_investment) * 100
        profit = final_value - initial_investment

        return (
            f"ROI Analysis:\n"
            f"  Initial Investment: ${initial_investment:,.2f}\n"
            f"  Final Value:        ${final_value:,.2f}\n"
            f"  Net Profit/Loss:    ${profit:,.2f}\n"
            f"  ROI:                {roi:.2f}%"
        )

    def calculate_break_even(self, fixed_costs: float, variable_cost_per_unit: float, price_per_unit: float) -> str:
        """Calculates Break-Even Point."""
        if price_per_unit <= variable_cost_per_unit:
            return "Error: Price per unit must be greater than variable cost per unit to break even."

        contribution_margin = price_per_unit - variable_cost_per_unit
        break_even_units = fixed_costs / contribution_margin
        break_even_revenue = break_even_units * price_per_unit

        return (
            f"Break-Even Analysis:\n"
            f"  Fixed Costs:    ${fixed_costs:,.2f}\n"
            f"  Variable Cost:  ${variable_cost_per_unit:,.2f}/unit\n"
            f"  Price:          ${price_per_unit:,.2f}/unit\n"
            f"  Break-Even Units:   {break_even_units:,.2f}\n"
            f"  Break-Even Revenue: ${break_even_revenue:,.2f}"
        )

    def calculate_inflation(self, initial_value: float, inflation_rate: float, years: int) -> str:
        """Calculates future value based on inflation."""
        if years < 0:
            return "Error: Years must be non-negative."

        rate_decimal = inflation_rate / 100
        future_value = initial_value * ((1 + rate_decimal) ** years)
        purchasing_power_loss = initial_value - (initial_value / ((1 + rate_decimal) ** years))

        return (
            f"Inflation Analysis:\n"
            f"  Initial Value:  ${initial_value:,.2f}\n"
            f"  Inflation Rate: {inflation_rate}%\n"
            f"  Time:           {years} years\n"
            f"  Future Cost:    ${future_value:,.2f} (to buy same goods)\n"
            f"  Purchasing Power Loss: ${purchasing_power_loss:,.2f}"
        )


def run_finance_lab_logic(args) -> bool:
    """CLI handler for Finance Lab."""
    manager = FinanceLabManager()

    if args.action == "loan":
        if args.principal is None or args.rate is None or args.term is None:
            print("Error: --principal, --rate, and --term are required for loan calculation.", file=sys.stderr)
            return False
        print(manager.calculate_loan_payment(args.principal, args.rate, args.term))

    elif args.action == "compound":
        if args.principal is None or args.rate is None or args.time is None:
            print("Error: --principal, --rate, and --time are required for compound interest.", file=sys.stderr)
            return False
        freq = args.frequency if args.frequency else 1
        print(manager.calculate_compound_interest(args.principal, args.rate, args.time, freq))

    elif args.action == "npv":
        if args.rate is None or args.flows is None:
            print("Error: --rate and --flows are required for NPV.", file=sys.stderr)
            return False
        try:
            flows = [float(x.strip()) for x in args.flows.split(",")]
        except ValueError:
            print("Error: --flows must be a comma-separated list of numbers.", file=sys.stderr)
            return False
        print(manager.calculate_npv(args.rate, flows))

    elif args.action == "roi":
        if args.initial is None or args.final is None:
            print("Error: --initial and --final are required for ROI.", file=sys.stderr)
            return False
        print(manager.calculate_roi(args.initial, args.final))

    elif args.action == "break-even":
        if args.fixed is None or args.variable is None or args.price is None:
            print("Error: --fixed, --variable, and --price are required for break-even analysis.", file=sys.stderr)
            return False
        print(manager.calculate_break_even(args.fixed, args.variable, args.price))

    elif args.action == "inflation":
        if args.value is None or args.rate is None or args.years is None:
            print("Error: --value, --rate, and --years are required for inflation calculation.", file=sys.stderr)
            return False
        print(manager.calculate_inflation(args.value, args.rate, args.years))

    return True
