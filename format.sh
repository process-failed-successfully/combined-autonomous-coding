#!/bin/bash
sed -i 's/typing.Optional//' shared/ulid_lab.py
sed -i 's/import sys/import sys\n/' shared/ulid_lab.py
sed -i 's/def run_ulid_lab_logic/def run_ulid_lab_logic/' shared/ulid_lab.py
