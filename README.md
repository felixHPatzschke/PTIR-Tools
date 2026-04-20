# ptirtools

A python library for Tools to handle and analyze **P**hoto**t**hermal **I**nfra**r**ed (PTIR) spectroscopy data.

## Usage

### Basic Setup

Import the module like so:

``` python
import ptirtools as ptir
```

### Reading a \*.ptir File

``` python
# initialize a container object
file = ptir.PTIRFile()
# load measurements from a file into the container object
file.safe_load(filename)
```

A `PTIRFile` object can hold the contents of arbitrarily many \*.ptir files.
Each measurement has a UUID and can be accessed using the index operator:

``` python
measurement = file[uuid]
```

### Selecting Measurements

To get the uuids for a desired selection of measurements, use the `separate_measurements_by_attributes` method:

```python
uuids_by_type = file.separate_measurements_by_attributes( file.all_measurements.keys(), "TYPE" )
```

`uuids_by_type` will contain a dictionary mapping the `TYPE` attributes of measurements to `set`s of uuids such that the measurements corresponding to the uuids in one `set` will all have that given `TYPE`. 

## Components

### Measurements

Measurements are the elementary dataset as it is understood by PTIRStudio. There are several types of measurements:

- `CameraImage`
- `FluorescenceImage`
- `FLPTIRImage`
- `FLPTIRImageStack`
- `OPTIRSpectrum`
- `OPTIRImage`
