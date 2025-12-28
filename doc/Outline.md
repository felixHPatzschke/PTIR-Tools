# PTIR Tools Library

## Requirements

We want a python library to handle PTIR data. It should include classes to store data associated with any kind of measingful acquisition mode. Since, in the \*.ptir files, datasets are always stored as individual measurements, we need to first define a couple of ways measurements can "belong together" and then implement a way to recognize that they actually _do_ belong together. If they do, they should be packaged into a new object that can handle the data in a reasonable way.

### Source Measurement Types

The following fundamental measurement types exist:
- `OPTIRSpectrum`: OPTIR Spectra are a kind of IR absorption spectra. They are defined over some spectral domain and contain, for each point in that domain, a value of some kind. 
- `OPTIRImage`: OPTIR Images are scanned micrographs, mapping each point on an _xy_ grid to some kind of value. 
- `CameraImage`: A micrograph recorded with a normal camera, in greyscale.
- `FluorescenceImage`: A fluorescence micrograph, also recorded on a normal camera.
- `FLPTIRImage`: A difference micrograph between fluorescence signals with IR on and off. 

### Relationships between OPTIR Measurements

In general, measurements may be related by being different data channels recorded at the same time. **Relevant Channels** for OPTIR measurements are...

- `O-PTIR`: The amplitude of the demodulated signal. This channel should always be included. Unit is (usually) millivolts but this is an error on the manufacturer's side. After corrections applied as part of the acquisition routine, it should be unitless. 
- `Phase`: The phase of the demodulated signal. This channel _should_ exist but cannot be guaranteed to. If it does, then it is convenient to immediately package it together with the O-PTIR channel as a complex-valued spectrum. $\left( Z = \text{OPTIR} \cdot \exp\left( \mathfrak{i} \cdot \text{Phase} \right) \right)$ Unit is degrees, but should be converted to radians at earliest convenience in the evaluation pipeline. 
- `DC`: The non-oscillating part of the recorded voltage. Usually included but not always. It is unclear whether this channel is needed for normalization or not, so it's a good idea to at least keep track of it. By itself, the DC channel does not contain data that is interesting for our purposes, in a quantitative way, but it may be used to identify a location of interest. DC data is always real-valued, but for convenience we may have to store it as complex-valued data with zero imaginary part. Unit is volts. (which is correct in this case)
- `X`, `Y`: The real and imaginary parts of the lock-in amplifier output. These data contain the same information as the O-PTIR and Phase channels, just in a different representation. If these channels are present, they can be used to reconstruct or validate the O-PTIR and Phase channels.
- `O-PTIR 2nd Harmonic`: Usually not present. Contains data equivalent to the O-PTIR channel, but demodulated at twice the base modulation frequency.

(These apply to OPTIRSpectra, OPTIRImages and Hyperspectral Images)

Among each other, **OPTIRSpectra** may additionally be related in the following ways:

- Part of an **Array Acquisition** (there are different types of array acuisition modes defined by the PTIR Studio software)
  - **Line Scan:** A series of spectra recorded at points along a line. Such sets of spectra should be recognizable by their spatial coordinates, which should all lie on a line in the _xy_ plane and be spaced equally. (Obviously, some margin of error needs to be included to account for inaccurate positioning and floating point errors.) Such datasets should get their own class (e.g. OPTIRLineProfile) where data is stored in a 2D array (position along line $\times$ wavenumber).
  - **Hyperspectral Scans** (but stored as individual spectra in the HDF5 file): A series of spectra recorded at points on a 2D grid. (for recognition, margin of error is still needed) Such data should have a class that is either the same as or easily converted to a purpose-built class for Hyperspectral Images, where data is stored in a 3D array (_y_ position $\times$ _x_ position $\times$ wavenumber). (-> later)
  - **Point Cloud:** A series of spectra recorded at arbitrary points in space. Their positions do not have to lie on a line or a grid, but are usually in close proximity to one another. (-> clustering analysis for recognition?) Here, the data should be stored in a 2D array (point index $\times$ wavenumber) along with a list of the spatial coordinates of each point. For plotting, each point should have a polygon associated with it, derived from a voronoi tesselation of the point cloud.

