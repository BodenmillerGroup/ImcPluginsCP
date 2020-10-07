import numpy as np
import pytest

import cellprofiler_core.image
import cellprofiler_core.measurement

import cellprofiler_core.modules.injectimage
import cellprofiler_core.object
import cellprofiler_core.pipeline
import cellprofiler_core.workspace
from cellprofiler_core.utilities.core import modules as cpmodules

IMAGE_NAME = "image"
OUTPUT_IMAGE = "outputimage"
OBJECT_NAME = "ObjectName"

IMAGE_SCALE = 2 ** 16 - 1

import plugins.masktobinstack as masktobinstack


@pytest.fixture(scope="function")
def image():
    return cellprofiler_core.image.Image(scale=IMAGE_SCALE)


@pytest.fixture(scope="function")
def objects(image):
    objects = cellprofiler_core.object.Objects()

    objects.parent_image = image

    return objects


@pytest.fixture(scope="function")
def measurements():
    return cellprofiler_core.measurement.Measurements()


@pytest.fixture(scope="function")
def module():
    module = masktobinstack.MaskToBinstack()
    module.image_name.value = IMAGE_NAME
    module.objects_name.value = OBJECT_NAME
    module.output_name.value = OUTPUT_IMAGE

    return module


@pytest.fixture(scope="function")
def workspace(image, measurements, module, objects):
    image_set_list = cellprofiler_core.image.ImageSetList()

    image_set = image_set_list.get_image_set(0)

    image_set.add(IMAGE_NAME, image)

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


def test_init():
    x = masktobinstack.MaskToBinstack()


@pytest.fixture(scope="function", params=["test1", "empty"])
def data(request):
    if request.param == "test1":
        data = np.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 0, 2, 2, 2, 0, 0],
                [0, 0, 2, 3, 2, 0, 0],
                [0, 0, 2, 2, 2, 0, 0],
                [1, 0, 0, 0, 0, 0, 0],
            ]
        )
    elif request.param == "empty":
        data = np.zeros((4, 4))

    return data


@pytest.fixture(
    scope="function", params=[masktobinstack.IF_IMAGE, masktobinstack.IF_OBJECTS]
)
def conf_module(request, data, image, objects, module):
    input_type = request.param
    module.input_type.value = input_type
    if input_type == masktobinstack.IF_IMAGE:
        image.pixel_data = data / IMAGE_SCALE
    else:
        objects.segmented = data.astype(int)
    return module


def test_maskimg_mid(data, conf_module, workspace):
    module = conf_module
    module.main_object_def.value = masktobinstack.SEL_MID

    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE).pixel_data

    np.testing.assert_equal(result[:, :, 0], data == 3)
    np.testing.assert_equal(result[:, :, 1], (data == 2) | (data == 1))
    np.testing.assert_equal(result[:, :, 2], data == 0)


def test_maskimg_max(data, conf_module, workspace):
    module = conf_module
    module.main_object_def.value = masktobinstack.SEL_MAXAREA

    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE).pixel_data

    np.testing.assert_equal(result[:, :, 0], data == 2)
    np.testing.assert_equal(result[:, :, 1], (data == 3) | (data == 1))
    np.testing.assert_equal(result[:, :, 2], data == 0)


def test_maskimg_provided(data, conf_module, workspace):
    module = conf_module
    module.main_object_def.value = masktobinstack.SEL_PROVIDED
    module.main_object_id.value = "1"

    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE).pixel_data

    np.testing.assert_equal(result[:, :, 0], data == 1)
    np.testing.assert_equal(result[:, :, 1], (data == 2) | (data == 3))
    np.testing.assert_equal(result[:, :, 2], data == 0)
