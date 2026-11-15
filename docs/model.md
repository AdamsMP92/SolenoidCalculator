# Scientific model

This document is the repository-native basis for the online documentation.
It summarizes the 2023 *Versuch 38* derivation and the model implemented by
the legacy MATLAB app.

## Scope and assumptions

The coil is represented as a cylindrical annulus with inner radius `r1`,
outer radius `r2`, and axial height `h`. The macroscopic current density is
homogeneous in the coil cross-section and points in the azimuthal direction.
The model assumes vacuum permeability and low-frequency behaviour.

It does not resolve individual conductors in the magnetic-field calculation.
Skin effect, proximity effect, parasitic capacitance, leads, and magnetic
materials are not included.

The current density has units A/m^2. A unit of A/m^3 stated in the old note is
dimensionally inconsistent and is not used by the implementation.

## Discrete winding geometry

For conductor radius `r` and coating thickness `c`, the centre-to-centre wire
pitch is

```text
p = 2 (r + c).
```

Only complete turns inside the requested envelope are retained:

```text
N_rho = floor((r2_requested - r1) / p)
N_z   = floor(h_requested / p)
N     = N_rho N_z.
```

The continuum magnetic model uses the effective occupied dimensions

```text
r2_effective = r1 + p N_rho
h_effective  = p N_z.
```

Unlike the MATLAB interface, the Python model preserves both requested and
effective values instead of overwriting the inputs.

## Macroscopic current density

The discrete winding current is mapped to the uniform continuum density

```text
J = N I / ((r2 - r1) h).
```

This source is inserted directly into the magnetostatic Maxwell equations or,
equivalently, into the Biot-Savart integral. The implementation does not rely
on introducing an H field or on assuming a global relation
`B = mu0 (H + M)`.

## Axial magnetic flux density

On the symmetry axis the Biot-Savart integral reduces to

```text
B_z(z) = mu0 J / 2 [F(z + h/2) - F(z - h/2)],
F(a)   = a log((r2 + sqrt(r2^2 + a^2))
                 / (r1 + sqrt(r1^2 + a^2))).
```

At the centre this agrees with the independent expression

```text
B_z(0) = mu0 N I / (2 (r2 - r1))
         log((2 r2 + sqrt(h^2 + 4 r2^2))
             / (2 r1 + sqrt(h^2 + 4 r1^2))).
```

## DC self-inductance L0

Use the unitary Fourier convention

```text
F_tilde(q) = (2 pi)^(-3/2) integral_R3
  F(r) exp(-i q dot r) d^3r.
```

Parseval's identity and the magnetic energy then give the real- and
reciprocal-space route

```text
Em = 1/2 L0 I^2
   = 1/(2 mu0) integral_R3 |B(r)|^2 d^3r
   = 1/(2 mu0) integral_R3 |B_tilde(q)|^2 d^3q.
```

For `q > 0`, the magnetostatic Maxwell equations give

```text
B_tilde(q) = i mu0 (q cross J_tilde(q)) / q^2.
```

The Fourier transform of the homogeneous azimuthal current density separates
into axial, radial, and angular form factors:

```text
J_tilde(q) = -i 2 pi J h / (2 pi)^(3/2)
  j0(qz h/2) R1(q_rho) e_phi_q,

e_phi_q = (-sin(phi_q), cos(phi_q), 0)^T,

R1(q_rho) = q_rho/6
  [rho^3 1F2(3/2; 2, 5/2; -(q_rho rho)^2/4)]_(r1)^(r2).
```

Insert these form factors into the energy, use
`J = N I / ((r2 - r1) h)`, carry out the angular and axial integrations, and
set `alpha = h q_rho` and `nu_i = r_i/h`. Without displaying the intermediate
integral algebra, this reduction yields

```text
L0 = mu0 pi N^2 h^3 / (18 (r2 - r1)^2) G(r1/h, r2/h),
```

where

```text
Phi(alpha, nu) = nu^3 1F2(3/2; 2, 5/2; -(alpha nu)^2/4),

G(nu1, nu2) = integral_0^infinity
  (alpha - 1 + exp(-alpha))
  (Phi(alpha, nu2) - Phi(alpha, nu1))^2
  d alpha.
```

For numerical stability, the implementation evaluates the hypergeometric
difference through an equivalent Bessel integral. The improper integral is
accumulated in finite tail segments and returns explicit convergence
diagnostics.

## Wire length and DC ohmic resistance R0

For the simple-cubic winding model,

```text
length = 2 pi N (r1 + N_rho (r + c)),
R0     = length / (conductivity pi r^2).
```

The optional frequency is used only for the ideal series impedance

```text
Z0 = R0 + j omega L0,  omega = 2 pi f.
```
