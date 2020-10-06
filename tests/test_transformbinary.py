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

import plugins.transformbinary as transformbinary


def test_init():
    x = transformbinary.TransformBinary()


@pytest.fixture(scope="function")
def image():
    return cellprofiler_core.image.Image()


@pytest.fixture(scope="function")
def measurements():
    return cellprofiler_core.measurement.Measurements()


@pytest.fixture(scope="function")
def module():
    module = transformbinary.TransformBinary()
    module.image_name.value = IMAGE_NAME
    module.transformed_image_name.value = OUTPUT_IMAGE

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


def test_transform(image, measurements, module, workspace):
    img = [[0, 0, 0], [0, 1.0, 0], [0, 0, 0]]
    sqrt_2 = np.sqrt(2)
    expected = [[-sqrt_2, -1, -sqrt_2], [-1, 1, -1], [-sqrt_2, -1, -sqrt_2]]

    image.pixel_data = img

    module.run(workspace)

    result = workspace.image_set.get_image(OUTPUT_IMAGE).pixel_data

    np.testing.assert_array_almost_equal(result, expected)


def test_transform_2(image, measurements, module, workspace):
    img = [[0.5, 0.2, 0.7], [1, 0, 0.5], [0.1, 0.2, 0.3]]
    sqrt_2 = np.sqrt(2)
    expected = [[sqrt_2, 1, sqrt_2], [1, -1, 1], [sqrt_2, 1, sqrt_2]]

    image.pixel_data = img

    module.run(workspace)

    result = workspace.image_set.get_image(OUTPUT_IMAGE).pixel_data

    np.testing.assert_array_almost_equal(result, expected)

def test_transform_3(image, measurements, module, workspace):
    img = [[1, 0, 1], [0, 0, 0.], [1, 0, 1]]
    sqrt_2 = np.sqrt(2)
    expected = [[1, -1, 1], [-1, -sqrt_2, -1], [1, -1, 1]]

    image.pixel_data = img

    module.run(workspace)

    result = workspace.image_set.get_image(OUTPUT_IMAGE).pixel_data

    np.testing.assert_array_almost_equal(result, expected)
