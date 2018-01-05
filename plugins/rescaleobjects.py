'''<b>Expand Or Shrink Objects</b> expands or shrinks objects by a defined distance.
<hr>
The module expands or shrinks objects by adding or removing border
pixels. You can specify a certain number of border pixels to be
added or removed, expand objects until they are almost touching or shrink
objects down to a point. Objects are never lost using this module (shrinking
stops when an object becomes a single pixel). The module can separate touching
objects without otherwise shrinking
the objects.

<p><b>ExpandOrShrinkObjects</b> can perform some specialized morphological operations that
remove pixels without completely removing an object. See the Settings help (below)
for more detail.</p>

<p><i>Special note on saving images:</i> You can use the settings in this module to pass object
outlines along to the module <b>OverlayOutlines</b> and then save them
with the <b>SaveImages</b> module. You can also pass the identified objects themselves along to the
object processing module <b>ConvertToImage</b> and then save them with the
<b>SaveImages</b> module.</p>

<h4>Available measurements</h4>
<b>Image measurements:</b>
<ul>
<li><i>Count:</i> Number of expanded/shrunken objects in the image.</li>
</ul>
<b>Object measurements:</b>
<ul>
<li><i>Location_X, Location_Y:</i> Pixel (<i>X,Y</i>) coordinates of the center of mass of
the expanded/shrunken objects.</li>
</ul>

<p>See also <b>Identify</b> modules.</p>'''

import numpy as np
from centrosome.cpmorphology import binary_shrink, thin
from centrosome.cpmorphology import fill_labeled_holes, adjacent
from centrosome.cpmorphology import skeletonize_labels, spur
from centrosome.outline import outline
from scipy.ndimage import distance_transform_edt

from skimage import transform
from skimage.morphology import disk
from skimage.filters import rank
import scipy.ndimage as ndi




import cellprofiler.image as cpi
import cellprofiler.module as cpm
import cellprofiler.measurement as cpmeas
import cellprofiler.object as cpo
import cellprofiler.setting as cps
from cellprofiler.modules.identify import add_object_count_measurements
from cellprofiler.modules.identify import add_object_location_measurements
from cellprofiler.modules.identify import get_object_measurement_columns
from cellprofiler.setting import YES, NO

O_UPSCALE = 'Upscale objects with a scaling factor'
O_DOWNSCALE = 'Downscale objects with a scaling factor'

O_ALL = [O_UPSCALE, O_DOWNSCALE]


class RescaleObjects(cpm.Module):
    module_name = 'RescaleObjects'
    category = 'Object Processing'
    variable_revision_number = 1

    def create_settings(self):
        self.object_name = cps.ObjectNameSubscriber(
                "Select the input objects",
                cps.NONE, doc='''
            Select the objects that you want to rescale.''')

        self.output_object_name = cps.ObjectNameProvider(
                "Name the output objects",
                "RescaledObject", doc='''
            Enter a name for the resulting objects.''')

        self.operation = cps.Choice(
                "Select the operation",
                O_ALL, doc='''
            Select the operation that you want to perform:
            <ul>
            <li><i>%(O_DOWNSCALE)s:</i> Downscale the Object Masks to a smaller image size.</li>
            <li><i>%(O_UPSCALE)s:</i> Expand objects, assigning every pixel in the image to an
            object. Background pixels are assigned to the nearest object.</li>
            </ul>''' % globals())

        self.scaling = cps.Float(
                "Factor to scale the object mask", 1, minval=0)


    def settings(self):
        return [self.object_name, self.output_object_name, self.operation,
                self.scaling]

    def visible_settings(self):
        result = [self.object_name, self.output_object_name, self.operation]
        # if self.operation in (O_SHRINK, O_EXPAND, O_SPUR):
        #     result += [self.iterations]
        # if self.operation in (O_SHRINK, O_SHRINK_INF):
        #     result += [self.wants_fill_holes]
        result += [self.scaling]
        # if self.wants_outlines.value:
        #     result += [self.outlines_name]
        return result

    def run(self, workspace):
        input_objects = workspace.object_set.get_objects(self.object_name.value)
        output_objects = cpo.Objects()
        output_objects.segmented = self.do_labels(input_objects.segmented)
        if (input_objects.has_small_removed_segmented):
            output_objects.small_removed_segmented = \
                self.do_labels(input_objects.small_removed_segmented)
        if (input_objects.has_unedited_segmented):
            output_objects.unedited_segmented = \
                self.do_labels(input_objects.unedited_segmented)
        workspace.object_set.add_objects(output_objects,
                                         self.output_object_name.value)
        add_object_count_measurements(workspace.measurements,
                                      self.output_object_name.value,
                                      np.max(output_objects.segmented))
        add_object_location_measurements(workspace.measurements,
                                         self.output_object_name.value,
                                         output_objects.segmented)

        if self.show_window:
            workspace.display_data.input_objects_segmented = input_objects.segmented
            workspace.display_data.output_objects_segmented = output_objects.segmented

    def display(self, workspace, figure):
        input_objects_segmented = workspace.display_data.input_objects_segmented
        output_objects_segmented = workspace.display_data.output_objects_segmented
        figure.set_subplots((2, 1))
        figure.subplot_imshow_labels(0, 0, input_objects_segmented,
                                     self.object_name.value)
        figure.subplot_imshow_labels(1, 0, output_objects_segmented,
                                     self.output_object_name.value)

    def _scale_labels(self, labels, scale):
        """
        Scales a label matrix
        :return: rescaled label matrix
        """

        trans_labs = transform.rescale(labels+1, scale=scale.value, preserve_range=True)

        trans_labs[(trans_labs %1) > 0] = 1
        trans_labs = np.round(trans_labs) - 1
        selem=disk(2)
        tmplabels_max = ndi.maximum_filter(trans_labs, size=2)
        tmplabels_min = -ndi.maximum_filter(-trans_labs, size=2)
        trans_labs[tmplabels_max != tmplabels_min] = 0

        return trans_labs


    def do_labels(self, labels):
        '''Run whatever transformation on the given labels matrix'''

        labels = self._scale_labels(labels=labels, scale=self.scaling)
        return labels

    def upgrade_settings(self, setting_values, variable_revision_number,
                         module_name, from_matlab):
        return setting_values, variable_revision_number, from_matlab

    def get_measurement_columns(self, pipeline):
        '''Return column definitions for measurements made by this module'''
        columns = get_object_measurement_columns(self.output_object_name.value)
        return columns

    def get_categories(self, pipeline, object_name):
        """Return the categories of measurements that this module produces

        object_name - return measurements made on this object (or 'Image' for image measurements)
        """
        categories = []
        if object_name == cpmeas.IMAGE:
            categories += ["Count"]
        if object_name == self.output_object_name:
            categories += ("Location", "Number")
        return categories

    def get_measurements(self, pipeline, object_name, category):
        """Return the measurements that this module produces

        object_name - return measurements made on this object (or 'Image' for image measurements)
        category - return measurements made in this category
        """
        result = []

        if object_name == cpmeas.IMAGE:
            if category == "Count":
                result += [self.output_object_name.value]
        if object_name == self.output_object_name:
            if category == "Location":
                result += ["Center_X", "Center_Y"]
            elif category == "Number":
                result += ["Object_Number"]
        return result
