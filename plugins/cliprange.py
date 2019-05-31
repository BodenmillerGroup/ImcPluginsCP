# coding=utf-8

#################################
#
# Imports from useful Python libraries
#
#################################

import numpy as np
import scipy.ndimage

#################################
#
# Imports from CellProfiler
#
##################################

import cellprofiler.image
import cellprofiler.module
import cellprofiler.setting

__doc__ = """\
ClipRange
=============

**ClipRange**
Clips the maximum of an image by setting all values higher than an user defined percentile to the value of said percentile.
This is useful if an image has rare but strong outliers.

============ ============ ===============
Supports 2D? Supports 3D? Respects masks?
============ ============ ===============
YES          NO           YES
============ ============ ===============

See also
^^^^^^^^
Smoothing can also be used to address the outlier problem, e.g. with a median filter.

What do I need as input?
^^^^^^^^^^^^^^^^^^^^^^^^
Can be a single or multichannel image. The filter will be applied per plane.


What do I get as output?
^^^^^^^^^^^^^^^^^^^^^^^^
The filtered image.

Measurements made by this module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
No measurement will be made.
TODO: potentially record the percentile value that was used for truncating. However this can also be found by looking at the image maximal pixel value, thus it is likely not necessary.

Technical notes
^^^^^^^^^^^^^^^
Nothing fancy done here.

References
^^^^^^^^^^
"""

#
# Constants
#
# It's good programming practice to replace things like strings with
# constants if they will appear more than once in your program. That way,
# if someone wants to change the text, that text will change everywhere.
# Also, you can't misspell it by accident.
#

#
# The module class.
#
# Your module should "inherit" from cellprofiler.module.Module, or a
# subclass of cellprofiler.module.Module. This module inherits from
# cellprofiler.module.ImageProcessing, which is the base class for
# image processing modules. Image processing modules take an image as
# input and output an image.
#
# This module will use the methods from cellprofiler.module.ImageProcessing
# unless you re-implement them. You can let cellprofiler.module.ImageProcessing
# do most of the work and implement only what you need.
#
# Other classes you can inherit from are:
#
# -  cellprofiler.module.ImageSegmentation: modules which take an image
#    as input and output a segmentation (objects) should inherit from this
#    class.
# -  cellprofiler.module.ObjectProcessing: modules which operate on objects
#    should inherit from this class. These are modules that take objects as
#    input and output new objects.
#
class ClipRange(cellprofiler.module.ImageProcessing):
    #
    # The module starts by declaring the name that's used for display,
    # the category under which it is stored and the variable revision
    # number which can be used to provide backwards compatibility if
    # you add user-interface functionality later.
    #
    # This module's category is "Image Processing" which is defined
    # by its superclass.
    #
    module_name = "ClipRange"

    variable_revision_number = 1

    #
    # "create_settings" is where you declare the user interface elements
    # (the "settings") which the user will use to customize your module.
    #
    # You can look at other modules and in cellprofiler.settings for
    # settings you can use.
    #
    def create_settings(self):
        #
        # The superclass (cellprofiler.module.ImageProcessing) defines two
        # settings for image input and output:
        #
        # -  x_name: an ImageNameSubscriber which "subscribes" to all
        #    ImageNameProviders in prior modules. Modules before yours will
        #    put images into CellProfiler. The ImageNameSubscriber gives
        #    your user a list of these images which can then be used as inputs
        #    in your module.
        # -  y_name: an ImageNameProvider makes the image available to subsequent
        #    modules.
        super(ClipRange, self).create_settings()

        #
        # reST help that gets displayed when the user presses the
        # help button to the right of the edit box.
        #
        # The superclass defines some generic help test. You can add
        # module-specific help text by modifying the setting's "doc"
        # string.
        #
        self.x_name.doc = """\
This is the image that the module operates on. You can choose any image
that is made available by a prior module.

**ClipRange** will clip the range of this image.
"""
        #
        self.outlier_percentile = cellprofiler.setting.Float(
            text="Outlier Percentile",
            value=0.999,  # The default value is 1 - a short-range scale
            minval=0,  # We don't let the user type in really small values
            maxval=1,  # or large values
            doc="""\
                This sets the percentile that will be clipd. E.g. if 0.99 is set, all pixel values that are higher than the value of the pixel at the 99th percentiles will be set to the value at the 99th percentile. In other words, the highest percent of pixel will be clipd.
"""
        )

    #
    # The "settings" method tells CellProfiler about the settings you
    # have in your module. CellProfiler uses the list for saving
    # and restoring values for your module when it saves or loads a
    # pipeline file.
    #
    def settings(self):
        #
        # The superclass's "settings" method returns [self.x_name, self.y_name],
        # which are the input and output image settings.
        #
        settings = super(ClipRange, self).settings()

        # Append additional settings here.
        return settings + [
            self.outlier_percentile
        ]

    #
    # "visible_settings" tells CellProfiler which settings should be
    # displayed and in what order.
    #
    # You don't have to implement "visible_settings" - if you delete
    # visible_settings, CellProfiler will use "settings" to pick settings
    # for display.
    #
    def visible_settings(self):
        #
        # The superclass's "visible_settings" method returns [self.x_name,
        # self.y_name], which are the input and output image settings.
        #
        visible_settings = super(ClipRange, self).visible_settings()

        # Configure the visibility of additional settings below.
        visible_settings += [
            self.outlier_percentile
        ]

        #
        # Show the user the scale only if self.wants_smoothing is checked
        #

        return visible_settings

    #
    # CellProfiler calls "run" on each image set in your pipeline.
    #
    def run(self, workspace):
        #
        # The superclass's "run" method handles retreiving the input image
        # and saving the output image. Module-specific behavior is defined
        # by setting "self.function", defined in this module. "self.function"
        # is called after retrieving the input image and before saving
        # the output image.
        #
        # The first argument of "self.function" is always the input image
        # data (as a numpy array). The remaining arguments are the values of
        # the module settings as they are returned from "settings" (excluding
        # "self.y_data", or the output image).
        #
        self.function = clip_percentile

        super(ClipRange, self).run(workspace)

    #
    # "volumetric" indicates whether or not this module supports 3D images.
    # The "gradient_image" function is inherently 2D, and we've noted this
    # in the documentation for the module. Explicitly return False here
    # to indicate that 3D images are not supported.
