# Solenoid Calculator

A tested Python implementation for estimating the winding geometry, DC ohmic
resistance `R0`, DC inductance `L0`, ideal series impedance `Z0`, and axial
magnetic flux density of a thick cylindrical solenoid.

The numerical model is based on a homogeneous azimuthal current density in
the rectangular coil cross-section and a simple-cubic winding model. The
calculation core is deliberately separated from the web interface.

## Development

The project uses [Pixi](https://pixi.sh/) for a reproducible environment:

```bash
pixi install
pixi run test
pixi run lint
pixi run typecheck
```

Run the local web interface with:

```bash
pixi run app
```

Then open `http://127.0.0.1:8000`. To create the static Shinylive bundle
used by GitHub Pages:

```bash
pixi run export-site
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

## Web deployment

The public interface is exported with Shinylive, so the same Python
calculation core runs locally in each visitor's browser. GitHub Actions
deploys pushes to `main` to GitHub Pages:

<https://adamsmp92.github.io/SolenoidCalculator/>

## Scope

The impedance is currently the ideal low-frequency series model
`Z0 = R0 + j omega L0`, with `omega = 2 pi f`. Skin effect, proximity effect,
parasitic capacitance, lead resistance, and magnetic materials are outside the
present model.
