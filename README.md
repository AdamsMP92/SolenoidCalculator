# Solenoid Calculator

A tested Python implementation for estimating the winding geometry, DC
resistance, DC inductance, ideal series impedance, and axial magnetic flux
density of a thick cylindrical solenoid.

The numerical model is based on a homogeneous azimuthal current density in
the rectangular coil cross-section and a simple-cubic winding model. The
calculation core is deliberately independent of the future web interface.

## Development

The project uses [Pixi](https://pixi.sh/) for a reproducible environment:

```bash
pixi install
pixi run test
pixi run lint
pixi run typecheck
```

A minimal API example:

```python
from solenoid_calculator import SolenoidInputs, calculate

inputs = SolenoidInputs.from_millimetres(
    wire_radius_mm=0.5,
    coating_thickness_mm=0.1,
    conductivity_s_per_m=56e6,
    inner_radius_mm=11.0,
    outer_radius_mm=18.2,
    height_mm=48.0,
    current_a=1.0,
    frequency_hz=50.0,
)
result = calculate(inputs)
print(result.inductance_h, result.resistance_ohm)
```

## Documentation

- [Scientific model](docs/model.md)
- [Reference cases](docs/reference-cases.md)
- [Implementation decisions](docs/implementation-notes.md)

## Scope

The impedance is currently the ideal low-frequency series model
`Z = R + i 2 pi f L`. Skin effect, proximity effect, parasitic capacitance,
lead resistance, and magnetic materials are outside the present model.
