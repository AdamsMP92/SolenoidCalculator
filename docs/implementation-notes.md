# Implementation decisions

## Deliberate differences from the MATLAB app

1. Requested and effective coil dimensions are both retained. The old app
   silently replaced the user's outer radius and height.
2. All inputs are validated before any division or numerical integration.
   A geometry must contain at least one radial and one axial turn.
3. The inductance convergence test uses the absolute tail contribution and a
   combined absolute/relative tolerance. The old callback tested the signed
   difference `dL < 1e-9`, while displaying `abs(dL)`.
4. The current density is documented in A/m^2, consistent with dimensional
   analysis.
5. Inductance is purely geometrical for vacuum and is calculated separately
   from the selected current and frequency.

## Numerical radial factor

SciPy does not need to evaluate the generalized hypergeometric function
directly. With

```text
A(u) = integral_0^u t J1(t) dt
     = integral_0^u J0(t) dt - u J0(u),
```

the radial factor can be written as

```text
F(alpha; nu1, nu2) = 6 / alpha^3
  (A(alpha nu2) - A(alpha nu1)).
```

A power series is used around zero to avoid cancellation; elsewhere SciPy's
Bessel integral implementation is used.