**OPTIRImages** always contain data recorded in an XY grid and at a fixed wavenumber. OPTIRImages may have to be organized into the following higher-level structures:

- **z Stacks:** A series of images recorded over the same area in _xy_, but at different _z_ heights (Top Focus). While the _x_ and _y_ coordinates will already form a nice grid, the _z_ focus values may be a bit noisy, due to the imperfect positioning of the objective. The true _z_ focus values should be stored, but for displaying, it will usually be fine to assume equally spaced _z_ positions. 
- **Spectral Image Stacks:** A series of images recorded at the same z position and over the same _xy_ area, but at different wavenumbers. In terms of dimensions, these are equivalent to Hyperspectral images, just recorded by scanning position and then wavenumber, not the other way around. Wavenumbers are not generally evenly spaced. 
- **Power Scans:** Series of images recorded at the same xy position and wavenumber, but at different laser powers. These are less common, but may be useful for certain types of analysis. (Never used before, not a priority to implement)

Importantly, these higher-level structures may be combined. So, we might have a dataset where both z focus and wavenumber are varied. In that case, we would have a 4D dataset (_y_ $\times$ _x_ $\times$ _z_ $\times$ wavenumber). There should be an abstract implementation to recognize and handle any combination of these relationships. It would be convenient in this case to keep track of what kind of parameter each dimension / array axis corresponds to. I.e. we should know that _x,y,z_ are spatial coordinates and wavenumber is not, so that, in default plots, we know to make _xy_-, _xz_- and _yz_-slices, but not a slice that's mixed between spatial and non-spatial dimensions. Also, we would like to collapse/accumulate the dataset ove certain axes, e.g. correlation with a certain test spectrum. Also for this, we need to know what each axis corresponds to. 

### Camera Images
Some standard micrographs are recorded with a normal camera. These are mainly used for orientation, to identify/select a point/region to spectrally analyze and to document the sample. These measurements have types `CameraImage` and `FluorescenceImage`. For Fluorescence images, each available filter constitutes a channel. Otherwise matching Fluorescence images may be combined into an RGB composite. Not a priority to implement handling for these right now.

### FLPTIR Images
FLPTIR is a wide field mode of acquisition of IR absorption data at a microscopic scale, using the fact that fluorescence is attenuated by heat. Of a fluorescent sample, fluorescence micrographs are recorded sequentially, with the IR laser at a constant wave number alternating between on and off. The difference between consecutive images will show where heating through absorption weakened the fluorescence intensity. Measurements are accumulated over a few cycles to improve signal-to-noise. 

The stored datasets contain pairs of images, one giving the average fluorescence intensity, the other giving the correlation of fluorescence intensity and IR state. This somewhat corresponds to a zeroth-order harmonic (DC) and first-order harmonic (OPTIR). However, OPTIR and FLPTIR are quantitatively different and these signals should not be confused for one another. 

Within each such pair of images, the IR wavenumber is fixed, but, in the storage format, FLPTIR images may be grouped into (sparse) hyperspectral datasets, i.e. one for each probed wavenumber. 

### Metadata
Certain kinds of metadata have some kind of structure and should therefore be handled by dedicated classes. This includes in particular...

- **Spectroscopic Domains:** These define the wavenumber axis for spectra and spectral image stacks. They may be non-uniformly spaced and have missing regions. A dedicated class should be able to generate the actual wavenumber axis as needed.
- **Spatial Positions:** There are three independently moving components in the setup. The sample is translated using an xy stage. The objectives above and below can be independently translated in z. Whether the bottom focus is relevant at all depends on the measurement configuration. Separate Classes should store and manage `StagePosition` (_x_,_y_) and `FocusPosition` (top focus (usually interpreted as z in the end), bottom focus)
- **Spatial Domains:** While spectra are recorded in a specific point, images are recorded over an area. A dedicated class should be able to store and manage the spatial domain of images. Here, we may assume that image data is always recorded on a regular grid in x and y with no missing points. The class should only store the necessary metadata to reconstruct the spatial axes as needed.
- **Configuration:** The optical path may be changed by switching mirrors, objectives, etc.. Most importantly, we make the distinction between...
  - Copropagation / Counterpropagation: In Copropagation, both pump and probe beams are directed onto the sample through the top objective. In Counterpropagation, the pump beam is directed onto the sample through the bottom objective, while the probe beam comes from above.
  - Transmission / Reflection: In Transmission mode, the probe beam is collected by the bottom objective after passing through the sample. In Reflection mode, the probe beam is collected by the top objective after being reflected off the sample surface.

