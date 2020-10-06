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
OUTPUT_IMAGE = "outputimage"

import plugins.summarizestack as summarizestack


def test_init():
    x = summarizestack.SummarizeStack()

@pytest.fixture(scope="function")
def image():
    return cellprofiler_core.image.Image()


@pytest.fixture(scope="function")
def measurements():
    return cellprofiler_core.measurement.Measurements()


@pytest.fixture(scope="function")
def module():
    module = summarizestack.SummarizeStack()
    module.image_name.value = IMAGE_NAME
    module.grayscale_name.value = OUTPUT_IMAGE

    return module

@pytest.fixture(scope="function")
def workspace(image, measurements, module):
    image_set_list = cellprofiler_core.image.ImageSetList()

    image_set = image_set_list.get_image_set(0)

    image_set.add(IMAGE_NAME, image)

    object_set = cellprofiler_core.object.ObjectSet()

    return cellprofiler_core.workspace.Workspace(
        cellprofiler_core.pipeline.Pipeline(),
        module,
        image_set,
        object_set,
        measurements,
        image_set_list,
    )

def test_mean(image, module, workspace):
    image_shape = (10, 10, 3)
    test_image = np.zeros(image_shape)
    test_image[:,:,0] = 0.3
    expected =  np.zeros(image_shape[:2])
    expected[:] = 0.1

    image.pixel_data = test_image

    module.conversion_method.value = summarizestack.MEAN

    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE)

    np.testing.assert_array_almost_equal(expected, result.pixel_data)


def test_median(image, module, workspace):
    image_shape = (10, 10, 3)
    test_image = np.zeros(image_shape)
    test_image[:,:,0] = 0.3
    test_image[:,:,1] = 0.1
    expected =  np.zeros(image_shape[:2])
    expected[:] = 0.1

    image.pixel_data = test_image

    module.conversion_method.value = summarizestack.MEDIAN

    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE)

    np.testing.assert_array_almost_equal(expected, result.pixel_data)


def test_custom_max(image, module, workspace):
    image_shape = (10, 10, 3)
    test_image = np.zeros(image_shape)
    test_image[:,:,0] = 0.3
    test_image[:,:,1] = 0.1
    expected =  np.zeros(image_shape[:2])
    expected[:] = 0.3

    image.pixel_data = test_image

    module.conversion_method.value = summarizestack.CUSTOMFUNCTION
    module.custom_function.value = "np.max"

    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE)

    np.testing.assert_array_almost_equal(expected, result.pixel_data)







