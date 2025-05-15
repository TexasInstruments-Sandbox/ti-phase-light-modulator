# TI PLM (Phase Light Modulator)

Easy TI PLM data formatting and phase processing in Python.

This library provides utilities designed to make it easy to work with TI PLM technology. It addresses challenges associated with:

* PLM device parameters (resolution, phase displacements, bit layout, etc.) - See [PLM database](./src/ti_plm/db/)
* Formatting phase data correctly for different TI PLM devices (quantization, bit packing, data flip, etc.)
* Displaying CGHs on PLM EVMs over external video (HDMI, DP)

## Installation

Recommended: use `conda`, `venv`, `uv`, etc. to set up a dedicated Python environment to avoid dependency conflicts.

* `pip install ti-plm`
  * Core functionality only
* `pip install "ti-plm[display]"`
  * Installs optional dependencies needed by `display` module (pygame, screeninfo, pillow, etc.)

## Usage

This library provides a `PLM` class that keeps track of PLM device parameters and provides functions to process data in a way specific to that device. PLM functions support n-dimensional arrays by default, as long as the last 2 dimensions are rows, columns. This means you can easily and efficiently process phase data for RGB images (color channel being the outermost dimension), or time-series data (time being the outermost dimension).

```python
from ti_plm import PLM

# Typically PLM parameters will be loaded from the database
print(PLM.get_device_list())  # print a list of all available devices in the database
plm = PLM.from_db('p67')  # load p67 data from database into a new `plm` object

# Alternatively, PLM parameters can be specified manually
# See PLM class documentation for required parameters,
# or look at example json files in src/ti_plm/db
plm = PLM(
    name=...,
    shape=...,
    pitch=...,
    displacement_ratios=...,
    memory_lut=...,
    electrode_layout=...,
    data_flip=...
)

# Once the plm object is instantiated, you can use its class methods to process phase data
# This will take care of quantizing to appropriate displacement levels and mapping data to
# the electrode layout specific to this device. In this case phase_map would contain floating
# point phase data between 0 and 2pi
bmp = plm.process_phase_map(phase_map)

# This process can also be broken down into individual steps:
# 1. Quantize continuous phase data into buckets corresponding to available mirror levels
state_index = plm.quantize(phase_map)
# 2. Map state_index values to electrodes
bmp = plm.electrode_map(state_index)
# 3. Replicate bits across the full 8 bits of the bmp
bmp *= 255

# If phase_map data has additional dimensions for color channel or time-series, make sure the last
# 2 dimensions are rows, columns. See examples/p67.py for a demo of this.
```

See [examples](./examples/) and [tests](./tests/) for more usage examples.

## CLI

A simple CLI is included in this library that wraps the `display` module to enable image display from the command line. After installing the library with `display` dependencies, you can run `ti_plm display <path/to/image>` on your command line to render images fullscreen on an external monitor. For full usage information, run `ti_plm display --help`.
