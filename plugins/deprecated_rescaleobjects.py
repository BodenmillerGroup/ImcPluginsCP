"""<b>Deprecated_RescaleObjects</b> rescale objects by a defined distance.
x"""

import numpy as np

from skimage import transform
from skimage.morphology import disk
import scipy.ndimage as ndi


import cellprofiler_core.module as cpm
import cellprofiler_core.measurement as cpmeas
import cellprofiler_core.object as cpo
import cellprofiler_core.setting as cps
from cellprofiler_core.utilities.core.module.identify import (
    add_object_count_measurements,
    add_object_location_measurements,
    get_object_measurement_columns,
)
from cellprofiler_core.setting import HTMLText

YES, NO = "Yes", "No"
O_UPSCALE = "Upscale objects with a scaling factor"
O_DOWNSCALE = "Downscale objects with a scaling factor"

O_ALL = [O_UPSCALE, O_DOWNSCALE]


DEPRECATION_STRING = """
                The RescaleObject module is deprecated as the
                functionality is now integrated in the official `ResizeObjects` module.\n
                Please MANUALLY migrate to the new module.\n
                Consider using the 'ExpandOrShrinkObjects' modules to recreate the border
                between objects after scaling them down (as it was done in the old module).\n
                This module will be removed with the next major ImcPluginsCP release!
                """


class Deprecated_RescaleObjects(cpm.Module):
    module_name = "Deprecated_RescaleObjects"
    category = "Deprecated"
    variable_revision_number = 1

    def create_settings(self):
        self.deprecation_warning = HTMLText(
            text="Deprecation Warning",
            content=DEPRECATION_STRING,
            doc=DEPRECATION_STRING,
        )
        self.object_name = cps.subscriber.LabelSubscriber(
            "Select the input objects",
            "None",
            doc="""
            Select the objects that you want to rescale.""",
        )

        self.output_object_name = cps.text.LabelName(
            "Name the output objects",
            "RescaledObject",
            doc="""
            Enter a name for the resulting objects.""",
        )

        self.operation = cps.choice.Choice(
            "Select the operation",
            O_ALL,
            doc="""
            Select the operation that you want to perform:
            <ul>
            <li><i>%(O_DOWNSCALE)s:</i> Downscale the Object Masks to a smaller image size.</li>
            <li><i>%(O_UPSCALE)s:</i> Expand objects, assigning every pixel in the image to an
            object. Background pixels are assigned to the nearest object.</li>
            </ul>"""
            % globals(),
        )

        self.scaling = cps.text.Float("Factor to scale the object mask", 1, minval=0)

    def settings(self):
        return [self.object_name, self.output_object_name, self.operation, self.scaling]

    def visible_settings(self):
        result = [
            self.deprecation_warning,
            self.object_name,
            self.output_object_name,
            self.operation,
        ]
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
        if input_objects.has_small_removed_segmented:
            output_objects.small_removed_segmented = self.do_labels(
                input_objects.small_removed_segmented
            )
        if input_objects.has_unedited_segmented:
            output_objects.unedited_segmented = self.do_labels(
                input_objects.unedited_segmented
            )
        workspace.object_set.add_objects(output_objects, self.output_object_name.value)
        add_object_count_measurements(
            workspace.measurements,
            self.output_object_name.value,
            np.max(output_objects.segmented),
        )
        add_object_location_measurements(
            workspace.measurements,
            self.output_object_name.value,
            output_objects.segmented,
        )

        if self.show_window:
            workspace.display_data.input_objects_segmented = input_objects.segmented
            workspace.display_data.output_objects_segmented = output_objects.segmented

    def display(self, workspace, figure):
        input_objects_segmented = workspace.display_data.input_objects_segmented
        output_objects_segmented = workspace.display_data.output_objects_segmented
        figure.set_subplots((2, 1))
        figure.subplot_imshow_labels(
            0, 0, input_objects_segmented, self.object_name.value
        )
        figure.subplot_imshow_labels(
            1, 0, output_objects_segmented, self.output_object_name.value
        )

    def _scale_labels(self, labels, scale):
        """
        Scales a label matrix
        :return: rescaled label matrix
        """

        trans_labs = transform.rescale(
            labels + 1, scale=scale.value, preserve_range=True
        )

        trans_labs[(trans_labs % 1) > 0] = 1
        trans_labs = np.round(trans_labs) - 1
        selem = disk(2)
        tmplabels_max = ndi.maximum_filter(trans_labs, size=2)
        tmplabels_min = -ndi.maximum_filter(-trans_labs, size=2)
        trans_labs[tmplabels_max != tmplabels_min] = 0

        return trans_labs

    def do_labels(self, labels):
        """Run whatever transformation on the given labels matrix"""

        labels = self._scale_labels(labels=labels, scale=self.scaling)
        return labels

    def upgrade_settings(self, setting_values, variable_revision_number, module_name):
        return setting_values, variable_revision_number

    def get_measurement_columns(self, pipeline):
        """Return column definitions for measurements made by this module"""
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
