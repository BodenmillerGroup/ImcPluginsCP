.. image:: https://zenodo.org/badge/69028464.svg
   :target: https://zenodo.org/badge/latestdoi/69028464

ImcPluginsCP
========================

This repository contains CellProfiler plugins developed to facilitate working with highly multiplexed images
(>40 channels).

When produced through Imaging Mass Cytometry, these images are 'intrinsically' aligned, e.g. pixels across all color planes
come from the same measurement and could affect each other (e.g. channel crosstalk). To represent this, we prefer
to work with mutlichannel image instead of working with individual planes (similar to 3D images that are also not
analyzed plane-by-plane but as a stack). This modules help Cellprofiler to better work with such stacks.

Their main use have been the associated multiplexed image segmentation pipeline (https://github.com/BodenmillerGroup/ImcSegmentationPipeline)
and projects using this workflow.

Changelog:
------------
- 2020-11-20: Fixes a bug in CorrectSpilloverMeasurements introduced by the
    CP3 -> CP4 transition that caused the the name suffix to be appended
    to the image instead of the measurement name.

- 2020-11-18: ExportVarCsv now also adds column metadata for the Image table.

- 2020-11-13: Adds new ExportVarCsv module
    This module parses measurement names from output tables into a
    clean metadata file that should facilitate the import of cellprofiler
    output into anndata.

- 2020-10-30:
    The modules have been updated to work with *CellProfiler 4* instead of *CellProfiler 3 or 2*!
    The CP2 and CP3 modules are still available at the branch:
    - https://github.com/BodenmillerGroup/ImcPluginsCP/tree/master-cp2
    - https://github.com/BodenmillerGroup/ImcPluginsCP/tree/master-cp3

    Several modules have been deprecated or changed names. Please read the 'deprecation' notes displayed when
    loading these modules to see if and how you need to adapt your pipeline.

General Information
-------------------
ImcPluginsCP contains a selection of CellProfiler modules that facilitate
handling, processing as well as measurement of multiplexed data. It was primarily
written with imaging mass cytometry (IMC) data for a Ilastik based image segmentation workflow.
Many modules are slightly modified versions of CellProfiler modules (https://github.com/CellProfiler/CellProfiler).
 
The modules were tested with CellProfiler 4.
 
For installation copy the folder to a local directory,
modify the CellProfiler `Preferences` in the GUI to the plugin folder (`PATHTO/ImcPluginsCP/plugins`) and **restart** cellprofiler.

For command line usage use the command line flag:  `--plugins-directory=PATHTO/ImcPluginsCP/plugins`

The modules
-------------------

Measurement modules:

* MeasureObjectIntensityMultichannel:
    Allows to measure all the image planes of a multicolor image with an object
    by applying 'MeasureObjectIntensity' to each plane.
    The number of planes in the stack needs to be known and indicated beforehand.
    The name of the measurements will have a suffix `_c{channelnr}` where channelnr is 1 based index of the plane.

* MeasureImageIntensityMultichannel:
    Allows to measure all the image planes of a multicolor image by applying 'MeasureImageIntensity' to each plane.
    The number of planes in the stack needs to be known and indicated beforehand.
    The name of the measurements will have a suffix `_c{channelnr}` where channelnr is 1 based index of the plane.

* ExportVarCsv:
    Exports a CSV containing metadata for measurements akin to the .var table
    in anndata objects: https://anndata.readthedocs.io/en/latest/anndata.AnnData.html
    This should greatly facilitate the conversion of cellprofiler output to
    anndata objects.

Image processing modules:

* Smooth Multichannel:
    allows to apply image filters to all stacks of a multichannel image
    Very similar to the normal *Smooth* module.
    Additionally provides filters:

    - "Remove single hot pixels" (good for single, strong outliers)

    - "Median Filter Scipy": Fixes a bug of the normal Median filter when small footprints are used.

* ClipRange:
    Clips the maximum of an image by setting all values higher than an user defined percentile to the value of said percentile.
    This is useful if an image has rare but strong outliers.

* SummarizeStack:
    Converts an image with multiple channels to a greyscale image by averaging/summing/... over the pixel values.

* StackImages:
    Takes multiple grayscale or color images and stacks them to a new multichannel image.

* CropImage:
    Allows cropping of sections of images with defined size.
    Cropping coordinates can be chosen manually (e.g. also from Metadata) or randomly.
    This modules allows to provide metadata fields (e.g. Filename) as random seeds to make the 'random'
    cropping reproducible.
    A common use case is to reduce image size for a machine learning dataset.
    This is very similar to the Cellprofiler module: Crop

* SaveObjectCrops: Crops object regions out of an image. One region per object.
    In order to process large images it can be beneficial to crop segmented regions of
    interest out. This module will crop out segmented images from an object masks.

    The crops will be saved using the provided naming scheme with the following suffix:
    '_l{ObjectNumber}_x{x coordinate of top left corner}_y{y coordinate of top left corner}'

    To save cropped object masks convert it first to an image using *ConvertObjectToImage*.

    This is similar to *SaveCroppedObjects* which will export full sized images where all pixels except the ones
    from the current objects are masked.

* MaskToBinstack:
    This module is thought for the use in combination cropped out masks that contain one main object.
    The main object id should be provided by metadata or manually. The module will
    then create a stack of 3 binary mask layers: the main object, other objects,
    background.

* Transform binary: Applies a distance transforms to a binary image.
    This modules allows you to apply distance transforms to the image.
    Converts a boolean image (or stack of boolean images) to the 'distance to the border' between regions.
    Negative values indicate that a pixel is inside the object, positive that it is outside.
    Helpful to quantify distance to segmented region borders (e.g. after identifying 'tumor' regions, this could be used
    to quantify the distance to the tumor border).


Spillover related modules:

* CorrectSpilloverApply:
    Applies an spillover matrix to a multichannel image to account for channel crosstalk (spillover)

    This module applies a previously calculate spillover matrix, loaded as a normal image.
    The spillover matrix is a float image with dimensions p*p (p=number of color channels).
    The diagonal is usually 1 and the off-diagonal values indicate what fraction of the main signal
    is detected in other channels.

    The order of the channels in the image and in the matrix need to match.

    For Imaging Mass Cytometry please check the example scripts in this repository how to generate such a matrix:
    https://github.com/BodenmillerGroup/cyTOFcompensation

    For more conceptual information, check our paper: https://doi.org/10.1016/j.cels.2018.02.010

    In general compensated images are mainly for visual purposes or to assess intensity distributions.
    If you do single cell MeanIntensity quantification, applying the compensation to *Measurements* is usually more accurate
    as pixels are more noisy than averaged intensities.
    Module: *CorrectSpilloverMeasurements*.

* CorrectSpilloverMeasurements:
    applies an spillover matrix to measurements multichannel image to account for channel crosstalk (spillover)

    This module applies a previously calculate spillover matrix, loaded as a normal image.
    The spillover matrix is a float image with dimensions p*p (p=number of color channels).
    The diagonal is usually 1 and the off-diagonal values indicate what fraction of the main signal
    is detected in other channels.

    The order of the channels in the measured image and in the matrix need to match.

    For Imaging Mass Cytometry please check the example scripts in this repository how to generate such a matrix:
    https://github.com/BodenmillerGroup/cyTOFcompensation

    For more conceptual information, check our paper: https://doi.org/10.1016/j.cels.2018.02.010

    Note that this compensation is only valid for measurements that perform identical operations of linear combinations of pixel values
    in all channels (e.g. MeanIntensity) but not others (e.g. MedianIntensity, MaxIntensity, StdIntensity...).
    For measurements where this applies, applying the compensation to *Measurements* is usually more accurate than compensating an image
    and then measuring.
    For measurements where this does not apply, please measure the image compensated with Module: *CorrectSpilloverApply*.


Pleas read also the documentation within CellProfiler for more hints how to use these modules!

Deprecated modules:
___________________
This will be removed in the next version of ImcPluginsCP.

* ColorToGray bb:
    a slight modification of the 'ColorToGray' CP module to support up to 60 channels per image
    -> Can be replaced by default *ColorToGray* module

* Rescale objects:
    Rescales object segmentation masks
    -> Can be replaced by the default *ResizeObjects* module

* Save images ilastik:
    a helper module to save images as `.tiff` in a way that ilastik 1.2.1 will recognize it as xyc image
    -> This will  is deprecated. I recommend to use the *saveimages_h5* module
    for this task and use `hdf5` instead of tiff

