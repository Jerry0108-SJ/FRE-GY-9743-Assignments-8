# FRE-GY-9743-Assignments-2026fall
Assignments for NYU, FRE-GY 9743, Fall 2026.

Assignment 8: open `hw8_sofr_ois_calibration_and_risk.ipynb`.
This is the student version with five TODO blocks, using the supplied SOFR OIS quotes
dated 2026-10-09. Excel quotes are in bp and are converted to decimal rates.
SOFR is calibrated only to OIS instruments. Funding uses the template's
zero-spread data, held at zero; the notebook displays only OIS quote risk.

Use Python 3.11, install `requirements.txt`, and start Jupyter from the repository
root. The notebook covers reading decimal market rates, calibrating SOFR,
reporting OIS quote risk, and constructing a first-order OIS hedge. Complete the
TODOs listed at the start of the notebook, then restart the kernel and run all
cells. Until they are completed, the relevant calls raise `NotImplementedError`.

The library follows the instructor's instrument factory, bootstrap calibration
with piecewise constant forward rates and flat extrapolation, and analytic
state-to-quote risk transformation. These calculations are accessed through
the notebook's API calls.
The supplied `USD-SOFR-OIS` convention is unchanged. Funding and the solver
are configured through `YieldCurveBuildMethodCommon` and a `DataGeneric`
funding table. The model has one funding node and 17 SOFR nodes.
`risk_calculation()` converts state risk to quote risk; `risk_postprocess()`
only attaches market-data labels. Use the template's annuity and par-rate
formulas; this assignment uses nonzero fixed coupons.
Original API names and signatures are retained. RFR swap valuation also uses
TODOs 2a and 2b when the curve is built from direct IFR inputs.
