'''
<b> Mask 2 binstack </b> converts a mask to an binary object stack
<hr>
This module is thought for cropped out masks that contain one main object.
The main object id should be provided by metadata or manually. The module will
then create a stack of 3 binary mask layers: the main object, other objects,
background
<br>
'''

import re

import matplotlib.colors
import numpy as np

import cellprofiler.cpimage  as cpi
import cellprofiler.cpmodule as cpm
import cellprofiler.settings as cps


class MaskToBinstack(cpm.CPModule):

    module_name = "MaskToBinstack"
    variable_revision_number = 1
    category = "Object Processing"

    def create_settings(self):
        self.objects_name = cps.ObjectNameSubscriber(
                "Select the input object", cps.NONE)
        
        self.output_name = cps.ImageNameProvider(
                "Input the output image stack name",
                "BinStack", doc="""
            Input the output name.
            """ %globals())

        self.main_object_id = cps.Text(
                "Indicate the object id",
                '1',
                doc="""
                Indicates the id from the main object.
                Rightclick to choose a metadata value.
                """ % globals(), metadata=True)

    def visible_settings(self):
        """Return either the "combine" or the "split" settings"""
        return [self.objects_name, self.output_name, self.main_object_id]

    def settings(self):
        """Return all of the settings in a consistent order"""
        return [self.objects_name,
                self.main_object_id]


    def validate_module(self, pipeline):
        """Test to see if the module is in a valid state to run

        Throw a ValidationError exception with an explanation if a module is not valid.
        """
        pass

    def run(self, workspace):
        """Run the module
        :
        pipeline     - instance of CellProfiler.Pipeline for this run
        workspace    - the workspace contains:
            image_set    - the images in the image set being processed
            object_set   - the objects (labeled masks) in this image set
            measurements - the measurements for this run
            frame        - display within this frame (or None to not display)
        """
        objmask = workspace.object_set.get_objects(self.objects_name.value)
        main_id = int(workspace.measurements.apply_metadata(
            self.main_object_id.value))
        name = self.output_name.value
        self.run_split(workspace, objmask, main_id, name)

    def display(self, workspace, figure):
        self.display_split(workspace, figure)

    def run_split(self, workspace, objmask, main_id, name):
        """Split image into individual components
        """
        segmented = objmask.get_segmented()
        is_main = segmented == main_id
        is_bg = segmented == 0
        is_other = (is_bg == False) & (is_main == False)
        imgs = [is_main, is_other, is_bg]
        bin_stack = np.stack(imgs, axis=2)
        bin_stack = bin_stack.astype(np.uint8)
        workspace.image_set.add(name, cpi.Image(bin_stack, convert=False))
        disp_collection = [[img, tit] for img, tit in zip(
            imgs, ['is main', 'is other', 'is bg'])]
        workspace.display_data.input_image = segmented
        workspace.display_data.disp_collection = disp_collection

    def display_split(self, workspace, figure):
        import matplotlib.cm

        input_image = workspace.display_data.input_image
        disp_collection = workspace.display_data.disp_collection
        ndisp = len(disp_collection)
        if ndisp == 1:
            subplots = (1, 2)
        else:
            subplots = (2, 2)
        figure.set_subplots(subplots)
        figure.subplot_imshow(0, 0, input_image,
                              title="Original image")

        if ndisp == 1:
            layout = [(0, 1)]
        elif ndisp == 2:
            layout = [(1, 0), (0, 1)]
        else:
            layout = [(1, 0), (0, 1), (1, 1)]
        for xy, disp in zip(layout, disp_collection):
            figure.subplot_imshow(xy[0], xy[1], disp[0],
                                  title="%s image" % (disp[1]),
                                  colormap=matplotlib.cm.Greys_r,
                                  sharexy=figure.subplot(0, 0))

    def prepare_settings(self, setting_values):
        '''Prepare the module to receive the settings

        setting_values - one string per setting to be initialized

        Adjust the number of channels to match the number indicated in
        the settings.
        '''
        return setting_values

    def upgrade_settings(self,
                         setting_values,
                         variable_revision_number,
                         module_name,
                         from_matlab):
        return setting_values, variable_revision_number, from_matlab