All metadata classes should be hashable and comparable for equality, so that we can easily identify measurements that share the same metadata and sort measurements by domains for example. 

As for the configuration, there should be one master class, `MeasurementConfiguration`, that _may_ store all configuration parameters but also works if only some of them are defined. Two configurations should be considered equal if all parameters that are defined in both configurations are equal. This way, we can easily group measurements by configuration even if not all configuration parameters are recorded for all measurements. The configuration class should also provide a way to generate human-readable descriptions of the configuration, e.g. for plot titles and legends. Member classes may be implemented if convenient. 

### Backgrounds

Some measurements link to a background or calibration measurement. OPTIR and FLPTIR measurements require different manners of background / calibration measurements. 

### Other Tools

The library should include basic tools for data analysis and handling. In no particular order, I'd like to include...

- **A library of materials and IR absorption / vibrational modes.**
- **Decomposition tools:** A function to decompose any dataset with a spectral domain into contributions from model spectra plus a residual. Different methods could be applied for that, e.g. multi-Gaussian fitting, NNLS, or PCA/SVD. Note that our datasets are generally complex-valued and `sklearn.decomposition.pca` and `.nmf` do not support complex-valued input.
- **Plotting helper functions,** e.g. to map complex-valued data to a colour space so that the amplitude corresponds to the brightness (somehow) and the phase corresponds to the hue. 
- **Logging:** Something will go wrong (e.g. measurement IDs may turn out to _not_ be unique) so I'd like to have a record of that. 
- **File I/O:** Besides reading in \*.ptir files, we should be able to export objects from our library, such as high-dimensional datasets, to a file and read them back in at a later point in time. These files wouldn't need to match the \*.ptir format. Instead their format should be tailored to seamless operation with the toolkit that we're developing here. Here, it would be important to ensure forward compatibility. 

## PTIR File Format
> Here, I include my notes from reverse engineering the \*.ptir file format as reference information to help build the library.

The device in the lab spits out \*.ptir files. Fundamentally, these are HDF5 files with a specific internal structure. The top-level groups are:

- `MEASUREMENTS`
- `BACKGROUNDS`
- `TREE`
- `VIEW`

We are mainly concerned with the `MEASUREMENTS` group, which contains the measured data. 

### Measurements

Within `MEASUREMENTS`, there is an arbitrary number of subgroups, each containing one "measurement". 

The key / identifier of each measurement group is an alphanumeric string that _appears to be_ a UUID. For example, one is `144de06d-52bb-47cb-9e96-6110b62010ab` and all I saw thusfar have the format `<4 byte hex>-<2 byte hex>-<2 byte hex>-<2 byte hex>-<6 byte hex>`. The identifier does not contain any quantitative data (as far as I can tell). It is, at this time, unclear, whether these identifiers _actually are_ UUIDs. We also do not know whether they are unique across different files. (I would, for the moment, work under these assumptions, but code should contain checks.)

A measurement group may contain the following subgroups:

- `DATA`: Always present. Contains the raw measured data values in an array of _some_ shape. The shape is dependent on the measurement type and the domain, of course. 
- `Channel`: Contains information about which exact data channel's data were stored into this measurement group. Included in most cases, but not always. For OPTIR measurements, the channel refers to the Lock-In Amplifier's output channels. For Fluorescence Images, it refers to the filter used. For `CameraImage` type measurements, the Channel subgroup is not present.
- `ParticleData`: Included for measurements of type `OPTIRSpectrum`. It is, at this time, unclear what data is supposed to be stored in this subgroup. We can disregard it for now.

