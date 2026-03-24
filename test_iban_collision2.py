from shared.iban_lab import IbanManager
manager = IbanManager()
collisions = 0
for i in range(1000):
    gb_iban = manager.generate("GB")
    checksum = int(gb_iban[2:4])
    bad_checksum = str((checksum + 1) % 97).zfill(2)
    bad_iban = gb_iban[:2] + bad_checksum + gb_iban[4:]
    if manager.validate(bad_iban):
        print(f"Collision: {gb_iban} -> {bad_iban}")
        collisions += 1
print(f"Collisions: {collisions}")
