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

-  data_type: datatype of feature

-  channel_id: additional identifier for color plane (provided via additional
    file)

"""

import csv
import os
import re

import cellprofiler_core.module as cpm
from cellprofiler_core.constants.measurement import (
    EXPERIMENT,
    IMAGE,
)
from cellprofiler_core.constants.module import (
    IO_FOLDER_CHOICE_HELP_TEXT,
    IO_WITH_METADATA_HELP_TEXT,
)
from cellprofiler_core.preferences import ABSOLUTE_FOLDER_NAME
from cellprofiler_core.preferences import DEFAULT_INPUT_FOLDER_NAME
from cellprofiler_core.preferences import DEFAULT_INPUT_SUBFOLDER_NAME
from cellprofiler_core.preferences import DEFAULT_OUTPUT_FOLDER_NAME
from cellprofiler_core.preferences import DEFAULT_OUTPUT_SUBFOLDER_NAME
from cellprofiler_core.setting import Binary, Divider, SettingsGroup, HiddenCount
from cellprofiler_core.setting import ValidationError
from cellprofiler_core.setting.do_something import DoSomething
from cellprofiler_core.setting.do_something import RemoveSettingButton
from cellprofiler_core.setting.subscriber import ImageListSubscriber
from cellprofiler_core.setting.text import Text, Filename, Directory

"""The caption for the image set number"""
IMAGE_NUMBER = "ImageNumber"

OBJECT_NUMBER = "ObjectNumber"
OBJECT_RELATIONSHIPS = "Object relationships"

"""Output columns"""
COLUMN_NAME = "column_name"
CATEGORY = "category"
IMAGE_NAME = "image_name"
OBJECT_NAME = "object_name"
FEATURE_NAME = "feature_name"
CHANNEL = "channel"
PARAMETERS = "parameters"
DATATYPE = "data_type"
CHANNEL_ID = "channel_id"

"""Output format"""
DELEMITER = ","
EXTENSION = ".csv"

"""Settings offsets"""
IDX_IMAGE_META_COUNT = 4


class ExportVarCsv(cpm.Module):
    module_name = "ExportVarCsv"
    variable_revision_number = 1
    category = ["ImcPluginsCP", "File Processing"]

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
            "var_",
            doc="""\
                The text you enter here is prepended to the names of each file produced by
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

        self.image_metas = []

        self.image_meta_count = HiddenCount(self.image_metas, "Extraction method count")

        self.add_image_meta_method_button = DoSomething(
            "",
            "Add image channel identifiers",
            self.add_image_meta,
            doc=f"""\
                This allows to add a '{CHANNEL_ID}' to the output that
                should be a unique identifier for the image plane (e.g. 
                fluophor, waveflength or metal name for mass cytometry).
                The annotation should be provided with a text file without
                header that has the an id on each new-line.
                """,
        )

    def add_image_meta(self, can_remove=True):
        group = SettingsGroup()

        if can_remove:
            group.append("divider", Divider())

        group.append(
            "input_image_names",
            ImageListSubscriber(
                "Select Images where this channel identifier applies",
                "None",
                doc="""\
                    The image that this channel identifier belongs to.
                    """,
            ),
        )
        group.append(
            "csv_location",
            Directory(
                "Metadata file location",
                support_urls=True,
                doc="""\
                    Location for a txt file without header
                    that contains on each new line a channel identifier for a 
                    multichannel image.
                    Must have exactly the same number of rows than
                    the multichannel image has channels.
                    """,
            ),
        )

        group.append(
            "csv_filename",
            Filename(
                "Metadata file name",
                "None",
                browse_msg="Choose txt/csv file",
                exts=[("Data file (*.csv)", "*.csv"), ("Data file (*.txt)", "*.txt")],
                doc="Provide the file name of the CSV file containing the metadata you want to load.",
                get_directory_fn=group.csv_location.get_absolute_path,
                set_directory_fn=lambda path: group.csv_location.join_parts(
                    *group.csv_location.get_parts_from_path(path)
                ),
            ),
        )
        if can_remove:
            group.append(
                "remover",
                RemoveSettingButton(
                    "", "Remove this image_meta", self.image_metas, group
                ),
            )
        self.image_metas.append(group)

    def visible_settings(self):
        """Return the settings as seen by the user"""
        result = [self.directory, self.wants_prefix]
        if self.wants_prefix:
            result += [self.prefix]

        for group in self.image_metas:
            result += [
                group.divider,
                group.input_image_names,
                group.csv_location,
                group.csv_filename,
                group.remover,
            ]
        result += [
            # self.wants_overwrite_without_warning,
            self.add_image_meta_method_button
        ]

        return result

    def settings(self):
        """Return the settings in the order used when storing """
        result = [
            self.directory,
            self.wants_prefix,
            self.prefix,
            self.wants_overwrite_without_warning,
            self.image_meta_count,
        ]
        for group in self.image_metas:
            result += [group.input_image_names, group.csv_location, group.csv_filename]
        return result

    def prepare_settings(self, setting_values):
        n_image_metas = int(setting_values[IDX_IMAGE_META_COUNT])
        if len(self.image_metas) > n_image_metas:
            del self.image_metas[n_image_metas:]
        while len(self.image_metas) < n_image_metas:
            self.add_image_meta()

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
            self.run_object(object_name, workspace, self.image_metas)

    def run_object(self, object_name, workspace, image_meta_groups):
        """Create a file (or files if there's metadata) based on the object names
        object_names - a sequence of object names (or Image or Experiment)
                       which tell us which objects get piled into each file
        workspace - get the images from here.
        settings_group - if present, use the settings group for naming.
        """
        if object_name in [EXPERIMENT, IMAGE, OBJECT_RELATIONSHIPS]:
            return
        self.save_var_file(
            object_name,
            workspace,
            image_meta_groups,
        )

    @staticmethod
    def get_var_meta(object_name, workspace):
        columns = [c[:3] for c in workspace.pipeline.get_measurement_columns()]

        features = [
            (col_object, feature, coltype)
            for col_object, feature, coltype in columns
            if col_object == object_name
        ]

        feature_meta = [
            {**DEFAULT_VARMETA, **parse_column_name(feature), DATATYPE: coltype}
            for col_object, feature, coltype in features
        ]

        return feature_meta

    def get_channel_annotations(self, image_meta_groups):
        annotation_dict = {}
        for group in image_meta_groups:
            fn = self.csv_path(group)
            annotations = []
            with open(fn, "r") as f:
                annotations = f.read().split("\n")
            for img in group.input_image_names.value:
                annotation_dict[img] = annotations
        return annotation_dict

    def add_channel_annotations(self, feature_meta, channel_annotations):
        for meta in feature_meta:
            image_name = meta[IMAGE_NAME]
            annotation = channel_annotations.get(image_name, None)
            if annotation is None:
                continue
            channel_nr = meta["channel"]
            if channel_nr is not None:
                meta["channel_id"] = annotation[int(channel_nr) - 1]

    def save_var_file(self, object_name, workspace, image_meta_groups):
        """Make a file containing object measurements
        object_names - sequence of names of the objects whose measurements
                       will be included
        image_set_numbers -  the image sets whose data gets extracted
        workspace - workspace containing the measurements
        settings_group - the settings group used to choose to make the file or
                         None if wants_everything
        """

        file_name = self.make_objects_file_name(object_name, workspace)

        feature_meta = self.get_var_meta(object_name, workspace)

        if len(image_meta_groups) > 0:
            image_meta = self.get_channel_annotations(image_meta_groups)
            self.add_channel_annotations(feature_meta, image_meta)

        fd = open(file_name, "w", newline="", encoding="utf-8")
        try:
            writer = csv.writer(fd, delimiter=DELEMITER)
            # Write the header
            writer.writerow([x for x in feature_meta[0].keys()])
            for row in feature_meta:
                writer.writerow(row.values())
        finally:
            fd.close()

    def make_objects_file_name(self, object_name, workspace):
        """Concoct the .CSV filename for some object category
        :param object_name: name of the objects whose measurements are to be
                            saved (or IMAGES or EXPERIMENT)
        :param workspace: the current workspace
        """
        filename = "%s.%s" % (object_name, "csv")
        filename = self.make_full_filename(filename, workspace)
        return filename

    def make_full_filename(self, file_name, workspace=None, image_set_number=None):
        """Convert a file name into an absolute path
        We do a few things here:
        * change the relative path into an absolute one using the "." and "&"
          convention
        * Create any directories along the path
        """
        measurements = None if workspace is None else workspace.measurements
        path_name = self.directory.get_absolute_path(measurements, image_set_number)
        if self.wants_prefix:
            prefix = self.prefix.value
        else:
            prefix = "var_"
        file_name = prefix + file_name
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

    @staticmethod
    def csv_path(group):
        return os.path.join(
            group.csv_location.get_absolute_path(), group.csv_filename.value
        )

    def upgrade_settings(self, setting_values, variable_revision_number, module_name):
        """Adjust the setting values based on the version that saved them"""
        return setting_values, variable_revision_number


