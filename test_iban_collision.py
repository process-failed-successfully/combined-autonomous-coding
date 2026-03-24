from shared.iban_lab import IbanManager
manager = IbanManager()
collisions = 0
for i in range(1000):
    gb_iban = manager.generate("GB")
    bad_iban = gb_iban[:-1] + ("0" if gb_iban[-1] != "0" else "1")
    if manager.validate(bad_iban):
        print(f"Collision: {gb_iban} -> {bad_iban}")
        collisions += 1
print(f"Collisions: {collisions}")
