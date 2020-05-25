.. image:: https://zenodo.org/badge/69028464.svg
   :target: https://zenodo.org/badge/latestdoi/69028464
ImcPluginsCP
========================
For a description of the associated image segmentation pipline, please visit: https://github.com/BodenmillerGroup/ImcSegmentationPipeline

Changenotes:
-----------
The modueles have been updated to work with *CellProfiler 3* instead of *CellProfiler 2*! The CP2 modules are still available at the branch: https://github.com/BodenmillerGroup/ImcPluginsCP/tree/master-cp2

General Information
-------------------
ImcPluginsCP contains a selection of CellProfiler modules that facilitate
handling, processing as well as measurement of multiplexed data. It was primarily
written with imaging mass cytometry (IMC) data for a Ilastik based image segmentation workflow.
Many modules are slightly modified versions of CellProfiler modules (https://github.com/CellProfiler/CellProfiler).
 
The modules were tested with CellProfiler 3.
 
For installation copy the folder to a local directry and modify the CellProfiler preferences to the plugin folder.
  
The modules
-------------------

* ColorToGray bb: a slight modification of the 'ColorToGray' CP module to support up to 60 channels per image
  -> This bill be deprecated as the corresponding change was pushed upstream to CellProfiller and should thus become available per default in the next version: https://github.com/CellProfiler/CellProfiler/pull/3619
* Crop bb: Crop a specified or random location from the image
* MaskToBinstack: allows to identify a main object in a mask and generate a stack of binary planes containing: 'is_maninobject', 'is_any_other_object', 'is_background'
* MeasureImageIntensityMultichannel: Allows to measure all the image planes of a multicolor image 
* MeasureObjectIntensityMultichannel: Allows to measure all the image planes of a multicolor image in objects 
* Rescale objects: Rescales object segmentation masks
* Save object crops: Crops object regions out of an image. One region per object.
* Save images ilastik: a helper module to save images as `.tiff` in a way that ilastik 1.2.1 will recognize it as xyc image 
  -> This will be deprecated, as I recommend to use the `saveimages_h5` module for this task and use `hdf5` instead of tiff
  -> This module relies on the TIFFFILE library, that needs to be installed in the python that `cellprofiller` is using. 
* Smooth Multichannel: allows to apply image filters to all stacks of a multichannel image
* Sumarize stack: converts a multichannel image into a single channel image by applying summarizing functions, e.g. sum of all channels 
* Transform binary: converts a boolean image to the 'distance to the border' between regions.
* Correct Spillover apply: applies spillover compensation on the images. Requires a spillover tiff image (flaot image with dimensions p*p (p=number of color channels). This can e.g. be calculated witht he R software CATALYST for mass cytometry data (https://bioconductor.org/packages/release/bioc/html/CATALYST.html, example script: https://github.com/BodenmillerGroup/cyTOFcompensation/blob/master/scripts/imc_adaptsm.Rmd)
* CorrectSpilloverApply:  applies spillover compensation on measurements, which is more accurate than on images (as object measurements are more accurate). Requires a spillover tiff image (flaot image with dimensions p*p (p=number of color channels). This can e.g. be calculated witht he R software CATALYST for mass cytometry data (https://bioconductor.org/packages/release/bioc/html/CATALYST.html, example script: https://github.com/BodenmillerGroup/cyTOFcompensation/blob/master/scripts/imc_adaptsm.Rmd)

Pleas read also the documetation within CellProfiler for more hints how to use these modules!
