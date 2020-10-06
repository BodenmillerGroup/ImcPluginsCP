import numpy as np
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
SM_IMAGE_NAME = "smimage"
OUTPUT_IMAGE_F = "outputimage%d"
MEASUREMENT_NAME = 'testmeasurement'
OBJECT_NAME = 'tstobject'
COMP_SUFFIX = 'Comp'

N_CHANNEL = 2


import plugins.correctspillovermeasurements as correctspillovermeasurements
import plugins.measureobjectintensitymultichannel as moimc


@pytest.fixture(scope="function")
def module():
    module = correctspillovermeasurements.CorrectSpilloverMeasurements()
    cpm = module.compmeasurements[0]
    cpm.object_name.value = OBJECT_NAME
    cpm.compmeasurement_name.value = MEASUREMENT_NAME
    cpm.corrected_compmeasurement_suffix.value = COMP_SUFFIX
    cpm.spill_correct_function_image_name.value = SM_IMAGE_NAME
    return module

@pytest.fixture(scope="function")
def meas_module():
    module = moimc.MeasureObjectIntensityMultichannel()
    return module

@pytest.fixture(scope="function")
def image():
    return cellprofiler_core.image.Image()


@pytest.fixture(scope="function")
def sm_image():
    return cellprofiler_core.image.Image()

@pytest.fixture(scope="function")
def objects():
    return cellprofiler_core.object.Objects()

@pytest.fixture(scope="function")
def measurements():
    return cellprofiler_core.measurement.Measurements()


@pytest.fixture(scope="function")
def workspace(image, sm_image, objects, measurements, module,
              meas_module):
    image_set_list = cellprofiler_core.image.ImageSetList()

    image_set = image_set_list.get_image_set(0)

    image_set.add(IMAGE_NAME, image)
    image_set.add(SM_IMAGE_NAME, sm_image)

    object_set = cellprofiler_core.object.ObjectSet()
    object_set.add_objects(objects, OBJECT_NAME)

    return cellprofiler_core.workspace.Workspace(
        cellprofiler_core.pipeline.Pipeline(),
        module,
        image_set,
        object_set,
        measurements,
        image_set_list,
    )

def test_init(module):
    module

def test_compensation(sm_image, module, workspace):
    vals = list(zip(*[[1, 0.1], [0, 1], [1, 0.1], [0, 1], [1, 0.1], [0.5, 0.05]]))
    nchan = len(vals)
    m = workspace.measurements
    for i, v in enumerate(vals):
        m.add_measurement(OBJECT_NAME,
                          f"{MEASUREMENT_NAME}_c{i+1}",
                          v
                          )
    cpm = module.compmeasurements[0]

    sm_image.pixel_data = [[1, 0.1], [0, 1]]
    cpm.spill_correct_method.value = correctspillovermeasurements.METHOD_LS
    module.run(workspace)
    results = [m.get_measurement(OBJECT_NAME,
                                  f"{MEASUREMENT_NAME}{COMP_SUFFIX}_c{i+1}")
                for i in range(nchan)]
    expected = [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0],
                [0.0, 1.0], [1.0, 0.0], [0.5, 0.0]]
    np.testing.assert_almost_equal(results, list(zip(*expected)))