def parse_intensity_col(col):
    re_exp = (
        f"(?P<{CATEGORY}>[a-zA-Z0-9]+)_"
        f"(?P<{FEATURE_NAME}>[a-zA-Z0-9]+(_[XYZ]+)?)"
        f"(_(?P<{IMAGE_NAME}>[a-zA-Z0-9]+))?"
        f"(_(?P<{PARAMETERS}>[0-9of_]+))?"
        f"(_c(?P<{CHANNEL}>[0-9]+))?"
    )
    return {COLUMN_NAME: col, **re.match(re_exp, col).groupdict()}


def parse_areashape_col(col):
    re_exp = f"(?P<{CATEGORY}>[a-zA-Z0-9]+)_" f"(?P<{FEATURE_NAME}>.*)"
    return {COLUMN_NAME: col, **re.match(re_exp, col).groupdict()}


def parse_id_col(col):
    return {COLUMN_NAME: col, CATEGORY: "ID", FEATURE_NAME: col}


def parse_neighbors_col(col):
    re_exp = (
        f"(?P<{CATEGORY}>[a-zA-Z0-9]+)_"
        f"(?P<{FEATURE_NAME}>[a-zA-Z0-9]+)"
        f"(_(?P<{PARAMETERS}>[0-9_]+))?"
    )
    outdict = {COLUMN_NAME: col, **re.match(re_exp, col).groupdict()}
    return outdict