# The first parameter must be the input image data. The remaining parameters are
    #
    def volumetric(self):
        return False


    def display(self, workspace, figure, cmap=["gray", "gray"]):
        """
        Per default the display is grayscale. If the image is color, set it to color mode.

        """
        if len(workspace.display_data.x_data.shape) > 2:
            layout = (2, 1)

            figure.set_subplots(
                dimensions=workspace.display_data.dimensions,
                subplots=layout
            )

            figure.subplot_imshow_color(
                image=workspace.display_data.x_data,
                title=self.x_name.value,
                normalize=True,
                x=0,
                y=0
            )

            figure.subplot_imshow_color(
                image=workspace.display_data.y_data,
                sharexy=figure.subplot(0, 0),
                title=self.y_name.value,
                normalize=True,
                x=1,
                y=0
            )
        else:
            super(ClipRange, self).display(workspace, figure, cmap)


# This is the function that gets called during "run" to create the output image.
# the additional settings defined in "settings", in the order they are returned.
#
# This function must return the output image data (as a numpy array).
#
def clip_percentile(pixels, outlier_percentile):
    if len(pixels.shape) == 3:
        output_pixels = pixels.copy()
        for channel in range(pixels.shape[2]):
            output_pixels[:, :, channel] = _clip_percentile_plane(
                    pixels[:,:,channel], outlier_percentile)
    else:
        output_pixels = _clip_percentile_plane(pixels, outlier_percentile)
    return output_pixels

def _clip_percentile_plane(img, percentile):
    tresh = np.percentile(img[:],percentile*100)
    return np.clip(img, a_min=None, a_max=tresh)

