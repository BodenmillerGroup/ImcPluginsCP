# coding=utf-8

"""
SaveImages - DEPRECATED
==========

**SaveImages** saves image or movie files.

Because CellProfiler usually performs many image analysis steps on many
groups of images, it does *not* save any of the resulting images to the
hard drive unless you specifically choose to do so with the
**SaveImages** module. You can save any of the processed images created
by CellProfiler during the analysis using this module.

You can choose from many different image formats for saving your files.
This allows you to use the module as a file format converter, by loading
files in their original format and then saving them in an alternate
format.

This module has been modified to
a) save images with float values > 1 as float
b) save stacks (e.g. multicolor images) as cxy images in the standard imagej format
   This is required for ilastik to read the images correctly.

This module is not functional any more.
Working with float images with values > 1 is not longer properly supported
cellprofiler.

Saving stacks for Ilastik can be done via saving them as hdf5 images in
the main CP module.

============ ============ ===============
Supports 2D? Supports 3D? Respects masks?
============ ============ ===============
YES          YES          YES
============ ============ ===============

See also
^^^^^^^^

See also **NamesAndTypes**.
"""

import cellprofiler_core.measurement
import cellprofiler_core.module
import cellprofiler_core.setting
from cellprofiler.modules import _help

from cellprofiler_core.setting import HTMLText

IF_IMAGE = "Image"
IF_MASK = "Mask"
IF_CROPPING = "Cropping"
IF_MOVIE = "Movie"
IF_ALL = [IF_IMAGE, IF_MASK, IF_CROPPING, IF_MOVIE]

BIT_DEPTH_8 = "8-bit integer"
BIT_DEPTH_16 = "16-bit integer"
BIT_DEPTH_FLOAT = "32-bit floating point"

FN_FROM_IMAGE = "From image filename"
FN_SEQUENTIAL = "Sequential numbers"
FN_SINGLE_NAME = "Single name"

SINGLE_NAME_TEXT = "Enter single file name"
SEQUENTIAL_NUMBER_TEXT = "Enter file prefix"

FF_JPEG = "jpeg"
FF_NPY = "npy"
FF_PNG = "png"
FF_TIFF = "tiff"

PC_WITH_IMAGE = "Same folder as image"

WS_EVERY_CYCLE = "Every cycle"
WS_FIRST_CYCLE = "First cycle"
WS_LAST_CYCLE = "Last cycle"


DEPRECATION_STRING = """
                This module is not functional any more.\n
                Working with float images with values > 1 is not longer properly supported
                cellprofiler.\n

                Saving stacks for Ilastik can be done via saving them as hdf5 images in
                the main CP module.\n
                Please MANUALLY change this module to the SaveImages module!\n
                This dummy module will be removed in the next major ImcPluginsCP version.\n
                """

