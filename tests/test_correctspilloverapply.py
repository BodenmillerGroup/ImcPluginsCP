import numpy as np
import pytest
import io
from dataclasses import dataclass
from typing import List

import cellprofiler_core.image
import cellprofiler_core.measurement

import cellprofiler_core.modules.injectimage
import cellprofiler_core.object
import cellprofiler_core.pipeline
import cellprofiler_core.workspace
from cellprofiler_core.utilities.core import modules as cpmodules
import cellprofiler_core.setting as cps

IMAGE_NAME = "image"
SM_IMAGE_NAME = "sm"
OUTPUT_IMAGE = "outputimage"

import plugins.correctspilloverapply as correctspilloverapply


@pytest.fixture(scope="function")
def image():
    return cellprofiler_core.image.Image()


@pytest.fixture(scope="function")
def sm_image():
    return cellprofiler_core.image.Image()


@pytest.fixture(scope="function")
def measurements():
    return cellprofiler_core.measurement.Measurements()


@pytest.fixture(scope="function")
def module():
    module = correctspilloverapply.CorrectSpilloverApply()
    image_settings = module.images[0]
    image_settings.image_name.value = IMAGE_NAME
    image_settings.corrected_image_name.value = OUTPUT_IMAGE
    image_settings.spill_correct_function_image_name.value = SM_IMAGE_NAME
    return module


@pytest.fixture(scope="function")
def workspace(image, sm_image, measurements, module):
    image_set_list = cellprofiler_core.image.ImageSetList()

    image_set = image_set_list.get_image_set(0)

    image_set.add(IMAGE_NAME, image)
    image_set.add(SM_IMAGE_NAME, sm_image)

    object_set = cellprofiler_core.object.ObjectSet()

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


@pytest.fixture(
    params=[correctspilloverapply.METHOD_LS, correctspilloverapply.METHOD_NNLS]
)
def method(request):
    return request.param


@dataclass
class ExampleCase:
    """
    Simple testcase
    """

    name: str
    method: str
    img: np.ndarray
    sm: np.ndarray
    expected: np.ndarray


@pytest.fixture(params=["test_simple", "test_nnls", "test_zeros"])
def testcase(request, method):
    case = request.param
    if case == "test_simple":
        return ExampleCase(
            name=case,
            method=method,
            img=np.asarray(
                [[[1, 0.1], [0, 1], [1, 0.1]], [[0, 1], [1, 0.1], [0.5, 0.05]]]
            ),
            sm=np.asarray([[1, 0.1], [0, 1]]),
            expected=np.asarray(
                [
                    [[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]],
                    [[0.0, 1.0], [1.0, 0.0], [0.5, 0.0]],
                ]
            ),
        )
    elif case == "test_nnls":
        expected = np.asarray(
            [
                [[1.0, -0.1], [0.0, 0.0], [0.0, 0.0]],
                [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
            ]
        )
        if method == correctspilloverapply.METHOD_NNLS:
            expected[0, 0, 1] = 0
            expected[0, 0, 0] = 0.990099

        return ExampleCase(
            name=case,
            method=method,
            img=np.asarray([[[1, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0.0]]]),
            sm=np.asarray([[1, 0.1], [0, 1]]),
            expected=expected,
        )

    elif case == "test_zeros":
        return ExampleCase(
            name=case,
            method=method,
            img=np.asarray([[[0, 0], [0, 0], [0, 0]], [[0, 0], [0, 0], [0, 0.0]]]),
            sm=np.asarray([[1, 0.1], [0, 1]]),
            expected=np.asarray(
                [
                    [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
                    [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
                ]
            ),
        )
    else:
        raise ValueError(f'Unexpected testname "{case}"')


def test_compensate_image_ls(method):
    img = np.asarray([[[1, 0.1], [0, 1], [1, 0.1]], [[0, 1], [1, 0.1], [0.5, 0.05]]])
    sm = np.asarray([[1, 0.1], [0, 1]])
    expected = np.asarray(
        [[[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]], [[0.0, 1.0], [1.0, 0.0], [0.5, 0.0]]]
    )
    out = correctspilloverapply.CorrectSpilloverApply.compensate_image_ls(
        img, sm, method
    )

    np.testing.assert_array_almost_equal(out, expected)


def test_compensate_image(testcase, image, sm_image, module, workspace):
    image.pixel_data = testcase.img
    sm_image.pixel_data = testcase.sm
    image_settings = module.images[0]
    image_settings.spill_correct_method.value = testcase.method

    module.run(workspace)

    result = workspace.image_set.get_image(OUTPUT_IMAGE).pixel_data

    np.testing.assert_array_almost_equal(testcase.expected, result)