def parse_parent_col(col):
    re_exp = (
        f"(?P<{CATEGORY}>[a-zA-Z0-9]+)"
        f"_(?P<{OBJECT_NAME}>[a-zA-Z0-9]+)"
        f"(_(?P<{FEATURE_NAME}>[a-zA-Z0-9]+))?"
        f"(_(?P<{PARAMETERS}>[0-9_]+))?"
    )
    outdict = {COLUMN_NAME: col, **re.match(re_exp, col).groupdict()}

    if outdict[FEATURE_NAME] is None:
        outdict[FEATURE_NAME] = outdict[CATEGORY]
    return outdict


def parse_distance_col(col):
    re_exp = (
        f"(?P<{CATEGORY}>[a-zA-Z0-9]+)_"
        f"(?P<{FEATURE_NAME}>[a-zA-Z0-9]+)"
        f"_(?P<{OBJECT_NAME}>[a-zA-Z0-9]+)"
        f"(_(?P<{PARAMETERS}>[0-9_]+))?"
    )
    outdict = {COLUMN_NAME: col, **re.match(re_exp, col).groupdict()}
    return outdict


category_parsers = {
    k: fkt
    for ks, fkt in [
        [
            (
                "Intensity",
                "Granularity",
                "RadialDistribution",
                "AreaOccupied",
                "Location",
                "Texture",
            ),
            parse_intensity_col,
        ],
        [("ObjectNumber", "ImageNumber", "Number"), parse_id_col],
        [("AreaShape", "Math"), parse_areashape_col],
        [["Neighbors"], parse_neighbors_col],
        [["Children", "Parent"], parse_parent_col],
        [["Distance"], parse_distance_col],
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
    'image_name': Image name of measured image
    'object_name': object name of additionally measured object
    'channel': numeric, 1 if no channels
    'parameters': other measurement parameters
    }
    """
    category = column_name.split("_")[0]
    fkt = category_parsers.get(category, parse_intensity_col)
    return fkt(column_name)


DEFAULT_VARMETA = {
    COLUMN_NAME: None,
    CATEGORY: None,
    IMAGE_NAME: None,
    OBJECT_NAME: None,
    FEATURE_NAME: None,
    CHANNEL: None,
    PARAMETERS: None,
    CHANNEL_ID: None,
}
