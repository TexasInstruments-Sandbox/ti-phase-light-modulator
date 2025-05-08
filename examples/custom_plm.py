# Customize a PLM with measured displacement levels and export to json
# Then, load that json file and use it to process a phase map

import pathlib
import numpy as np
from ti_plm import PLM

here = pathlib.Path(__file__).parent  # change to `pathlib.Path('.')` if running in a notebook
out = here / 'out'
out.mkdir(exist_ok=True)

# hypothetical measured displacement levels (normalized)
measured_ratios = np.array([0.0, 0.01395, 0.02863, 0.05992, 0.07348, 0.082216, 0.18364, 0.23701, 0.316312, 0.38889, 0.40321, 0.51986, 0.5965, 0.68123, 0.89665, 1.0])

# use p67 params from database but replace displacement ratios with measured values
custom_plm = PLM.from_db('p67', displacement_ratios=measured_ratios)

# export custom json
with open(out / 'custom_p67.json', 'w') as fp:
    fp.write(custom_plm.param.serialize_parameters())

# load custom json file but overwrite name with custom string
with open(out / 'custom_p67.json') as fp:
    params = PLM.param.deserialize_parameters(fp.read())
    params['name'] = 'Custom p67'

# init new PLM object with parameters loaded from json file
plm = PLM(**params)
print(plm)
print(plm.displacement_ratios)

# use plm object for phase map processing...
phase_map = np.random.random(plm.shape) * 2 * np.pi
bmp = plm.process_phase_map(phase_map)

print('phase map shape:', phase_map.shape)
print('bmp shape:', bmp.shape)
