'''<b>CorrectSpillover - Apply</b> applies an spillover matrix, usually created by
the R Bioconductor package CATALYST, to an image in order to correct for uneven
illumination (uneven shading).
<hr>

This module applies a previously calculate spillover matrix,
loaded by <b>LoadSingleImage</b>.
This module corrects each image in the pipeline using the function specified.

'''

import numpy as np
import scipy.optimize as spo

import cellprofiler.image  as cpi
import cellprofiler.module as cpm
import cellprofiler.setting as cps


SETTINGS_PER_IMAGE = 4
METHOD_LS = 'LeastSquares'
METHOD_NNLS = 'NonNegativeLeastSquares'

class CorrectSpilloverApply(cpm.Module):
    category = "Image Processing"
    variable_revision_number = 1
    module_name = "CorrectSpilloverApply"

    def create_settings(self):
        """Make settings here (and set the module name)"""
        self.images = []
        self.add_image(can_delete = False)
        self.add_image_button = cps.DoSomething("", "Add another image",
                                                self.add_image)

    def add_image(self, can_delete = True):
        '''Add an image and its settings to the list of images'''
        image_name = cps.ImageNameSubscriber(
            "Select the input image",
            cps.NONE, doc = '''
            Select the image to be corrected.''')

        corrected_image_name = cps.ImageNameProvider(
            "Name the output image",
            "SpillCorrected", doc = '''
            Enter a name for the corrected image.''')

        spill_correct_function_image_name = cps.ImageNameSubscriber(
            "Select the spillover function image",
            cps.NONE, doc = '''
            Select the spillover correction image that will be used to
            carry out the correction. This image is usually produced by the R
            software CATALYST or loaded as a .tiff format image using the
            <b>Images</b> module or
            <b>LoadSingleImage</b>.''')
        spill_correct_method = cps.Choice(
            "Spillover correction method",
            [ METHOD_LS, METHOD_NNLS], doc = """
            Select the spillover correction method.
            <ul>
            <li><i>%(METHOD_LS)s:</i> Gives the least square solution
            for overdetermined solutions or the exact solution for exactly 
            constraint problems. </li>
            <li><i>%(METHOD_NNLS)s:</i> Gives the non linear least squares
            solution: The most accurate solution, according to the least
            squares criterium, without any negative values.
            </li>
            </ul>
            """ % globals())

        image_settings = cps.SettingsGroup()
        image_settings.append("image_name", image_name)
        image_settings.append("corrected_image_name", corrected_image_name)
        image_settings.append("spill_correct_function_image_name",
                              spill_correct_function_image_name)
        image_settings.append("spill_correct_method", spill_correct_method)

        if can_delete:
            image_settings.append("remover",
                                  cps.RemoveSettingButton("","Remove this image",
                                                          self.images,
                                                          image_settings))
        image_settings.append("divider",cps.Divider())
        self.images.append(image_settings)

    def settings(self):
        """Return the settings to be loaded or saved to/from the pipeline

        These are the settings (from cellprofiler.settings) that are
        either read from the strings in the pipeline or written out
        to the pipeline. The settings should appear in a consistent
        order so they can be matched to the strings in the pipeline.
        """
        result = []
        for image in self.images:
            result += [image.image_name, image.corrected_image_name,
                       image.spill_correct_function_image_name,
                       image.spill_correct_method
                      ]
        return result

    def visible_settings(self):
        """Return the list of displayed settings
        """
        result = []
        for image in self.images:
            result += [image.image_name, image.corrected_image_name,
                       image.spill_correct_function_image_name,
                       image.spill_correct_method
                      ]
            #
            # Get the "remover" button if there is one
            #
            remover = getattr(image, "remover", None)
            if remover is not None:
                result.append(remover)
            result.append(image.divider)
        result.append(self.add_image_button)
        return result

    def prepare_settings(self, setting_values):
        """Do any sort of adjustment to the settings required for the given values

        setting_values - the values for the settings

        This method allows a module to specialize itself according to
        the number of settings and their value. For instance, a module that
        takes a variable number of images or objects can increase or decrease
        the number of relevant settings so they map correctly to the values.
        """
        #
        # Figure out how many images there are based on the number of setting_values
        #
        assert len(setting_values) % SETTINGS_PER_IMAGE == 0
        image_count = len(setting_values) / SETTINGS_PER_IMAGE
        del self.images[image_count:]
        while len(self.images) < image_count:
            self.add_image()

    def run(self, workspace):
        """Run the module

        workspace    - The workspace contains
        pipeline     - instance of cpp for this run
        image_set    - the images in the image set being processed
        object_set   - the objects (labeled masks) in this image set
        measurements - the measurements for this run
        frame        - the parent frame to whatever frame is created. None means don't draw.
        """
        for image in self.images:
            self.run_image(image, workspace)

    def run_image(self, image, workspace):
        '''Perform illumination according to the parameters of one image setting group

        '''
        #
        # Get the image names from the settings
        #
        image_name = image.image_name.value
        spill_correct_name = image.spill_correct_function_image_name.value
        corrected_image_name = image.corrected_image_name.value
        #
        # Get images from the image set
        #
        orig_image = workspace.image_set.get_image(image_name)
        spillover_mat = workspace.image_set.get_image(spill_correct_name)
        #
        # Either divide or subtract the illumination image from the original
        #
        method = image.spill_correct_method.value
        output_pixels = self.compensate_image_ls(orig_image.pixel_data,
                                              spillover_mat.pixel_data, method)
        # Save the output image in the image set and have it inherit
        # mask & cropping from the original image.
        #
        output_image = cpi.Image(output_pixels, parent_image = orig_image)
        workspace.image_set.add(corrected_image_name, output_image)
        #
        # Save images for display
        #
        if self.show_window:
            if not hasattr(workspace.display_data, 'images'):
                workspace.display_data.images = {}
                workspace.display_data.images[image_name] = orig_image.pixel_data
                workspace.display_data.images[corrected_image_name] = output_pixels
                workspace.display_data.images[spill_correct_name] = spillover_mat.pixel_data

    def compensate_image_ls(self, img, sm, method):
        """
        Compensate an img with dimensions (x, y, c) with a spillover matrix
        with dimensions (c, c) by first reshaping the matrix to the shape dat=(x*y,
        c) and the solving the linear system:
            comp * sm = dat -> comp = dat * inv(sm)

        Example: 
            >>> img = np.array([[[1,0.1],[0, 1], [1,0.1]],
                                [[0,1],[1,0.1], [2,0.2]]])
            >>> sm = np.array([[1,0.1],[0,1]])
            >>> compensate_image(sm, img)
            array([[[ 1.,  0.],
                    [ 0.,  1.],
                    [ 1.,  0.]],
                   [[ 0.,  1.],
                    [ 1.,  0.],
                    [ 2.,  0.]]])
        """
        x, y ,c = img.shape
        dat = np.ravel(img, order='C')
        dat = np.reshape(dat,(x*y,c), order='C')
        if method == METHOD_LS:
            compdat = np.linalg.lstsq(sm.T, dat.T)[0]
            compdat = compdat.T
        if method == METHOD_NNLS:
            nnls = lambda x: spo.nnls(sm.T, x)[0]
            compdat = np.apply_along_axis(nnls,1, dat)
        compdat = compdat.ravel(order='C')
        comp_img = np.reshape(compdat, (x,y,c), order='C')
        return comp_img

    def display(self, workspace, figure):
        ''' Display one row of orig / illum / output per image setting group'''
        figure.set_subplots((3, len(self.images)))
        for j, image in enumerate(self.images):
            image_name = image.image_name.value
            spill_correct_function_image_name = \
                    image.spill_correct_function_image_name.value
            corrected_image_name = image.corrected_image_name.value
            orig_image = workspace.display_data.images[image_name]
            illum_image = workspace.display_data.images[spill_correct_function_image_name]
            corrected_image = workspace.display_data.images[corrected_image_name]
            def imshow(x, y, image, *args, **kwargs):
                if image.ndim == 2:
                    f = figure.subplot_imshow_grayscale
                else:
                    f = figure.subplot_imshow_color
                    return f(x, y, image, *args, **kwargs)
            imshow(0, j, orig_image,
               "Original image: %s" % image_name,
               sharexy = figure.subplot(0,0))
            title = ("Illumination function: %s\nmin=%f, max=%f" %
                 (spill_correct_function_image_name,
                  round(illum_image.min(), 4),
                  round(illum_image.max(), 4)))
            imshow(1, j, illum_image, title,
              sharexy = figure.subplot(0,0))
            imshow(2, j, corrected_image,
              "Final image: %s" %
              corrected_image_name,
              sharexy = figure.subplot(0,0))


    def upgrade_settings(self, setting_values, variable_revision_number,
                         module_name, from_matlab):
        """Adjust settings based on revision # of save file

        setting_values - sequence of string values as they appear in the
        saved pipeline
        variable_revision_number - the variable revision number of the module
        at the time of saving
        module_name - the name of the module that did the saving
        from_matlab - True if saved in CP Matlab, False if saved in pyCP

        returns the updated setting_values, revision # and matlab flag
        """
        if variable_revision_number < 1:
            n_settings_old = 3
            n_images = len(setting_values)/n_settings_old
            setting_values = \
             [setting_values[(i*n_settings_old):((i+1)*n_settings_old)] +
             [METHOD_LS] for i in range(n_images)][0]
            variable_revision_number =+ 1
        return setting_values, variable_revision_number, from_matlab