Furthermore, a measurement group carries attributes. The `TYPE` attribute should always be present. It contains a string type identifier for the type of measurement that the group contains. Measurement types I have discovered thusfar are the following:

- `OPTIRSpectrum`
- `OPTIRImage`
- `FluorescenceImage`
- `CameraImage`
- `FLPTIRImage`

The other attributes contain metadata about the measurement, such as positioning data, a timestamp, environmental parameters (temperature, humidity) information about the OPTIR configuration and so on. A breakdown of all attributes of a measurement group is given in `PTIR Measurement Attributes.md`. Not all attributes are present in all measurement groups. 

#### Channel Attributes

The `Channel` subgroups in a measurement group identifies which signal channel is stored in the measurement. All these metadata are stored as attributes of the `Channel` sugroup. 

The `DataSignal` attribute is always present and of a string type. In the case of OPTIR measurements, it identifies the Lock-in Amplifier output (translating to DC/OPTIR/X/Y). In the case of Fluorescence measurements, identifies the filter used (translating to R/G/B colour channels). 

The following attributes have also been encountered: 

- `Color`: string-type. contains a 4-byte colour hex code.
- `CorrectBackground`: type unclear but maps to bool
- `CorrectBaseline`: type unclear but maps to bool
- `CorrectGain`: type unclear but maps to bool
- `CorrectPower`: type unclear but maps to bool
- `Label`: string-type. always present. Just a label for displaying.
- `LineType`: string-type. interpretation unclear
- `Offset`: array\[1\] of float. interpretation unclear
- `Scale`: array\[1\] of float. interpretation unclear
- `SigDigits`: array\[1\] of int (?). number of significant digits (?). interpretation unclear
- `Units`: string-type. Identifies the unit of the data. This may be important for handling phase information. This is usually correctly tagged as being in units of degrees. We should explicitly check this field though, just in case. However, the units for some other channels are sometimes inconsistent: Signal amplitudes are often assigned units of voltage (V or mV), but depending on the corrections modes done or not done, it should be unitless in some cases.

### Regarding string encoding

I have described metadata fields multiple times as "string-type". String-type data and attributes may be encoded in a few different ways in the \*.ptir files. Here is a decoding routine that I wrote for inspection purposes:

```python
def as_string(value) -> str:
    if isinstance(value, np.ndarray):
        shape = value.shape
        if len(shape) == 1 and value.dtype.kind == "S":
            ### intercept fixed-width byte strings
            return ''.join(value.astype('<U1').tolist())
        elif len(shape) == 1 and shape[0] < 5:
            ### intercept short 1D arrays and output by value
            return f"[ {', '.join([str(v) for v in value])} ]"
        else:
            ### for larger arrays, output the shape
            return f"np.array[{','.join([ str(x) for x in value.shape])}]"
    elif isinstance(value, str):
        return f"\"{value}\""
    elif isinstance(value, np.bytes_):
        return value.decode('UTF-8')
    else:
        #return f"{type(value)}: {value}"
        return f"{type(value)}"
```

It works reasonably well, as far as I can tell, but it was meant as a subroutine for generating an overview of the data format. As such, it is supposed to turn any value into a string that tells me what the field means. Since numeric data is almost exclusively stored in some array-like data structure, it also generates a string representation of those (just the shape if the array is too big). The relevant checks for string decoding are the following:

- type is `np.ndarray`, number of axes is `1` and `value.dtype.kind == "S"`: Fixed/width byte strings
- type is `np.bytes_`: UTF-8 encoded string
- type is `str`: self-explanatory

Non-ASCII characters are included in some cases and should be displayed appropriately. 

If we ever want to implement re-exporting data as \*.ptir files, we need to keep track of which field was encoded in which way.

## Implementation Plan

Here, we sketch out what we expect users to want to do and how these functionalities could be implemented. 

