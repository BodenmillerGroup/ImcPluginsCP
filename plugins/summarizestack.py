'''
<b>Summarize Stack</b> converts an image with multiple channels to one image by averaging over the pixel values.
<hr>


<br>
<i>Note:</i>All <b>Identify</b> modules require grayscale images.
<p>See also <b>GrayToColor</b>.
'''

import re

import matplotlib.colors
import numpy as np
import functools

import cellprofiler.image as cpi
import cellprofiler.module as cpm
import cellprofiler.setting as cps

CH_CHANNELS = "Channels"
MEAN = 'Mean'
MEDIAN = 'Median'
CUSTOMFUNCTION = 'Python Function'
SLOT_CHANNEL_COUNT = 40
SLOT_FIXED_COUNT = 20
SLOTS_PER_CHANNEL = 3
SLOT_CHANNEL_CHOICE = 0


class ColorToGray(cpm.Module):
    module_name = "Summarize Stack"
    variable_revision_number = 0
    category = "Image Processing"

    def create_settings(self):
        self.image_name = cps.ImageNameSubscriber(
                "Select the input image", cps.NONE)

        self.conversion_method = cps.Choice(
                "Conversion method",
                [MEAN, MEDIAN, CUSTOMFUNCTION], doc='''
            How do you want to summarize the multichannel image?
            <ul>
            <li><i>%(MEAN)s:</i> Takes the mean.</li>
            <li><i>%(MEDIAN)s</i> Takes the median</li>
            <li><i>%(MEDIAN)s</i> Applies a cutstom python function</li>
            </ul>''' % globals())

        self.custom_function = cps.Text("Input a Python function", 'np.mean', doc='''
        Can be a simple function as "np.max" (without ") or complicated as "functools.partial(np.percentile,q=80, axis=2)".
        functools is imported as convenience.
        ''')
        # The following settings are used for the combine option
        self.grayscale_name = cps.ImageNameProvider(
                "Name the output image", "OrigGray")

        # The alternative model:
        self.channels = []


    def visible_settings(self):
        """Return either the "combine" or the "split" settings"""
        vv = [self.image_name, self.conversion_method]
        if self.conversion_method == CUSTOMFUNCTION:
            vv+= [self.custom_function]
        vv += [self.grayscale_name]
        return vv

    def settings(self):
        """Return all of the settings in a consistent order"""
        return [self.image_name, self.conversion_method,
                self.grayscale_name, self.custom_function]

    def validate_module(self, pipeline):
        """Test to see if the module is in a valid state to run

        Throw a ValidationError exception with an explanation if a module is not valid.
        Make sure that we output at least one image if split
        """


    def run(self, workspace):
        """Run the module

        pipeline     - instance of CellProfiler.Pipeline for this run
        workspace    - the workspace contains:
            image_set    - the images in the image set being processed
            object_set   - the objects (labeled masks) in this image set
            measurements - the measurements for this run
            frame        - display within this frame (or None to not display)
        """
        image = workspace.image_set.get_image(self.image_name.value,
                                                must_be_color=True)
        if self.conversion_method == MEAN:
            self.run_summarize(workspace, image, np.mean, axis=2)
        if self.conversion_method == MEDIAN:
            self.run_summarize(workspace, image, np.median, axis=2)
        if self.conversion_method == CUSTOMFUNCTION:
            self.run_summarize(workspace, image, eval(self.custom_function.get_value()), axis=2)

    def display(self, workspace, figure):
        self.display_combine(workspace, figure)

    def run_summarize(self, workspace, image, fkt, **kwargs):
        """Combine images to make a grayscale one
        """
        input_image = image.pixel_data
        print(image.pixel_data.shape)
        output_image = fkt(input_image, **kwargs)
        image = cpi.Image(output_image, parent_image=image)
        workspace.image_set.add(self.grayscale_name.value, image)

        workspace.display_data.input_image = input_image
        workspace.display_data.output_image = output_image

    def display_combine(self, workspace, figure):
        import matplotlib.cm

        input_image = workspace.display_data.input_image
        output_image = workspace.display_data.output_image
        #if len(input_image.shape) > 2:
        #    input_image = input_image[:,:,0]
        figure.set_subplots((1, 2))
        figure.subplot_imshow_color(0, 0, input_image,
                              title="Original image: %s" % self.image_name)
        figure.subplot_imshow(0, 1, output_image,
                              title="Grayscale image: %s" % self.grayscale_name,
                              colormap=matplotlib.cm.Greys_r,
                              sharexy=figure.subplot(0, 0))


    def prepare_settings(self, setting_values):
        '''Prepare the module to receive the settings

        setting_values - one string per setting to be initialized

        Adjust the number of channels to match the number indicated in
        the settings.
        '''


    def upgrade_settings(self,
                         setting_values,
                         variable_revision_number,
                         module_name,
                         from_matlab):


        return setting_values, variable_revision_number, from_matlab
