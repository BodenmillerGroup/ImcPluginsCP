"""test_smoothmultichannel.py - test the smooth module
"""

import io

import numpy as np
from scipy.ndimage import gaussian_filter

import cellprofiler_core.preferences as cppref
import cellprofiler_core.workspace as cpw
import cellprofiler_core.image as cpi
import cellprofiler_core.object as cpo
import cellprofiler_core.pipeline as cpp
import cellprofiler_core.measurement as cpmeas
from cellprofiler_core.utilities.core import modules as cpmodules

from centrosome.smooth import fit_polynomial, smooth_with_function_and_mask
from centrosome.filter import median_filter, bilateral_filter
import skimage.restoration

from plugins import smoothmultichannel as S

INPUT_IMAGE_NAME = "myimage"
OUTPUT_IMAGE_NAME = "myfilteredimage"

cppref.set_headless()
# Initiate plugins and custom plugins
cpmodules.fill_modules()
cpmodules.add_module_for_tst(S.SmoothMultichannel)


def make_workspace(image, mask):
    """Make a workspace for testing FilterByObjectMeasurement"""
    module = S.SmoothMultichannel()
    pipeline = cpp.Pipeline()
    object_set = cpo.ObjectSet()
    image_set_list = cpi.ImageSetList()
    image_set = image_set_list.get_image_set(0)
    workspace = cpw.Workspace(
        pipeline, module, image_set, object_set, cpmeas.Measurements(), image_set_list
    )
    image_set.add(INPUT_IMAGE_NAME, cpi.Image(image, mask, scale=1))
    module.image_name.value = INPUT_IMAGE_NAME
    module.filtered_image_name.value = OUTPUT_IMAGE_NAME
    return workspace, module