### De-Serializing PTIR files

Everything starts with the paths of one or more \*.ptir files. In order to just accumulate measurements into working memory, there shall be a function or class constructor to call with these paths as argument(s). The user shall receive an object (primitive iterable or custom class?) containing all measurements.

> Should it be a function returning a primitive iterable (tuple/list/dict) or a constructor returning an object of a custom class, purpose-built to handle these data?
> How should the measurements be ordered? Adressed by key/UUID? Grouped by type? Sorted by timestamp? ...?

### Storing Measurements in Base Classes

When accumulating measurements from HDF5 files, we can immediately read the `TYPE` attribute of each measurement group to determine what kind of measurement it is. Based on that, we can instantiate the appropriate base class for each measurement: We define...

- `OPTIRSpectrum`: For single-point O-PTIR spectra 
- `OPTIRImage`: For single O-PTIR images 
- … others that aren’t a priority right now

Of course, all data and attributes in the measurement groups should be kept track of. In the following, I discuss the most important ones or ones that may warrant special treatment.

#### Spectra

- Position 
	- _x_ and _y_: in the `PositionX` and `PositionY` attributes 
	- _z_: use the `TopFocus` attribute. Whether the `BottomFocus` attribute is relevant at all depends on the measurement configuration. It should be kept track of, but it only matters in relation the the top focus, if at all. 
- Spectroscopic Domain: Relevant Attributes are `XStart`, `XIncrement` and `WavenumberOffset`. The number of points is given by the size of the dataset itself. Not that not all wavenumbers have a valid data point associated with them. A NaN value indicates that no data was recorded at the respective wavenumber because the QCL has no emission in that part of the spectrum. To effectively handle all kinds of quirks with spectroscopic domains (e.g. non-uniform spacing, missing regions, etc.), Spectroscopic Domains should be handled by a dedicated class that can generate the actual wavenumber axis as needed. This can then be re-used for image stacks assembled over a spectroscopic domain. 
- Channel: The description of which data signal was stored in a particular measurement is given in the `Channel` subgroup’s `DataSignal` attribute. A dictionary to translate these strings into meaningful channel identifiers is given in `CHANNEL_TRANSLATION`.

#### Images

As metadata for images, we must store:

- Spatial Domain: The spatial domain of images should be handled by a dedicated class that can generate the spatial axes as needed.
- Wavenumber: The wavenumber at which the image was recorded is given in the `Wavenumber` attribute.
- Configuration

### Grouping of Channels

Next thing we can do immediately is to combine measurements that belong together as different channels of the same measurement. The following criteria can be used to identify measurements that belong together: 

- Same `TYPE` 
- Same spatial position or "compatible" domain (depending on which one applies to the given `TYPE`. Margin of error should not be needed here I guess.) 
- Same acquisition time (within a small margin of error to account for time taken to store data) 
- Different data channels 
- Same configuration

> At what point does a configuration attribute become a parameter that could have a domain associated with it?

Based on these criteria, we can group measurements together into objects of new classes that can handle multiple channels. But first we must decide on rules how to handle any combination of available channels. This will be important for later, when combining possibly partially mismatched measurements into higher-dimensional datasets.

We group the channels by their harmonic order. The main relevant channels, `O-PTIR`, `Phase`, `X` and `Y` belong to the first order. The `O-PTIR 2nd Harmonic` channel belongs to the second order. `DC` constitutes the zeroth order. Refer to the following table:

|                  | Amplitude / Magnitude | Phase                | Real Part        | Imaginary Part   |
| ---------------- | --------------------- | -------------------- | ---------------- | ---------------- |
| **zeroth order** | `DC`                  | -                    | -                | -                |
| **first order**  | `O-PTIR`              | `Phase`              | `X`              | `Y`              |
| **second order** | `O-PTIR 2nd Harmonic` | -                    | -                | -                |

(other channels filling the free spots or even higher order harmonics may be implemented in the future.)

