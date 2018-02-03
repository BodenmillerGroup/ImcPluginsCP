"""<b>Crop</b> crops an imag.
<hr>
Images are resized (made smaller or larger) based on user input. You
can resize an image by applying a resizing factor or by specifying the
desired dimensions, in pixels. You can also select which interpolation
method to use.
"""

import logging
import traceback

import numpy as np

logger = logging.getLogger(__name__)

import cellprofiler.module as cpm
import cellprofiler.image as cpi
import cellprofiler.setting as cps
import cellprofiler.measurement as cpmeas
C_RANDOM = 'Crop random sections of the image'
C_SPECIFIC = 'Crop specific image section'
C_X = 'X position of upper left corner of section'
C_Y = 'Y position of upper left corner of section'
C_H = 'Height of cropped section'
C_W = 'Width of cropped section'

'''The index of the additional image count setting'''
S_ADDITIONAL_IMAGE_COUNT = 7

class Crop(cpm.Module):

    category = "Image Processing"
    variable_revision_number = 2
    module_name = "Crop bb"

    def create_settings(self):
        self.image_name = cps.ImageNameSubscriber(
            "Select the input image",cps.NONE, doc = '''
            Select the image to be resized.''')

        self.cropped_image_name = cps.ImageNameProvider(
            "Name the output image", "croppedImage", doc = '''
            Enter the name of the cropped image.''')

        self.crop_random = cps.Choice(
            'Crop random or specified section?', [C_RANDOM, C_SPECIFIC])

        self.crop_x = cps.Text(
            "X of upper left corner",  '0',  doc = '''
            X position.''', metadata=True)


        self.crop_y = cps.Text(
            "Y of upper left corner",   '0',  doc = '''
            Y position.''', metadata=True)


        self.crop_w = cps.Text(
            "W width",   '100',  doc = '''
            Width of cut.''', metadata=True)

        self.crop_h = cps.Text(
            "H height",   '100',  doc = '''
            Height of cut.''', metadata=True)



        self.separator = cps.Divider(line=False)

        self.additional_images = []

        self.additional_image_count = cps.HiddenCount(
            self.additional_images, "Additional image count")

        self.add_button = cps.DoSomething("", "Add another image",
                                          self.add_image)

    def add_image(self, can_remove = True):
        '''Add an image + associated questions and buttons'''
        group = cps.SettingsGroup()
        if can_remove:
            group.append("divider", cps.Divider(line=False))

        group.append("input_image_name",
                     cps.ImageNameSubscriber(
                         "Select the additional image?",
                                            cps.NONE,doc="""
                                            What is the name of the additional image to resize? This image will be
                                            resized with the same settings as the first image."""))
        group.append("output_image_name",
                     cps.ImageNameProvider("Name the output image",
                                            "ResizedBlue",doc="""
                                            What is the name of the additional resized image?"""))
        if can_remove:
            group.append("remover", cps.RemoveSettingButton("", "Remove above image", self.additional_images, group))
        self.additional_images.append(group)

    def settings(self):
        result = [self.image_name,
                  self.cropped_image_name,
                self.crop_w,
                  self.crop_h,
                  self.crop_random,
                  self.crop_x,
                  self.crop_y,
                self.additional_image_count]

        for additional in self.additional_images:
            result += [additional.input_image_name, additional.output_image_name]

        return result

    def visible_settings(self):
        result = [self.image_name, self.cropped_image_name, self.crop_w,
                 self.crop_h, self.crop_random]
        if self.crop_random == C_SPECIFIC:
            result.append(self.crop_x)
            result.append(self.crop_y)

        for additional in self.additional_images:
            result += additional.visible_settings()
        result += [self.add_button]
        return result

    def prepare_settings(self, setting_values):
        '''Create the correct number of additional images'''
        try:
            additional_image_setting_count = \
                int(setting_values[S_ADDITIONAL_IMAGE_COUNT])
            if len(self.additional_images) > additional_image_setting_count:
                del self.additional_images[additional_image_setting_count:]
            else:
                for i in range(len(self.additional_images),
                               additional_image_setting_count):
                    self.add_image()
        except ValueError:
            logger.warning(
                'Additional image setting count was "%s" '
                'which is not an integer.',
                setting_values[S_ADDITIONAL_IMAGE_COUNT], exc_info=True)
            pass

    def run(self, workspace):
        crop_slice = self.get_crop(workspace, self.image_name.value,
                                   self.cropped_image_name.value)
        self.apply_crop(workspace, self.image_name.value,
                        self.cropped_image_name.value, crop_slice)
        self.save_crop_coordinates(workspace, crop_slice,
                                   self.cropped_image_name.value)

        for additional in self.additional_images:
            self.apply_crop(workspace, additional.input_image_name.value,
                            additional.output_image_name.value, crop_slice)
            self.save_crop_coordinates(workspace, crop_slice,
                                   additional.output_image_name.value)

    def get_crop(self, workspace, input_image_name, output_image_name):
        image = workspace.image_set.get_image(input_image_name)
        image_pixels = image.pixel_data
        if self.crop_random == C_RANDOM:
            x = None
            y = None
        else:
            x = int(workspace.measurements.apply_metadata(self.crop_x.value))
            y = int(workspace.measurements.apply_metadata(self.crop_y.value))
        crop_slice = self.crop_slice(image_pixels.shape[:2],
                                       w=int(workspace.measurements.apply_metadata(self.crop_w.value)),
                                       h=int(workspace.measurements.apply_metadata(self.crop_h.value)),
                                        x=x, y=y, flipped_axis=True
                                      )

        return crop_slice

    def apply_crop(self, workspace, input_image_name, output_image_name,
                   crop_slice):
        image = workspace.image_set.get_image(input_image_name)
        image_pixels = image.pixel_data
        if image_pixels.ndim > 2:
            crop_slice = self.add_slice_dimension(crop_slice)
        output_image = cpi.Image(image_pixels[crop_slice], parent_image=image)
        workspace.image_set.add(output_image_name, output_image)

        if self.show_window:
            if not hasattr(workspace.display_data, 'input_images'):
                workspace.display_data.input_images = [image.pixel_data]
                workspace.display_data.output_images = [output_image.pixel_data]
                workspace.display_data.input_image_names = [input_image_name]
                workspace.display_data.output_image_names = [output_image_name]
            else:
                workspace.display_data.input_images += [image.pixel_data]
                workspace.display_data.output_images += [output_image.pixel_data]
                workspace.display_data.input_image_names += [input_image_name]
                workspace.display_data.output_image_names += [output_image_name]

    def save_crop_coordinates(self, workspace, crop_slice, output_image_name):
        yh, xw =  [[c.start, c.stop-c.start] for c in crop_slice]
        m = workspace.measurements
        for name_feature, val in zip(['x', 'w', 'y', 'h'],xw+yh):
            cur_featurename = '_'.join(['Crop', output_image_name,
                                        name_feature])
            m.add_image_measurement('%s_%s' %  (cpmeas.C_METADATA,
                                                cur_featurename),
                                                val)
    def display(self, workspace, figure):
        '''Display the resized image

        workspace - the workspace being run
        statistics - a list of lists:
            0: index of this statistic
            1: input image name of image being aligned
            2: output image name of image being aligned
        '''
        input_images = workspace.display_data.input_images
        output_images = workspace.display_data.output_images
        input_image_names = workspace.display_data.input_image_names
        output_image_names = workspace.display_data.output_image_names

        figure.set_subplots((2, len(input_images)))

        for i, (input_image_pixels, output_image_pixels, input_image_name, output_image_name) in \
                enumerate(zip(input_images, output_images, input_image_names, output_image_names)):
            if input_image_pixels.ndim == 2:
                figure.subplot_imshow_bw(0, i, input_image_pixels,
                                         title=input_image_name)
                figure.subplot_imshow_bw(1, i, output_image_pixels,
                                         title=output_image_name)
            else:
                figure.subplot_imshow_color(0, i, input_image_pixels,
                                      title=input_image_name)
                figure.subplot_imshow_color(1, i, output_image_pixels,
                                      title=output_image_name)

    def get_measurement_columns(self, pipeline):
        meas = []
        for f in ['x', 'w', 'y', 'h']:
            meas.append((cpmeas.IMAGE, '_'.join([cpmeas.C_METADATA, 'Crop',
                         self.cropped_image_name.value, f]),
                         cpmeas.COLTYPE_INTEGER))
        return meas

    def upgrade_settings(self, setting_values, variable_revision_number,
                         module_name, from_matlab):

        return setting_values, variable_revision_number, from_matlab

    # functions
    @staticmethod
    def crop_slice(origshape, w, h=None, x=None, y=None, random_seed=None,
                   flipped_axis=False):
        """
        Returns a slicer to crop the image provided. If x and y position are not
        provided, a random slice will be taken.

        """
        if random_seed is not None:
            np.random.seed(random_seed)

        if h is None:
            h= w

        outsize = (w, h)
        if flipped_axis:
            outsize = reversed(outsize)
            x, y = y, x

        outslices = list()
        for dmax, dstart, dextend in zip(origshape, (x,y), outsize):
            if dmax > dextend:
                if dstart is None:
                    dstart = np.random.randint(0, dmax-dextend)
                dstart = min(dstart, dmax-dextend)
                outslices.append(np.s_[dstart:(dstart+dextend)])
            else:
                outslices.append(np.s_[0:dmax])
        outslices = tuple(outslices)
        return outslices

    @staticmethod
    def add_slice_dimension(sl, append=True):
        """
        Appends another dimension to a numpy slice
        :param sl: a numpy slice
        :return: a numpy slice extended for 1 dimension
        """

        if append:
            exsl = tuple([s for s in sl] + [np.s_[:]])
        else:
            exsl = tuple([np.s_[:]]+[s for s in sl])
        return exsl
