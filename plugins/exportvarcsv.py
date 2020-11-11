"""\
Export Var CSV
==============

This modules exports for each object a csv file containing metadata
for each measurement column in the object table.
This should greatly facilitate converting Cellprofiler output into
an anndata or SingleCellExperiment.

The columns are:

-  column_name: the column name in the object measurements

-  category: Feature category

-  image_name: Name of image used to calculate this feature

-  object_name: Name of addiitonal object used for this feature

-  feature_name: Name of calculated feature

-  channel: color plane in image used to calculate this feature

-  parameters: Additional parameters used to calculate this feature
   (meaning dependes on feature e.g. often scale, number of pixels,...)

-  datatype: datatype of feature

"""

import base64
import csv
import logging
import os
import re

import cellprofiler_core.module as cpm
import cellprofiler_core.setting as cps

from cellprofiler_core.constants.measurement import (
    EXPERIMENT,
    IMAGE,
    AGG_STD_DEV,
    C_PATH_NAME,
    R_SECOND_IMAGE_NUMBER,
    R_FIRST_OBJECT_NUMBER,
)
from cellprofiler_core.constants.module import (
    IO_FOLDER_CHOICE_HELP_TEXT,
    IO_WITH_METADATA_HELP_TEXT,
)
from cellprofiler_core.constants.pipeline import EXIT_STATUS
from cellprofiler_core.module import Module
from cellprofiler_core.preferences import ABSOLUTE_FOLDER_NAME
from cellprofiler_core.preferences import DEFAULT_INPUT_FOLDER_NAME
from cellprofiler_core.preferences import DEFAULT_INPUT_SUBFOLDER_NAME
from cellprofiler_core.preferences import DEFAULT_OUTPUT_FOLDER_NAME
from cellprofiler_core.preferences import DEFAULT_OUTPUT_SUBFOLDER_NAME
from cellprofiler_core.setting import Binary
from cellprofiler_core.setting import ValidationError
from cellprofiler_core.setting.text import Directory, Text

"""The caption for the image set number"""
IMAGE_NUMBER = "ImageNumber"

"""The caption for the object # within an image set"""
OBJECT_NUMBER = "ObjectNumber"

OBJECT_RELATIONSHIPS = "Object relationships"

DELEMITER = ','
EXTENSION = '.csv'

