import numpy
import pytest
import io

import cellprofiler_core.image
import cellprofiler_core.measurement

import cellprofiler_core.modules.injectimage
import cellprofiler_core.object
import cellprofiler_core.pipeline
import cellprofiler_core.workspace
from cellprofiler_core.utilities.core import modules as cpmodules

IMAGE_NAME = "image"
OUTPUT_IMAGE_F = "outputimage%d"

import plugins.exportvarcsv as exportvarcsv


def test_init():
    x = exportvarcsv.ExportVarCsv()


def test_addgroup():
    exportvarcsv.ExportVarCsv().add_image_meta()
