# TI PLM (Phase Light Modulator)

Easy TI PLM data formatting and phase processing in Python.

This library provides utilities designed to make it easy to work with TI PLM technology. It addresses challenges associated with:

* PLM device parameters (resolution, phase displacements, bit layout, etc.)
* Formatting phase data correctly for different TI PLM devices (quantization, bit packing, data flip, etc.)
* Displaying CGHs on PLM EVMs over external video (HDMI, DP)

## Installation

It is recommended to use a clean Python environment for working with this library using `conda`, `venv`, etc. This avoid potential dependency clashes with other installed libraries.

You can install `ti-plm` from this repo by cloning/downloading it and running `pip install .` from the project directory. This will also install all dependencies.

By default only core dependencies are installed. If you want to use the `display` module to render images/holograms on external monitors, there are a few additional dependencies that need to be installed, including `pygame`, `screeninfo`, and `pillow`. This can be done automatically by specifying the `display` pip install option: `pip install ".[display]"`

## Usage

See [examples](./examples/) and [tests](./tests/) for usage examples.

## CLI

A simple CLI is included in this library that wraps the `display` module to enable image display from the command line. After installing the library with `display` dependencies, you can run `ti_plm display <path/to/image>` on your command line to render images fullscreen on an external monitor. For full usage information, run `ti_plm display --help`.