class ExportVarCsv(cpm.Module):
    module_name = 'ExportVarCsv'
    variable_revision_number = 1
    category = ['ImcPluginsCP', 'File Processing']

    def create_settings(self):
        self.directory = Directory(
            "Output file location",
            dir_choices=[
                ABSOLUTE_FOLDER_NAME,
                DEFAULT_OUTPUT_FOLDER_NAME,
                DEFAULT_OUTPUT_SUBFOLDER_NAME,
                DEFAULT_INPUT_FOLDER_NAME,
                DEFAULT_INPUT_SUBFOLDER_NAME,
            ],
            doc="""\
        This setting lets you choose the folder for the output files. {folder_choice}
        {metadata_help}
        """.format(
                folder_choice=IO_FOLDER_CHOICE_HELP_TEXT,
                metadata_help=IO_WITH_METADATA_HELP_TEXT,
            ),
        )
        self.directory.dir_choice = DEFAULT_OUTPUT_FOLDER_NAME

        self.wants_prefix = Binary(
            "Add a prefix to file names?",
            True,
            doc="""\
        This setting lets you choose whether or not to add a prefix to each of
        the .CSV filenames produced by **ExportToSpreadsheet**. A prefix may be
        useful if you use the same directory for the results of more than one
        pipeline; you can specify a different prefix in each pipeline. Select
        *"Yes"* to add a prefix to each file name (e.g., “MyExpt\_Images.csv”).
        Select *"No"* to use filenames without prefixes (e.g., “Images.csv”).
                    """
                % globals(),
        )

        self.prefix = Text(
            "Filename prefix",
            "MyExpt_",
            doc="""\
        (*Used only if “Add a prefix to file names?” is "Yes"*)
        The text you enter here is prepended to the names of each file produced by
        **ExportToSpreadsheet**.
                    """
                % globals(),
        )

        self.wants_overwrite_without_warning = Binary(
            "Overwrite existing files without warning?",
            False,
            doc="""\
        This setting either prevents or allows overwriting of old .CSV files by
        **ExportToSpreadsheet** without confirmation. Select *"Yes"* to
        overwrite without warning any .CSV file that already exists. Select
        *"No"* to prompt before overwriting when running CellProfiler in the
        GUI and to fail when running headless."""
                % globals(),
        )

    def visible_settings(self):
        """Return the settings as seen by the user"""
        result = [self.directory, self.wants_prefix]
        if self.wants_prefix:
            result += [self.prefix]

        result += [
            self.wants_overwrite_without_warning
        ]

        return result

    def settings(self):
        """Return the settings in the order used when storing """
        result = [
            self.directory,
            self.wants_prefix,
            self.prefix,
            self.wants_overwrite_without_warning
        ]
        return result

    def validate_module_warnings(self, pipeline):
        """Warn user re: Test mode """
        if pipeline.test_mode:
            raise ValidationError(
                "ExportToSpreadsheet will not produce output in Test Mode",
                self.directory,
            )

    def prepare_run(self, workspace):
        return self.check_overwrite(workspace)

    def run(self, workspace):
        """
        All work is done in post_run()
        """
        pass

    def display(self, workspace, figure):
        figure.set_subplots((1, 1))
        if workspace.display_data.columns is None:
            figure.subplot_table(0, 0, [["Data written to spreadsheet"]])
        elif workspace.pipeline.test_mode:
            figure.subplot_table(
                0, 0, [["Data not written to spreadsheets in test mode"]]
            )
        else:
            figure.subplot_table(
                0,
                0,
                workspace.display_data.columns,
                col_labels=workspace.display_data.header,
            )

    def post_run(self, workspace):
        """Save measurements at end of run"""
        #
        # Don't export in test mode
        #

        if workspace.pipeline.test_mode:
            return
        #
        # Signal "display" that we are post_run
        #
        workspace.display_data.columns = None
        workspace.display_data.header = None
        #
        # Export all measurements if requested
        #
        for object_name in workspace.measurements.get_object_names():
            self.run_object(object_name, workspace)

    def run_object(self, object_name, workspace, settings_group=None):
        """Create a file (or files if there's metadata) based on the object names
        object_names - a sequence of object names (or Image or Experiment)
                       which tell us which objects get piled into each file
        workspace - get the images from here.
        settings_group - if present, use the settings group for naming.
        """
        if object_name in [
            EXPERIMENT,
            IMAGE,
            OBJECT_RELATIONSHIPS
        ]:
            return
        self.save_var_file(
            object_name,
            workspace,
            settings_group,
        )

    @staticmethod
    def get_var_meta(object_name, workspace):
        columns = [c[:3] for c in
            workspace.pipeline.get_measurement_columns()]

        features = [
            (col_object, feature, coltype)
            for col_object, feature, coltype in columns
            if col_object == object_name
        ]

        feature_meta = [{**DEFAULT_VARMETA,
                         **parse_column_name(feature),
                         'datatype': coltype}
            for col_object, feature, coltype in features
        ]

        return feature_meta

    def save_var_file(self, object_name, workspace, settings_group):
        """Make a file containing object measurements
        object_names - sequence of names of the objects whose measurements
                       will be included
        image_set_numbers -  the image sets whose data gets extracted
        workspace - workspace containing the measurements
        settings_group - the settings group used to choose to make the file or
                         None if wants_everything
        """

        file_name = self.make_objects_file_name(
            object_name, workspace
        )

        feature_meta = self.get_var_meta(object_name, workspace)
        fd = open(file_name, "w", newline="", encoding='utf-8')
        try:
            writer = csv.writer(fd, delimiter=DELEMITER)
            # Write the header
            writer.writerow([x for x in feature_meta[0].keys()])
            for row in feature_meta:
                writer.writerow(row.values())
        finally:
            fd.close()

    def make_objects_file_name(
        self, object_name, workspace
    ):
        """Concoct the .CSV filename for some object category
        :param object_name: name of the objects whose measurements are to be
                            saved (or IMAGES or EXPERIMENT)
        :param workspace: the current workspace
        """
        filename = "var_%s.%s" % (object_name, 'csv')
        filename = self.make_full_filename(filename, workspace)
        return filename

    def make_full_filename(self, file_name, workspace=None,
                           image_set_number=None):
        """Convert a file name into an absolute path
        We do a few things here:
        * change the relative path into an absolute one using the "." and "&"
          convention
        * Create any directories along the path
        """
        measurements = None if workspace is None else workspace.measurements
        path_name = self.directory.get_absolute_path(measurements,
                                                     image_set_number)
        if self.wants_prefix:
            file_name = self.prefix.value + file_name
        file_name = os.path.join(path_name, file_name)
        path, file = os.path.split(file_name)
        if not os.path.isdir(path):
            os.makedirs(path)
        return os.path.join(path, file)

    def check_overwrite(self, workspace):
        """
        TODO: implement
        """
        return True

    def upgrade_settings(self, setting_values, variable_revision_number,
                         module_name):
        """Adjust the setting values based on the version that saved them
        """
        return setting_values, variable_revision_number



