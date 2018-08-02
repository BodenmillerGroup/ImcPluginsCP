'''<b>CorrectSpillover - Apply</b> applies an spillover matrix, usually created by
the R Bioconductor package CATALYST to a multichannel measurement
<hr>

This module applies a previously calculate spillover matrix,
loaded by <b>LoadSingleImage</b> to single cell measurements.
'''

import numpy as np
import re
import scipy.optimize as spo

import cellprofiler.image  as cpi
import cellprofiler.module as cpm
import cellprofiler.setting as cps
import cellprofiler.measurement as cpmeas


SETTINGS_PER_IMAGE = 5
METHOD_LS = 'LeastSquares'
METHOD_NNLS = 'NonNegativeLeastSquares'

class PatchedMeasurementSetting(cps.Measurement):
    def __init__(self, *args, **kwargs):
        super(PatchedMeasurementSetting, self).__init__(*args, **kwargs)
    def test_valid(self, pipeline):
        pass

class CorrectSpilloverMeasurements(cpm.Module):
    category = "Measurement"
    variable_revision_number = 2
    module_name = "CorrectSpilloverMeasurements"

    def create_settings(self):
        """Make settings here (and set the module name)"""
        self.compmeasurements = []
        self.add_compmeasurement(can_delete = False)
        self.add_compmeasurement_button = cps.DoSomething("", "Add another measurement",
                                                self.add_compmeasurement)

    def add_compmeasurement(self, can_delete = True):
        '''Add an compmeasurement and its settings to the list of compmeasurements'''
        group = cps.SettingsGroup()

        object_name = cps.ObjectNameSubscriber('Select Object')

        compmeasurement_name = PatchedMeasurementSetting(
            'Select the measurment to correct for spillover',
            object_name.get_value, cps.NONE, doc=""" Select compmeasurement
            to be spillover corrected""")

        corrected_compmeasurement_suffix = cps.AlphanumericText(
            "Name the output compmeasurement suffix",
            "Corrected", doc = '''
            Enter a name for the corrected measurement.''')

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

        compmeasurement_settings = cps.SettingsGroup()
        compmeasurement_settings.append('object_name', object_name)
        compmeasurement_settings.append("compmeasurement_name", compmeasurement_name)
        compmeasurement_settings.append("corrected_compmeasurement_suffix", corrected_compmeasurement_suffix)
        compmeasurement_settings.append("spill_correct_function_image_name",
                              spill_correct_function_image_name)
        compmeasurement_settings.append("spill_correct_method", spill_correct_method)

        if can_delete:
            compmeasurement_settings.append("remover",
                                  cps.RemoveSettingButton("","Remove this measurement",
                                                          self.compmeasurements,
                                                          compmeasurement_settings))
        compmeasurement_settings.append("divider",cps.Divider())
        self.compmeasurements.append(compmeasurement_settings)

    def settings(self):
        """Return the settings to be loaded or saved to/from the pipeline

        These are the settings (from cellprofiler.settings) that are
        either read from the strings in the pipeline or written out
        to the pipeline. The settings should appear in a consistent
        order so they can be matched to the strings in the pipeline.
        """
        result = []
        for compmeasurement in self.compmeasurements:
            result += [compmeasurement.object_name,
                       compmeasurement.compmeasurement_name,
                       compmeasurement.corrected_compmeasurement_suffix,
                       compmeasurement.spill_correct_function_image_name,
                       compmeasurement.spill_correct_method
                      ]
        return result

    def visible_settings(self):
        """Return the list of displayed settings
        """
        result = []
        for compmeasurement in self.compmeasurements:
            result += [compmeasurement.object_name,
                       compmeasurement.compmeasurement_name,
                       compmeasurement.corrected_compmeasurement_suffix,
                       compmeasurement.spill_correct_function_image_name,
                       compmeasurement.spill_correct_method
                      ]
            #
            # Get the "remover" button if there is one
            #
            remover = getattr(compmeasurement, "remover", None)
            if remover is not None:
                result.append(remover)
            result.append(compmeasurement.divider)
        result.append(self.add_compmeasurement_button)
        return result

    def prepare_settings(self, setting_values):
        """Do any sort of adjustment to the settings required for the given values

        setting_values - the values for the settings

        This method allows a module to specialize itself according to
        the number of settings and their value. For instance, a module that
        takes a variable number of measurements or objects can increase or decrease
        the number of relevant settings so they map correctly to the values.
        """
        #
        # Figure out how many measurements there are based on the number of setting_values
        #
        assert len(setting_values) % SETTINGS_PER_IMAGE == 0
        compmeasurement_count = len(setting_values) / SETTINGS_PER_IMAGE
        del self.compmeasurements[compmeasurement_count:]
        while len(self.compmeasurements) < compmeasurement_count:
            self.add_compmeasurement()

    def _get_compmeasurement_columns(self, cm, pipeline):
        compmeasurement_name = cm.compmeasurement_name.value
        object_name = cm.object_name.value
        mods = [module for module in pipeline.modules()
                if module.module_num < self.module_num]
        cols = [col for m in mods for col in m.get_measurement_columns(pipeline)
                if (col[0] == object_name) and (
                    col[1].startswith(compmeasurement_name+'_c'))]
        return cols

    def _get_compmeasurment_output_columns(self, cm, pipeline):
        incols = self._get_compmeasurement_columns(cm, pipeline)
        suffix = cm.corrected_compmeasurement_suffix.value
        outcols = [(c[0], self._generate_outcolname(c[1], suffix), c[2])
                   for c in incols]
        return outcols

    def _generate_outcolname(self, colname, suffix):
        colfrag = colname.split('_')
        colfrag[1] += suffix
        outcol = '_'.join(colfrag)
        return outcol

    def get_measurement_columns(self, pipeline):
        '''Return column definitions for compmeasurements made rby this module'''
        columns = []
        for cm in self.compmeasurements:
            columns += self._get_compmeasurment_output_columns(cm, pipeline)
        return columns

    def get_categories(self, pipeline, object_name):
        for cm in self.compmeasurements:
            if object_name == self._get_obj(cm, pipeline):
                return ["Intensity"]
        return []

    def _get_obj(self, cm, pipeline):
        return cm.object_name.value

    def _get_featureout(self, cm, pipeline):
        outmeas = cm.compmeasurement_name.get_feature_name(pipeline)
        outmeas += cm.corrected_compmeasurement_suffix.value
        return outmeas

    def get_measurements(self, pipeline, object_name, category):
        results = []
        for cm in self.compmeasurements:
            if (object_name == self._get_obj(cm, pipeline)) and (
                category == 'Intensity'):
                results += [self._get_featureout(cm, pipeline)]
        return results

    def get_measurement_images(self, pipeline, object_name,
                               category, measurement):
        results = []
        for cm in self.compmeasurements:
            if (object_name == self._get_obj(cm, pipeline)) and (
                category == 'Intensity') and (
                measurement == self._get_featureout(cm, pipeline)):
                image_name = cm.compmeasurement_name.get_image_name(pipeline)
                results += [image_name]
        return results

    def run(self, workspace):
        """Run the module

        workspace    - The workspace contains
        pipeline     - instance of cpp for this run
        image_set    - the images in the image set being processed
        object_set   - the objects (labeled masks) in this image set
        measurements - the measurements for this run
        frame        - the parent frame to whatever frame is created. None means don't draw.
        """
        for compmeasurement in self.compmeasurements:
            self.run_compmeasurement(compmeasurement, workspace)


    def run_compmeasurement(self, compmeasurement, workspace):
        '''Perform spillover correction according to the parameters of e compmeasurement setting group

        '''
        # TODO: currently this relies on the channels being stored
        # in increasing order (which seems to be currently true). However
        # it would be clearly better to assert this channel order.
        #
        # Get the compmeasurement names from the settings
        #
        compmeasurement_name = compmeasurement.compmeasurement_name.value
        object_name = compmeasurement.object_name.value
        spill_correct_name = compmeasurement.spill_correct_function_image_name.value
        corrected_compmeasurement_suffix = compmeasurement.corrected_compmeasurement_suffix.value
        #
        # Get compmeasurements from workspace
        #
        measurements = workspace.get_measurements()
        pipline = workspace.pipeline

        m = [measurements.get_measurement(object_name, c[1])
             for c in self._get_compmeasurement_columns(compmeasurement, pipline)]
        data = np.stack(m).T

        spillover_mat = workspace.image_set.get_image(spill_correct_name)
        #
        # Either divide or subtract the illumination image from the original
        #
        method = compmeasurement.spill_correct_method.value
        compdat = self.compensate_dat(data,
                                              spillover_mat.pixel_data, method)
        # Save the output image in the image set and have it inherit
        # mask & cropping from the original image.
        #
        #
        # Save images for display
        #
        for m, c in zip(compdat.T, self._get_compmeasurment_output_columns(compmeasurement, pipline)):
            measurements.add_measurement(object_name, c[1], m)

    def compensate_dat(self, dat, sm, method):
        """
        Compensate by solving the linear system:
            comp * sm = dat -> comp = dat * inv(sm)

        """
        if method == METHOD_LS:
            compdat = np.linalg.lstsq(sm.T, dat.T)[0]
            compdat = compdat.T
        if method == METHOD_NNLS:
            nnls = lambda x: spo.nnls(sm.T, x)[0]
            compdat = np.apply_along_axis(nnls,1, dat)
        return compdat

    def display(self, workspace, figure):
        ''' Display one row of orig / illum / output per image setting group'''
        pass

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
        return setting_values, variable_revision_number, from_matlab
