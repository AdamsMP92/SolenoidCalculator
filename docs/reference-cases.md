# Reference cases

The machine-readable values are stored in
[`tests/data/reference_cases.json`](../tests/data/reference_cases.json).

## Legacy MATLAB defaults

The MATLAB App Designer implementation uses:

- wire radius: 0.5 mm
- coating thickness: 0.1 mm
- conductivity: 56 MS/m
- inner/outer radius: 11.0 mm / 18.2 mm
- requested height: 48.0 mm
- current: 1 A
- frequency: 50 Hz

This gives `N_rho = 6`, `N_z = 40`, `N = 240`, a wire-length estimate of
22.0162813164 m, and a DC resistance of 0.5005714286 ohm.

The frozen Python port baseline additionally gives:

- DC inductance: 0.6534096581 mH
- central axial flux density at 1 A: 5.3650734609 mT
- ideal impedance magnitude at 50 Hz: 0.5410262996 ohm

## Published Versuch 38 example

The additional 2023 reference note gives:

- wire radius: 0.11 mm
- coating thickness: 20% of the wire radius = 0.022 mm
- conductivity: 56 MS/m
- requested inner/outer radius: 2.5 mm / 11.6 mm
- requested height: 10 mm

The simple-cubic model produces `N_rho = 34`, `N_z = 37`, and `N = 1258`.
Its effective outer radius is 11.476 mm and effective height is 9.768 mm.
The published rounded outputs are:

- DC resistance: 25.94 ohm
- DC inductance: 10.97 mH

This case is the primary independent regression test for the numerical
inductance implementation. The Python result is 10.9734266890 mH and differs
from the rounded published value by approximately 0.03%.