For each basic measurement type (i.e `OPTIRSpectrum` and `OPTIRImage` for now), we define an associated multi-channel class (`OPTIRMultiChannelSpectrum` and `OPTIRMultiChannelImage`) that can store representations of any combination of harmonic orders. For calculating the representation of each harmonic order, the apply the following rules:

- If a pair of channels that can be combined into a complex-valued representation is present (O-PTIR + Phase or X + Y), then do so and store only the complex-valued data. 
- If both pairs are present, calculate both complex-valued representations. Store the mean of both as the main data and the deviation between both as an uncertainty estimate. (But delete the uncertainty estimate if it’s so small that it’s negligible?) 
- If not enough channels are present to form a complex-valued representation, distinguish further:
    - If an amplitude channel is present (`DC`, `O-PTIR` or `O-PTIR 2nd Harmonic`), store that as real-valued main data. 
    - Otherwise, discard the harmonic order entirely, since phase or X/Y data without amplitude is not meaningful.

Then, the multi channel classes should (a) include metadata to keep track of which harmonic orders are available and in what form (complex or amplitude only) and (b) provide methods to access the data in a convenient way.

It might actually make sense to implement the multi-channel classes first, and then define the single-channel "base" classes as special cases of these, where only one channel is present. This should avoid code duplication.

> Note, that non-zero-order harmonic signals should generally be normalized against the corresponding zeroth-order harmonic signal if one is to derive quantitative statements from the measurement. For OPTIR, it is currently unclear if this is done during acquisition or remains to be done in analysis. For FLPTIR, it is not done in acquisition. Also note that this normalization affects signal-to-noise.

### Recognition of Higher-Level Structures

Up until this point, the structuring of data could be done automatically, directly upon reading the HDF5 files. The next step is to recognize and accumulate higher-level datasets. This step should be invoked manually by the user, since it may require some tuning of parameters (e.g. margin of error for spatial positions). The user should also be be able to pass any Iterable of abstract measurement objects to the relevant function(s), so that they can pre-select according to their requirements. 

Usage could look a little something like this:

```python
hyperspectrals = ptir.find_stacks(ALL_IMAGES, stack_by=["wavenumber"], invalid="mask")
# or
hyperspectral_z_stacks = ptir.find_stacks(ALL_IMAGES, stack_by=["wavenumber", "z"], invalid="NaN")
# or
line_profiles = ptir.find_line_profiles(ALL_SPECTRA)
```

In the following, we outline how the recognition and accumulation of higher-level datasets could be done for spectra and images.

#### Image Stacks

As noted earlier, images may stack into arbitrary parameter spaces. Handling the parameter dimensions sequientially may incur the issue that certain stacks may be incompatible, even though they have subsets that would produce valid and interesting datasets. Consider the following example:

> We have a set of images recorded in the same xy region. We sampled the z focus at 1300µm, 1310µm, ... up until 1400µm. For each z focus, we recorded images at wavenumbers 1377cm⁻¹, 1470cm⁻¹ and 1733cm⁻¹. However, due to an error, the images at z focus 1350µm and wavenumbers 1470cm⁻¹ and 1733cm⁻¹ are missing. If we accumulate over z focus first, then the three resulting stacks (one for each wavenumber) would be incompatible. If we accumulate over wavenumber first, the same issue would arise for the stacks at z focus 1350µm. 

Of course, we cannot magically recover missing data. While it is possible to determine the accumulation order that maximizes the size of the resulting valid dataset, this may not be what the user needs. Therefore, we should provide ways for the user to (a) specify which parameters to accumulate over and in what order and (b) specify how to handle missing data. It may be necessary to discard sections of the dataset that are incomplete, but some analyses may still be possible with parts of the dataset marked as invalid (e.g. correlation with a test spectrum over only the valid parts). In these cases it may be more convenient to fill invalid sections with NaN or to store a mask alongside the data as in a `numpy.ma.masked_array`.

#### Spectra Line Profiles

...

#### Spectra Arrays

...

#### Spectra Point Clouds

...

### Filtering

Assuming we have some big object containing all measurements, we need a flexible way to select only those that we are interested in for some manner of analysis. 