class Deprecated_SaveImagesIlastik(cellprofiler_core.module.Module):
    module_name = "SaveImages Ilastik"

    variable_revision_number = 13

    category = "Deprecated"

    def create_settings(self):
        self.deprecation_warning = HTMLText(
            text="Deprecation Warning", content=DEPRECATION_STRING, doc=DEPRECATION_STRING
        )

        self.save_image_or_figure = cellprofiler_core.setting.choice.Choice(
            "Select the type of image to save",
            IF_ALL,
            IF_IMAGE,
            doc="""\
The following types of images can be saved as a file on the hard drive:

-  *{IF_IMAGE}:* Any of the images produced upstream of **SaveImages**
   can be selected for saving. Outlines of objects created by other
   modules such as **Identify** modules, **Watershed**, and various object
   processing modules can also be saved with this option, but you must
   use the **OverlayOutlines** module to create them prior to saving images.
   Likewise, if you wish to save the objects themselves, you must use the
   **ConvertObjectsToImage** module to create a savable image.
-  *{IF_MASK}:* Relevant only if a module that produces masks has been used
  such as **Crop**, **MaskImage**, or **MaskObjects**. These
   modules create a mask of the pixels of interest in the
   image. Saving the mask will produce a binary image in which the
   pixels of interest are set to 1; all other pixels are set to 0.
-  *{IF_CROPPING}:* Relevant only if the **Crop** module is used. The
   **Crop** module also creates a cropping image which is typically the
   same size as the original image. However, since **Crop** permits
   removal of the rows and columns that are left blank, the cropping can
   be of a different size than the mask.
-  *{IF_MOVIE}:* A sequence of images can be saved as a TIFF stack.
            """.format(**{
                "IF_CROPPING": IF_CROPPING,
                "IF_IMAGE": IF_IMAGE,
                "IF_MASK": IF_MASK,
                "IF_MOVIE": IF_MOVIE
            })
        )

        self.image_name = cellprofiler_core.setting.text.ImageName(
            "Select the image to save", doc="Select the image you want to save."
        )

        self.file_name_method = cellprofiler_core.setting.choice.Choice(
            "Select method for constructing file names",
            [
                FN_FROM_IMAGE,
                FN_SEQUENTIAL,
                FN_SINGLE_NAME
            ],
            FN_FROM_IMAGE,
            doc="""\
*(Used only if saving non-movie files)*

Several choices are available for constructing the image file name:

-  *{FN_FROM_IMAGE}:* The filename will be constructed based on the
   original filename of an input image specified in **NamesAndTypes**.
   You will have the opportunity to prefix or append additional text.

   If you have metadata associated with your images, you can append
   text to the image filename using a metadata tag. This is especially
   useful if you want your output given a unique label according to the
   metadata corresponding to an image group. The name of the metadata to
   substitute can be provided for each image for each cycle using the
   **Metadata** module.
-  *{FN_SEQUENTIAL}:* Same as above, but in addition, each filename
   will have a number appended to the end that corresponds to the image
   cycle number (starting at 1).
-  *{FN_SINGLE_NAME}:* A single name will be given to the file. Since
   the filename is fixed, this file will be overwritten with each cycle.
   In this case, you would probably want to save the image on the last
   cycle (see the *Select how often to save* setting). The exception to
   this is to use a metadata tag to provide a unique label, as mentioned
   in the *{FN_FROM_IMAGE}* option.

{USING_METADATA_TAGS_REF}

{USING_METADATA_HELP_REF}
""".format(**{
                "FN_FROM_IMAGE": FN_FROM_IMAGE,
                "FN_SEQUENTIAL": FN_SEQUENTIAL,
                "FN_SINGLE_NAME": FN_SINGLE_NAME,
                "USING_METADATA_HELP_REF": _help.USING_METADATA_HELP_REF,
                "USING_METADATA_TAGS_REF": _help.USING_METADATA_TAGS_REF
            })
        )

        self.file_image_name = cellprofiler_core.setting.subscriber.image_subscriber.FileImageSubscriber(
            "Select image name for file prefix",
            "None",
            doc="""\
*(Used only when “{FN_FROM_IMAGE}” is selected for constructing the filename)*

Select an image loaded using **NamesAndTypes**. The original filename
will be used as the prefix for the output filename.""".format(**{
                "FN_FROM_IMAGE": FN_FROM_IMAGE
            })
        )

        self.single_file_name = cellprofiler_core.setting.text.Text(
            SINGLE_NAME_TEXT,
            "OrigBlue",
            metadata=True,
            doc="""\
*(Used only when “{FN_SEQUENTIAL}” or “{FN_SINGLE_NAME}” are selected
for constructing the filename)*

Specify the filename text here. If you have metadata associated with
your images, enter the filename text with the metadata tags.
{USING_METADATA_TAGS_REF}
Do not enter the file extension in this setting; it will be appended
automatically.""".format(**{
                "FN_SEQUENTIAL": FN_SEQUENTIAL,
                "FN_SINGLE_NAME": FN_SINGLE_NAME,
                "USING_METADATA_TAGS_REF": _help.USING_METADATA_TAGS_REF
            })
        )

        self.number_of_digits = cellprofiler_core.setting.text.Integer(
            "Number of digits",
            4,
            doc="""\
*(Used only when “{FN_SEQUENTIAL}” is selected for constructing the filename)*

Specify the number of digits to be used for the sequential numbering.
Zeros will be used to left-pad the digits. If the number specified here
is less than that needed to contain the number of image sets, the latter
will override the value entered.""".format(**{
                "FN_SEQUENTIAL": FN_SEQUENTIAL
            })
        )

        self.wants_file_name_suffix = cellprofiler_core.setting.Binary(
            "Append a suffix to the image file name?",
            False,
            doc="""\
Select "*{YES}*" to add a suffix to the image’s file name. Select "*{NO}*"
to use the image name as-is.
            """.format(**{
                "NO": "No",
                "YES": "Yes"
            })
        )

        self.file_name_suffix = cellprofiler_core.setting.text.Text(
            "Text to append to the image name",
            "",
            metadata=True,
            doc="""\
*(Used only when constructing the filename from the image filename)*

Enter the text that should be appended to the filename specified above.
If you have metadata associated with your images, you may use metadata tags.

{USING_METADATA_TAGS_REF}

Do not enter the file extension in this setting; it will be appended
automatically.
""".format(**{
                "USING_METADATA_TAGS_REF": _help.USING_METADATA_TAGS_REF
            })
        )

        self.file_format = cellprofiler_core.setting.choice.Choice(
            "Saved file format",
            [
                FF_JPEG,
                FF_NPY,
                FF_PNG,
                FF_TIFF
            ],
            value=FF_TIFF,
            doc="""\
*(Used only when saving non-movie files)*

Select the format to save the image(s).

Only *{FF_TIFF}* supports saving as 16-bit or 32-bit. *{FF_TIFF}* is a
"lossless" file format.

*{FF_PNG}* is also a "lossless" file format and it tends to produce
smaller files without losing any image data.

*{FF_JPEG}* is also small but is a "lossy" file format and should not be
used for any images that will undergo further quantitative analysis.

Select *{FF_NPY}* to save an illumination correction image generated by
**CorrectIlluminationCalculate**.""".format(**{
                "FF_NPY": FF_NPY,
                "FF_TIFF": FF_TIFF,
                "FF_PNG": FF_PNG,
                "FF_JPEG": FF_JPEG
            })
        )

        self.pathname = cellprofiler_core.setting.text.Directory(
            "Output file location",
            self.file_image_name,
            doc="""\
This setting lets you choose the folder for the output files.
{IO_FOLDER_CHOICE_HELP_TEXT}

An additional option is the following:

-  *Same folder as image*: Place the output file in the same folder that
   the source image is located.

{IO_WITH_METADATA_HELP_TEXT}

If the subfolder does not exist when the pipeline is run, CellProfiler
will create it.

If you are creating nested subfolders using the sub-folder options, you
can specify the additional folders separated with slashes. For example,
“Outlines/Plate1” will create a “Plate1” folder in the “Outlines”
folder, which in turn is under the Default Input/Output Folder. The use
of a forward slash (“/”) as a folder separator will avoid ambiguity
between the various operating systems.
""".format(**{
                "IO_FOLDER_CHOICE_HELP_TEXT": _help.IO_FOLDER_CHOICE_HELP_TEXT,
                "IO_WITH_METADATA_HELP_TEXT": _help.IO_WITH_METADATA_HELP_TEXT
            })
        )

        self.bit_depth = cellprofiler_core.setting.choice.Choice(
            "Image bit depth",
            [
                BIT_DEPTH_8,
                BIT_DEPTH_16,
                BIT_DEPTH_FLOAT
            ],
            doc="""\
Select the bit-depth at which you want to save the images.

*{BIT_DEPTH_FLOAT}* saves the image as floating-point decimals with
32-bit precision. When the input data is integer or binary type, pixel
values are scaled within the range (0, 1). Floating point data is not
rescaled.

{BIT_DEPTH_16} and {BIT_DEPTH_FLOAT} images are supported only for
TIFF formats.""".format(**{
                "BIT_DEPTH_FLOAT": BIT_DEPTH_FLOAT,
                "BIT_DEPTH_16": BIT_DEPTH_16
            })
        )

        self.overwrite = cellprofiler_core.setting.Binary(
            "Overwrite existing files without warning?",
            False,
            doc="""\
Select "*{YES}*" to automatically overwrite a file if it already exists.
Select "*{NO}*" to be prompted for confirmation first.

If you are running the pipeline on a computing cluster, select "*{YES}*"
since you will not be able to intervene and answer the confirmation
prompt.""".format(**{
                "NO": "No",
                "YES": "Yes"
            })
        )

        self.when_to_save = cellprofiler_core.setting.choice.Choice(
            "When to save",
            [
                WS_EVERY_CYCLE,
                WS_FIRST_CYCLE,
                WS_LAST_CYCLE
            ],
            WS_EVERY_CYCLE,
            doc="""\
*(Used only when saving non-movie files)*

Specify at what point during pipeline execution to save file(s).

-  *{WS_EVERY_CYCLE}:* Useful for when the image of interest is
   created every cycle and is not dependent on results from a prior
   cycle.
-  *{WS_FIRST_CYCLE}:* Useful for when you are saving an aggregate
   image created on the first cycle, e.g.,
   **CorrectIlluminationCalculate** with the *All* setting used on
   images obtained directly from **NamesAndTypes**.
-  *{WS_LAST_CYCLE}:* Useful for when you are saving an aggregate image
   completed on the last cycle, e.g., **CorrectIlluminationCalculate**
   with the *All* setting used on intermediate images generated during
   each cycle.""".format(**{
                "WS_EVERY_CYCLE": WS_EVERY_CYCLE,
                "WS_FIRST_CYCLE": WS_FIRST_CYCLE,
                "WS_LAST_CYCLE": WS_LAST_CYCLE
            })
        )

        self.update_file_names = cellprofiler_core.setting.Binary(
            "Record the file and path information to the saved image?",
            False,
            doc="""\
Select "*{YES}*" to store filename and pathname data for each of the new
files created via this module as a per-image measurement.

Instances in which this information may be useful include:

-  Exporting measurements to a database, allowing access to the saved
   image. If you are using the machine-learning tools or image viewer in
   CellProfiler Analyst, for example, you will want to enable this
   setting if you want the saved images to be displayed along with the
   original images.""".format(**{
                "YES": "Yes"
            })
        )

        self.create_subdirectories = cellprofiler_core.setting.Binary(
            "Create subfolders in the output folder?",
            False, doc="""Select "*{YES}*" to create subfolders to match the input image folder structure.""".format(**{
                "YES": "Yes"
            })
        )

        self.root_dir = cellprofiler_core.setting.text.Directory(
            "Base image folder",
            doc="""\
*Used only if creating subfolders in the output folder*

In subfolder mode, **SaveImages** determines the folder for an image file by
examining the path of the matching input file. The path that SaveImages
uses is relative to the image folder chosen using this setting. As an
example, input images might be stored in a folder structure of
"images\/*experiment-name*\/*date*\/*plate-name*". If
the image folder is "images", **SaveImages** will store images in the
subfolder, "*experiment-name*\/*date*\/*plate-name*". If the
image folder is "images\/*experiment-name*", **SaveImages** will
store images in the subfolder, "*date*\/*plate-name*".""")

    def settings(self):
        """Return the settings in the order to use when saving"""
        return [self.save_image_or_figure, self.image_name,
                self.file_name_method, self.file_image_name,
                self.single_file_name, self.number_of_digits,
                self.wants_file_name_suffix,
                self.file_name_suffix, self.file_format,
                self.pathname, self.bit_depth,
                self.overwrite, self.when_to_save,
                self.update_file_names, self.create_subdirectories,
                self.root_dir]

    def visible_settings(self):
        """Return only the settings that should be shown"""
        result = [
            self.deprecation_warning,
            self.save_image_or_figure,
            self.image_name,
            self.file_name_method
        ]

        if self.file_name_method == FN_FROM_IMAGE:
            result += [self.file_image_name, self.wants_file_name_suffix]
            if self.wants_file_name_suffix:
                result.append(self.file_name_suffix)
        elif self.file_name_method == FN_SEQUENTIAL:
            self.single_file_name.text = SEQUENTIAL_NUMBER_TEXT
            # XXX - Change doc, as well!
            result.append(self.single_file_name)
            result.append(self.number_of_digits)
        elif self.file_name_method == FN_SINGLE_NAME:
            self.single_file_name.text = SINGLE_NAME_TEXT
            result.append(self.single_file_name)
        else:
            raise NotImplementedError("Unhandled file name method: %s" % self.file_name_method)
        if self.save_image_or_figure != IF_MOVIE:
            result.append(self.file_format)
        supports_16_bit = (self.file_format == FF_TIFF and self.save_image_or_figure == IF_IMAGE) or \
                          self.save_image_or_figure == IF_MOVIE
        if supports_16_bit:
            # TIFF supports 8 & 16-bit, all others are written 8-bit
            result.append(self.bit_depth)
        result.append(self.pathname)
        result.append(self.overwrite)
        if self.save_image_or_figure != IF_MOVIE:
            result.append(self.when_to_save)
        result.append(self.update_file_names)
        if self.file_name_method == FN_FROM_IMAGE:
            result.append(self.create_subdirectories)
            if self.create_subdirectories:
                result.append(self.root_dir)
        return result

    @property
    def module_key(self):
        return "%s_%d" % (self.module_name, self.module_num)

    def prepare_group(self, workspace, grouping, image_numbers):
        d = self.get_dictionary(workspace.image_set_list)
        if self.save_image_or_figure == IF_MOVIE:
            d['N_FRAMES'] = len(image_numbers)
            d['CURRENT_FRAME'] = 0
        return True

    def prepare_to_create_batch(self, workspace, fn_alter_path):
        self.pathname.alter_for_create_batch_files(fn_alter_path)
        if self.create_subdirectories:
            self.root_dir.alter_for_create_batch_files(fn_alter_path)

    def run(self, workspace):
        """Run the module

        pipeline     - instance of cellprofiler_core.pipeline for this run
        workspace    - the workspace contains:
            image_set    - the images in the image set being processed
            object_set   - the objects (labeled masks) in this image set
            measurements - the measurements for this run
            frame        - display within this frame (or None to not display)
        """
        raise NotImplementedError("""
                This module is deprecated!\n
                Please use the .hdf5 saving from the official
                SaveImages module to export images for Ilastik!
                """)


    def upgrade_settings(self, setting_values, variable_revision_number, module_name):
        return setting_values, variable_revision_number

    def validate_module(self, pipeline):
        if (self.save_image_or_figure in (IF_IMAGE, IF_MASK, IF_CROPPING) and
                    self.when_to_save in (WS_FIRST_CYCLE, WS_EVERY_CYCLE)):
            #
            # Make sure that the image name is available on every cycle
            #
            for setting in cellprofiler_core.setting.get_name_providers(pipeline,
                                                                   self.image_name):
                if setting.provided_attributes.get(cellprofiler_core.setting.AVAILABLE_ON_LAST_ATTRIBUTE):
                    #
                    # If we fell through, then you can only save on the last cycle
                    #
                    raise cellprofiler_core.setting.ValidationError("%s is only available after processing all images in an image group" %
                                                               self.image_name.value,
                                                               self.when_to_save)

        # XXX - should check that if file_name_method is
        # FN_FROM_IMAGE, that the named image actually has the
        # required path measurement

        # Make sure metadata tags exist
        if self.file_name_method == FN_SINGLE_NAME or \
                (self.file_name_method == FN_FROM_IMAGE and self.wants_file_name_suffix.value):
            text_str = self.single_file_name.value if self.file_name_method == FN_SINGLE_NAME else self.file_name_suffix.value
            undefined_tags = pipeline.get_undefined_metadata_tags(text_str)
            if len(undefined_tags) > 0:
                raise cellprofiler_core.setting.ValidationError(
                        "%s is not a defined metadata tag. Check the metadata specifications in your load modules" %
                        undefined_tags[0],
                        self.single_file_name if self.file_name_method == FN_SINGLE_NAME else self.file_name_suffix)

    def volumetric(self):
        return True

