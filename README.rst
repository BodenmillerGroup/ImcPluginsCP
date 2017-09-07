ImcPluginsCP
========================

ImcPluginsCP contains a selection of CellProfiler modules that facilitate
handling, processing as well as measurement of multiplexed data. It was primarily
written with imaging mass cytometry (IMC) data for a Ilastik based image segmentation workflow.
Many modules are slightly modified versions of CellProfiler modules (https://github.com/CellProfiler/CellProfiler).
 
The modules were tested with CellProfiler 2.2.0
 
For installation copy the folder to a local directry and modify the CellProfiler preferences to the plugin folder.
 
Note that some plugins (save_object_crops and saveimages_ilastik) directly depend on the TiffFile python library for writing out tiff images.
Please install the library on the CellProfiler associated python using:
'pip install tifffile'
 
## The modules
* ColorToGray bb: a slight modification of the 'ColorToGray' CP module to support up to 60 channels per image
* Crop bb: Crop a specified or random location from the image
* MaskToBinstack: allows to identify a main object in a mask and generate a stack of binary planes containing: 'is_maninobject', 'is_any_other_object', 'is_background'
* MeasureImageIntensityMultichannel: Allows to measure all the image planes of a multicolor image 
* MeasureObjectIntensityMultichannel: Allows to measure all the image planes of a multicolor image in objects 
* Rescale objects: Rescales object segmentation masks
* Save object crops: Crops object regions out of an image. One region per object.
* Save images ilastik: a helper module to save images in a way that ilastik 1.2.1 will recognize it as xyc image -> relies on the TIFFFILE library!
* Smooth Multichannel: allows to apply image filters to all stacks of a multichannel image
* Sumarize stack: converts a multichannel image into a single channel image by applying summarizing functions, e.g. sum of all channels 
* Transform binary: converts a boolean image to the 'distance to the border' between regions.
* Correct Spillover apply: applies spillover compensation on the images. Requires a spillover tiff image (flaot image with dimensions p*p (p=number of color channels). This can e.g. be calculated witht he R software CATALYST for mass cytometry data (https://bioconductor.org/packages/release/bioc/html/CATALYST.html)

Pleas read also the documetation within CellProfiler for more hints how to use these modules!
