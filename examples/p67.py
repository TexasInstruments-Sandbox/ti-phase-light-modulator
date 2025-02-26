# Load 8-bit phase map from png file and convert to bitmap suitable for display on a .67 PLM

import pathlib
import numpy as np
from PIL import Image
from ti_phase_light_modulator import PLM

here = pathlib.Path(__file__).parent
out = here / 'out'

# Initialize PLM object pre-configured with .67 parameters
plm = PLM.from_db('p67')

# Read image file containing phase info encoded as 8-bit values and scale it between 0 and 2pi
img = Image.open(here / 'dlp_logo_8bit.png')
phase = np.asarray(img, dtype=float) / 255 * 2 * np.pi

# PIL loads images with channel in last dimension slot, but we need it in the first
# This only applies to RGB images (e.g. if separate phase patterns were encoded into each RGB channel)
if len(phase.shape) > 2:
    phase = np.moveaxis(phase, 2, 0)

# Process phase data into bitmap specific to the .67 PLM
# This handles all quantization to appropriate phase displacement levels and mapping to the correct 2x2 electrode locations
bmp = plm.process_phase_map(phase)

if len(bmp.shape) > 2:
    bmp = np.moveaxis(bmp, 0, 2)

# Save to output directory
Image.fromarray(bmp).save(out / 'dlp_logo_p67.png')
