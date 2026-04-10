import sys
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

class CurrencyLabManager:
    """Manages Currency Lab operations: fetching rates and converting."""

    # Static fallback rates (Base: USD)
    STATIC_RATES: Dict[str, float] = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "JPY": 151.0,
        "CAD": 1.36,
        "AUD": 1.52,
        "INR": 83.3,
        "CHF": 0.90,
        "CNY": 7.23,
        "NZD": 1.67,
        "MXN": 16.5,
        "BRL": 5.0,
        "ZAR": 18.8,
        "SEK": 10.6,
        "NOK": 10.8,
        "DKK": 6.8,
        "SGD": 1.35,
        "HKD": 7.8,
        "TRY": 32.0,
        "KRW": 1350.0,
    }

    API_URL = "https://open.er-api.com/v6/latest/USD"

    def __init__(self):
        self._rates: Optional[Dict[str, float]] = None
        self._last_update: Optional[str] = None
        self._using_fallback = False

    def _fetch_rates(self) -> None:
        """Fetches rates from the API or falls back to static rates."""
        if self._rates is not None:
            return  # Already fetched

        try:
            req = urllib.request.Request(self.API_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:  # nosec B310
                data = json.loads(response.read().decode('utf-8'))
                if data.get("result") == "success":
                    self._rates = data.get("rates", {})
                    self._last_update = data.get("time_last_update_utc", "Unknown")
                    self._using_fallback = False
                    return
        except Exception:
            pass # nosec B110 - intentional fallback to static rates on any network/parse error

        # Fallback
        self._rates = self.STATIC_RATES.copy()
        self._using_fallback = True
        self._last_update = "Static Fallback (Not Real-time)"

    def get_rates(self) -> Tuple[Dict[str, float], bool]:
        """Returns the dictionary of rates and a boolean indicating if it's a fallback."""
        self._fetch_rates()
        return self._rates or {}, self._using_fallback

    def convert(self, amount: float, from_cur: str, to_cur: str) -> str:
        """Converts an amount from one currency to another."""
        self._fetch_rates()
        rates = self._rates or {}

        from_cur = from_cur.upper().strip()
        to_cur = to_cur.upper().strip()

        if from_cur not in rates:
            return f"Error: Unknown currency '{from_cur}'."
        if to_cur not in rates:
            return f"Error: Unknown currency '{to_cur}'."

        if amount < 0:
            return "Error: Amount must be non-negative."

        # Convert to USD first, then to target
        from_rate = rates[from_cur]
        to_rate = rates[to_cur]

        usd_amount = amount / from_rate
        result = usd_amount * to_rate

        fallback_warning = " (WARNING: Using static fallback rates)" if self._using_fallback else ""

        return (
            f"Conversion Result:\n"
            f"  {amount:,.2f} {from_cur} = {result:,.2f} {to_cur}\n"
            f"  Rate: 1 {from_cur} = {to_rate/from_rate:.4f} {to_cur}\n"
            f"  Last Update: {self._last_update}{fallback_warning}"
        )

    def list_currencies(self) -> List[str]:
        """Lists all supported currencies."""
        self._fetch_rates()
        if self._rates:
            return sorted(list(self._rates.keys()))
        return []

def run_currency_lab_logic(args) -> bool:
    """CLI handler for Currency Lab."""
    manager = CurrencyLabManager()

    if args.list:
        currencies = manager.list_currencies()
        print("Supported Currencies:")
        import textwrap
        wrapped = textwrap.fill(", ".join(currencies), width=80)
        print(wrapped)
        return True

    if args.amount is not None and args.from_cur and args.to_cur:
        try:
            val = float(args.amount)
        except ValueError:
            print(f"Error: Invalid amount '{args.amount}'. Must be a number.", file=sys.stderr)
            return False

        result = manager.convert(val, args.from_cur, args.to_cur)
        if result.startswith("Error"):
            print(result, file=sys.stderr)
            return False

        print(result)
        return True

    print("Error: Must provide either --list, or --amount, --from-cur, and --to-cur.", file=sys.stderr)
    return False
