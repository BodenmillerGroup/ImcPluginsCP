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
OUTPUT_IMAGE_F = "outputimage%d"

import plugins.correctspilloverapply as correctspilloverapply


def test_init():
    x = correctspilloverapply.CorrectSpilloverApply()


@pytest.fixture(params=[correctspilloverapply.METHOD_LS,
                        correctspilloverapply.METHOD_NNLS])
def method(request):
    return request.param

def test_compensate_image_ls(method):
    img = np.array([[[1, 0.1], [0, 1], [1, 0.1]],
                         [[0, 1], [1, 0.1], [2, 0.2]]])
    sm = np.array([[1, 0.1], [0, 1]])
    expected = np.array([[[1., 0.],
                       [0., 1.],
                       [1., 0.]],
                      [[0., 1.],
                       [1., 0.],
                       [2., 0.]]])
    out = correctspilloverapply.CorrectSpilloverApply.compensate_image_ls(img, sm, method)

    np.testing.assert_array_almost_equal(out, expected)