def test_01_03_load_v02():
    data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
    Version:3
    DateRevision:20130522170932
    ModuleCount:1
    HasImagePlaneDetails:False

    Smooth Multichannel:[module_num:1|svn_version:\'Unknown\'|variable_revision_number:2|show_window:False|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True]
    Select the input image:InputImage
    Name the output image:OutputImage
    Select smoothing method:Median Filter
    Calculate artifact diameter automatically?:Yes
    Typical artifact diameter, in  pixels:19.0
    Edge intensity difference:0.2
    Clip intensity at 0 and 1:No

    """
    pipeline = cpp.Pipeline()
    cpmodules.fill_modules()
    cpmodules.add_module_for_tst(S.SmoothMultichannel)
    pipeline.load(io.StringIO(data))
    assert len(pipeline.modules()) == 1
    smooth = pipeline.modules()[0]
    assert isinstance(smooth, S.SmoothMultichannel)
    assert smooth.image_name == "InputImage"
    assert smooth.filtered_image_name == "OutputImage"
    assert smooth.wants_automatic_object_size
    assert smooth.object_size == 19
    assert smooth.smoothing_method == S.MEDIAN_FILTER
    assert not smooth.clip


def test_02_01_fit_polynomial():
    """Test the smooth module with polynomial fitting"""
    np.random.seed(0)
    #
    # Make an image that has a single sinusoidal cycle with different
    # phase in i and j. Make it a little out-of-bounds to start to test
    # clipping
    #
    i, j = np.mgrid[0:100, 0:100].astype(float) * np.pi / 50
    image = (np.sin(i) + np.cos(j)) / 1.8 + 0.9
    image += np.random.uniform(size=(100, 100)) * 0.1
    mask = np.ones(image.shape, bool)
    mask[40:60, 45:65] = False
    for clip in (False, True):
        expected = fit_polynomial(image, mask, clip)
        assert np.all((expected >= 0) & (expected <= 1)) == clip
        workspace, module = make_workspace(image, mask)
        module.smoothing_method.value = S.FIT_POLYNOMIAL
        module.clip.value = clip
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        assert result is not None
        np.testing.assert_almost_equal(result.pixel_data, expected)


def test_03_01_gaussian_auto_small():
    """Test the smooth module with Gaussian smoothing in automatic mode"""
    sigma = 100.0 / 40.0 / 2.35
    np.random.seed(0)
    image = np.random.uniform(size=(100, 100)).astype(np.float32)
    mask = np.ones(image.shape, bool)
    mask[40:60, 45:65] = False
    fn = lambda x: gaussian_filter(x, sigma, mode="constant", cval=0.0)
    expected = smooth_with_function_and_mask(image, fn, mask)
    workspace, module = make_workspace(image, mask)
    module.smoothing_method.value = S.GAUSSIAN_FILTER
    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
    assert result is not None
    np.testing.assert_almost_equal(result.pixel_data, expected)


def test_03_02_gaussian_auto_large():
    """Test the smooth module with Gaussian smoothing in large automatic mode"""
    sigma = 30.0 / 2.35
    image = np.random.uniform(size=(3200, 100)).astype(np.float32)
    mask = np.ones(image.shape, bool)
    mask[40:60, 45:65] = False
    fn = lambda x: gaussian_filter(x, sigma, mode="constant", cval=0.0)
    expected = smooth_with_function_and_mask(image, fn, mask)
    workspace, module = make_workspace(image, mask)
    module.smoothing_method.value = S.GAUSSIAN_FILTER
    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
    assert result is not None
    np.testing.assert_almost_equal(result.pixel_data, expected)


def test_03_03_gaussian_manual():
    """Test the smooth module with Gaussian smoothing, manual sigma"""
    sigma = 15.0 / 2.35
    np.random.seed(0)
    image = np.random.uniform(size=(100, 100)).astype(np.float32)
    mask = np.ones(image.shape, bool)
    mask[40:60, 45:65] = False
    fn = lambda x: gaussian_filter(x, sigma, mode="constant", cval=0.0)
    expected = smooth_with_function_and_mask(image, fn, mask)
    workspace, module = make_workspace(image, mask)
    module.smoothing_method.value = S.GAUSSIAN_FILTER
    module.wants_automatic_object_size.value = False
    module.object_size.value = 15.0
    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
    assert result is not None
    np.testing.assert_almost_equal(result.pixel_data, expected)


def test_04_01_median():
    """test the smooth module with median filtering"""
    object_size = 100.0 / 40.0
    np.random.seed(0)
    image = np.random.uniform(size=(100, 100)).astype(np.float32)
    mask = np.ones(image.shape, bool)
    mask[40:60, 45:65] = False
    expected = median_filter(image, mask, object_size / 2 + 1)
    workspace, module = make_workspace(image, mask)
    module.smoothing_method.value = S.MEDIAN_FILTER
    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
    assert result is not None
    np.testing.assert_almost_equal(result.pixel_data, expected)


def test_04_02_median_multichannel():
    """test the smooth module with median filtering"""
    object_size = 100.0 / 40.0
    np.random.seed(0)
    image_plane = np.random.uniform(size=(100, 100)).astype(np.float32)
    image = np.repeat(image_plane[:, :, np.newaxis], 3, axis=2)
    mask = np.ones(image.shape[:2], bool)
    mask[40:60, 45:65] = False
    expected_plane = median_filter(image_plane, mask, object_size / 2 + 1)
    expected = np.repeat(expected_plane[:, :, np.newaxis], 3, axis=2)
    workspace, module = make_workspace(image, mask)
    module.smoothing_method.value = S.MEDIAN_FILTER
    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
    assert result is not None
    np.testing.assert_almost_equal(result.pixel_data, expected)


def test_05_01_bilateral():
    """test the smooth module with bilateral filtering"""
    sigma = 16.0
    sigma_range = 0.2
    np.random.seed(0)
    image = np.random.uniform(size=(100, 100)).astype(np.float32)
    mask = np.ones(image.shape, bool)
    mask[40:60, 45:65] = False
    expected = skimage.restoration.denoise_bilateral(
        image=image,
        multichannel=False,
        sigma_color=sigma_range,
        sigma_spatial=sigma,
    )
    workspace, module = make_workspace(image, mask)
    module.smoothing_method.value = S.SMOOTH_KEEPING_EDGES
    module.sigma_range.value = sigma_range
    module.wants_automatic_object_size.value = False
    module.object_size.value = 16.0 * 2.35
    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
    assert result is not None
    np.testing.assert_almost_equal(result.pixel_data, expected)


def test_06_01_remove_outlier():
    """Test the smooth module for outlier filtering
    Test if a singe outlier pixel will be detected.
    """
    img_shape = (10, 10)
    image = np.zeros(img_shape)
    image[5, 5] = 1

    mask = np.ones(img_shape)
    expected_image = np.zeros(img_shape)

    workspace, module = make_workspace(image, mask)
    module.smoothing_method.value = S.CLIP_HOT_PIXELS
    module.hp_threshold.value = 0.1
    module.hp_filter_size.value = 3
    module.scale_hp_threshold.value = False
    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
    np.testing.assert_almost_equal(result.pixel_data, expected_image)


def test_06_01_remove_outlier_multichannel():
    """Test the smooth module for outlier filtering
    Test if a singe outlier pixel will be detected in a multichannel image.
    """
    img_shape = (10, 10, 5)
    image = np.zeros(img_shape)
    image[5, 5, :] = 1

    mask = np.ones(img_shape[:2])
    expected_image = np.zeros(img_shape)

    workspace, module = make_workspace(image, mask)
    module.smoothing_method.value = S.CLIP_HOT_PIXELS
    module.hp_threshold.value = 0.1
    module.hp_filter_size.value = 3
    module.scale_hp_threshold.value = False
    module.run(workspace)
    result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
    np.testing.assert_almost_equal(result.pixel_data, expected_image)
