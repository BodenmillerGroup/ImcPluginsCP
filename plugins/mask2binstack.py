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

import cellprofiler.image  as cpi
import cellprofiler.module as cpm
import cellprofiler.setting as cps

IF_OBJECTS     = "Objects"
IF_IMAGE       = "Image"

SEL_PROVIDED = 'provided'
SEL_MAXAREA = 'maximum area'
SEL_MID = 'image mid'

class MaskToBinstack(cpm.Module):

    module_name = "MaskToBinstack"
    variable_revision_number = 1
    category = "Object Processing"

    def create_settings(self):
        self.input_type = cps.Choice(
            "Select the type of input",
            [IF_IMAGE, IF_OBJECTS], IF_IMAGE)


        self.image_name = cps.ImageNameSubscriber(
            "Select input images", cps.NONE)

        self.objects_name = cps.ObjectNameSubscriber(
                "Select the input objects", cps.NONE,
        )
        
        self.output_name = cps.ImageNameProvider(
                "Input the output image stack name",
                "BinStack", doc="""
            Input the output name.
            """ %globals())
        
        self.main_object_def = cps.Choice(
            "How should the main label be determined?",
                [SEL_MID, SEL_MAXAREA, SEL_PROVIDED],
                SEL_MID, doc="""
            The main object can be determined by 3 ways:
            <ul>
            <li> %(SEL_PROVIDED)s: Label provided by metadata or
            manual. <\li>
            <li> %(SEL_MAXAREA)s: Label with the biggest area is assumed to be
            the main label. <\li>
            <li> %(SEL_MID)s: The label closest to the middle of the image is
            considered the main label. <\li>
            <\ul>
            """ % globals())

        self.main_object_id = cps.Text(
                "Indicate the object id",
                '1',
                doc="""
                Indicates the id from the main object.
                Rightclick to choose a metadata value.
                """ % globals(), metadata=True)

    def visible_settings(self):
        """Return either the "combine" or the "split" settings"""
        results = [self.input_type]
        if self.input_type == IF_IMAGE:
            results += [self.image_name]
        else:
            results += [self.objects_name]
        results += [self.output_name]
        results += [self.main_object_def]
        if self.main_object_def == SEL_PROVIDED:
            results += [self.main_object_id]
        return results

    def settings(self):
        """Return all of the settings in a consistent order"""
        return [self.input_type, self.image_name, self.objects_name,
                self.main_object_id]


    def validate_module(self, pipeline):
        """Test to see if the module is in a valid state to run

        Throw a ValidationError exception with an explanation if a module is not valid.
        """
        pass

    def run(self, workspace):
        """Run the module
         
        pipeline     - instance of CellProfiler.Pipeline for this run
        workspace    - the workspace contains:
            image_set    - the images in the image set being processed
            object_set   - the objects (labeled masks) in this image set
            measurements - the measurements for this run
            frame        - display within this frame (or None to not display)
        """
        if self.input_type == IF_IMAGE:
            image = workspace.image_set.get_image(
                self.image_name.value)
            objmask = np.round(image.pixel_data.copy() * image.scale)
        else:
            objmask = workspace.object_set.get_objects(
                self.objects_name.value).get_segmented()
        
        if self.main_object_def == SEL_PROVIDED:
            main_id = int(workspace.measurements.apply_metadata(
            self.main_object_id.value))
        elif self.main_object_def == SEL_MAXAREA:
            main_id = np.argmax(np.bincount(objmask[objmask > 0]))
        elif self.main_object_def == SEL_MID:
            idx = np.where(objmask > 0)
            dists = [(idx[i]-int(objmask.shape[i]/2))**2 for i in range(2)]
            dists = np.sqrt(dists[0] + dists[1])
            i = np.argmin(dists)
            main_id = objmask[idx[0][i], idx[1][i]]
        else:
            raise(self.main_object_def + ' not valid')

        name = self.output_name.value
        self.run_split(workspace, objmask, main_id, name)

    def display(self, workspace, figure):
        self.display_split(workspace, figure)

    def run_split(self, workspace, objmask, main_id, name):
        """Split image into individual components
        """
        segmented = objmask
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