def parse_intensity_col(col):
    re_exp = ('(?P<category>[a-zA-Z0-9]+)_'
              '(?P<feature_name>[a-zA-Z0-9]+(_[XYZ]+)?)'
              '(_(?P<image_name>[a-zA-Z0-9]+))?'
              '(_(?P<parameters>[0-9of]+))?'
              '(_c(?P<channel>[0-9]+))?')
    return {'column_name': col, **re.match(re_exp, col).groupdict()}

def parse_areashape_col(col):
    re_exp = ('(?P<category>[a-zA-Z0-9]+)_'
              '(?P<feature_name>.*)')
    return {'column_name': col, **re.match(re_exp, col).groupdict()}

def parse_id_col(col):
    return {'column_name': col, 'category': 'ID', 'feature_name': col}

def parse_neighbors_col(col):
    re_exp = ('(?P<category>[a-zA-Z0-9]+)_'
              '(?P<feature_name>[a-zA-Z0-9]+)'
              '(_(?P<parameters>[0-9_]+))?')
    outdict = {'column_name': col,
            **re.match(re_exp, col).groupdict()}
    return outdict

def parse_parent_col(col):
    re_exp = ('(?P<category>[a-zA-Z0-9]+)'
              '_(?P<object_name>[a-zA-Z0-9]+)'
              '(_(?P<feature_name>[a-zA-Z0-9]+))?'
              '(_(?P<parameters>[0-9_]+))?')
    outdict = {'column_name': col,
               **re.match(re_exp, col).groupdict()}

    if outdict['feature_name'] is None:
        outdict['feature_name'] = outdict['category']
    return outdict

def parse_distance_col(col):
    re_exp = ('(?P<category>[a-zA-Z0-9]+)_'
              '(?P<feature_name>[a-zA-Z0-9]+)'
              '_(?P<object_name>[a-zA-Z0-9]+)'
             '(_(?P<parameters>[0-9_]+))?')
    outdict = {'column_name': col,
            **re.match(re_exp, col).groupdict()}
    return outdict

category_parsers = {k: fkt for ks, fkt in
                        [[('Intensity', 'Granulairty',
                        'RadialDistribution', 'AreaOccupied',
                        'Location', 'Texture'), parse_intensity_col],
                       [('ObjectNumber', 'ImageNumber', 'Number'), parse_id_col],
                        [ ('AreaShape', 'Math'),
                          parse_areashape_col],
                        [['Neighbors'], parse_neighbors_col],
                        [['Children', 'Parent'], parse_parent_col],
                        [['Distance'], parse_distance_col]

                          ]
                        for k in ks
                        }

def parse_column_name(column_name):
    """
    Cellprofiler nomenclature: MeasurementType_Category_Specificfeature_name_Parameters
    http://cellprofiler-manual.s3.amazonaws.com/CellProfiler-3.0.0/help/output_measurements.html

    Parses a Cellprofiler column name into a dictionary containing:
    {
    'column_name': the original column name,
    'category': the measurement category: Intensity, AreaShape, ...
    'feature_name': The 'Specificfeature_name' measured: MeanIntensity,
    MaxIntensity, ...
    'channel': numeric, 1 if no channels
    'parameters': other measurement parameters
    }

    column_name classes:
    - ObjectNumber, ImageNumber: special, only column_name will be filed
    - AreaShape, Math, Location: have format: CATEGORY_SPECIFICfeature_name
        -> SPECIFICfeature_name can also contain '_'
    - Intensity, Granularity, Children, RadialDistribution, Parent,
    AreaOccupied:
        Have format: CATEGORY_SPECIFICfeature_name(_image_name)(_cCHANNEL)
    - Neighbors and Texture:
        Have format: CATEGORY_SPECIFICFEATUERNAME_PARAMETERS
        (PARAMETERS can be more than one, _ separated)
    - Texture & RadialDistribution:
        CATEGORY_SPECIFICfeature_name_image_name_PARAMETERS

    """
    category = column_name.split('_')[0]
    fkt = category_parsers.get(category, parse_intensity_col)
    return fkt(column_name)

DEFAULT_VARMETA = {
               'column_name': '',
               'category': '',
               'image_name': '',
               'object_name': '',
               'feature_name': '',
               'channel': '',
               'parameters': ''
               }