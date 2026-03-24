from shared.iban_lab import IbanManager

manager = IbanManager()
iban = "GB578ZRFMXMI6YBHQVIZL0"
bad_iban = iban[:-1] + ("0" if iban[-1] != "0" else "1")
print(manager.validate(bad_iban))
