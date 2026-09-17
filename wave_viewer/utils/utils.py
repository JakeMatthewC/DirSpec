import numpy as np

from utils.directional import mem as _mem


def reconstrust_directional_spectrum(alpha1, alpha2, r1, r2, directions_deg,
                                     method="mem"):
    """
    Reconstruct normalized directional spreading D(theta) from Fourier parameters.

    alpha1, alpha2 : meteorological directions in degrees (direction FROM,
                     clockwise from true north), as stored in
                     dirspec.spectra_parameters
    r1, r2         : normalised Fourier coefficients in 0-1
    directions_deg : meteorological direction bins; the returned D is aligned to
                     these bins, so they can be plotted directly as bearings

    Uses the Maximum Entropy Method (Lygre & Krogstad 1986) via
    utils/directional.py, which is vendored verbatim from the ingest pipeline so
    that an on-the-fly spectrum and a stored spectra_directional row for the same
    timestep are identical. Do not reimplement the maths here -- the two copies
    drifting apart is what produced the mirrored-spectrum bug.

    No met->math conversion happens anywhere: alpha and the theta grid are both
    meteorological. Converting one without the other mirrors D about the 135/315
    axis, so waves from the north render as waves from the west.

    Returns None when any parameter is missing (bins the buoy could not resolve,
    stored NULL) or when MEM is degenerate for this bin (r1 -> 1).
    """
    params = (alpha1, alpha2, r1, r2)
    if any(v is None for v in params):
        return None
    if not np.all(np.isfinite(np.asarray(params, dtype=float))):
        return None

    D = _mem(alpha1, alpha2, r1, r2, directions_deg)[0]
    if not np.all(np.isfinite(D)):
        return None
    return D


def met_to_math_dir(angle_deg):
    """Meteorological bearing (degrees) -> mathematical angle (radians).

    NOT used when reconstructing D: that is built on the meteorological grid
    directly. Applying this to alpha without also transforming the theta grid
    mirrors the spectrum about 135/315.
    """
    return np.deg2rad((270 - angle_deg) % 360)
