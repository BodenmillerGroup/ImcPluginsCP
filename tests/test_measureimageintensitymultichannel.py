import numpy
import pytest
import io

import cellprofiler_core.image
import cellprofiler_core.measurement

import cellprofiler_core.modules.injectimage
import cellprofiler_core.object
import cellprofiler_core.pipeline
import cellprofiler_core.workspace
from cellprofiler_core.constants.measurement import COLTYPE_FLOAT, COLTYPE_INTEGER
from cellprofiler_core.utilities.core import modules as cpmodules

IMAGE_NAME = "image"
OUTPUT_IMAGE_F = "outputimage%d"

N_CHANNELS = 4

import plugins.measureimageintensitymultichannel as mimc



@pytest.fixture(scope="function")
def image():
    return cellprofiler_core.image.Image()


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
    module = mimc.MeasureImageIntensityMultiChannel()

    module.images_list.value = "image"

    module.objects_list.value = "objects"

    module.nchannels.value = N_CHANNELS


    return module


@pytest.fixture(scope="function")
def workspace(image, measurements, module, objects):
    image_set_list = cellprofiler_core.image.ImageSetList()

    image_set = image_set_list.get_image_set(0)

    image_set.add("image", image)

    object_set = cellprofiler_core.object.ObjectSet()

    object_set.add_objects(objects, "objects")

    return cellprofiler_core.workspace.Workspace(
        cellprofiler_core.pipeline.Pipeline(),
        module,
        image_set,
        object_set,
        measurements,
        image_set_list,
    )

def test_init():
    x = mimc.MeasureImageIntensityMultiChannel()

def test_zeros(image, measurements, module, workspace):
    """Test operation on a completely-masked image"""
    image.pixel_data = numpy.zeros((10, 10, N_CHANNELS))

    image.mask = numpy.zeros((10, 10), bool)

    module.run(workspace)

    for i in range(N_CHANNELS):
        assert (
            measurements.get_current_measurement(
                "Image", f"Intensity_TotalArea_image_c{i+1}"
            )
            == 0
        )

    assert len(measurements.get_object_names()) == 1

    assert measurements.get_object_names()[0] == "Image"

    columns = module.get_measurement_columns(workspace.pipeline)

    features = measurements.get_feature_names("Image") * N_CHANNELS

    assert len(columns) == len(features)

    for column in columns:
        assert column[1] in features


def test_image(image, measurements, module, workspace):
    """Test operation on a single unmasked image"""
    numpy.random.seed(0)

    pixels = numpy.random.uniform(size=(10, 10)).astype(numpy.float32) * 0.99

    pixels[0:2, 0:2] = 1

    image.pixel_data = pixels

    module.run(workspace)

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_TotalArea_image"
        )
        == 100
    )

    assert measurements.get_current_measurement(
        "Image", "Intensity_TotalIntensity_image"
    ) == numpy.sum(pixels)

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_MeanIntensity_image"
        )
        == numpy.sum(pixels) / 100.0
    )

    assert measurements.get_current_image_measurement(
        "Intensity_MinIntensity_image"
    ) == numpy.min(pixels)

    assert measurements.get_current_image_measurement(
        "Intensity_MaxIntensity_image"
    ) == numpy.max(pixels)

    assert (
        measurements.get_current_image_measurement("Intensity_PercentMaximal_image")
        == 4.0
    )


def test_image_and_mask(image, measurements, module, workspace):
    """Test operation on a masked image"""
    numpy.random.seed(0)

    pixels = numpy.random.uniform(size=(10, 10)).astype(numpy.float32) * 0.99

    pixels[1:3, 1:3] = 1

    mask = numpy.zeros((10, 10), bool)

    mask[1:9, 1:9] = True

    image.pixel_data = pixels

    image.mask = mask

    module.run(workspace)

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_TotalArea_image"
        )
        == 64
    )

    assert measurements.get_current_measurement(
        "Image", "Intensity_TotalIntensity_image"
    ) == numpy.sum(pixels[1:9, 1:9])

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_MeanIntensity_image"
        )
        == numpy.sum(pixels[1:9, 1:9]) / 64.0
    )

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_PercentMaximal_image"
        )
        == 400.0 / 64.0
    )


def test_image_and_objects(image, measurements, module, objects, workspace):
    """Test operation on an image masked by objects"""
    numpy.random.seed(0)

    pixels = numpy.random.uniform(size=(10, 10)).astype(numpy.float32) * 0.99

    pixels[1:3, 1:3] = 1

    image.pixel_data = pixels

    labels = numpy.zeros((10, 10), int)

    labels[1:9, 1:5] = 1

    labels[1:9, 5:9] = 2

    objects.segmented = labels

    module.wants_objects.value = True

    module.run(workspace)

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_TotalArea_image_objects"
        )
        == 64
    )

    assert measurements.get_current_measurement(
        "Image", "Intensity_TotalIntensity_image_objects"
    ) == numpy.sum(pixels[1:9, 1:9])

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_MeanIntensity_image_objects"
        )
        == numpy.sum(pixels[1:9, 1:9]) / 64.0
    )

    numpy.testing.assert_almost_equal(
        measurements.get_current_measurement(
            "Image",
            "Intensity_PercentMaximal_image_objects",
        ),
        400.0 / 64.0,
    )

    assert len(measurements.get_object_names()) == 1

    assert measurements.get_object_names()[0] == "Image"

    columns = module.get_measurement_columns(workspace.pipeline)

    features = measurements.get_feature_names("Image")

    assert len(columns) == len(features)

    for column in columns:
        assert column[1] in features


def test_image_and_objects_and_mask(image, measurements, module, objects, workspace):
    """Test operation on an image masked by objects and a mask"""
    numpy.random.seed(0)

    pixels = numpy.random.uniform(size=(10, 10)).astype(numpy.float32)

    mask = numpy.zeros((10, 10), bool)

    mask[1:9, :9] = True

    image.pixel_data = pixels

    image.mask = mask

    labels = numpy.zeros((10, 10), int)

    labels[1:9, 1:5] = 1

    labels[1:9, 5:] = 2

    objects.segmented = labels

    module.wants_objects.value = True

    module.run(workspace)

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_TotalArea_image_objects"
        )
        == 64
    )

    assert measurements.get_current_measurement(
        "Image", "Intensity_TotalIntensity_image_objects"
    ) == numpy.sum(pixels[1:9, 1:9])

    assert (
        measurements.get_current_measurement(
            "Image", "Intensity_MeanIntensity_image_objects"
        )
        == numpy.sum(pixels[1:9, 1:9]) / 64.0
    )


def test_get_measurement_columns_whole_image_mode(module):
    image_names = ["image%d" % i for i in range(3)]

    module.wants_objects.value = False

    expected_suffixes = []

    for image_name in image_names:
        im = module.images_list.value[-1]

        module.images_list.value.append(image_name)

        expected_suffixes.append(image_name)

    columns = module.get_measurement_columns(None)

    assert all([column[0] == "Image" for column in columns])

    for expected_suffix in expected_suffixes:
        for feature, coltype in (
            (
                mimc.F_TOTAL_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_MEAN_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_MIN_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_MAX_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_TOTAL_AREA,
                COLTYPE_INTEGER,
            ),
            (
                mimc.F_PERCENT_MAXIMAL,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_MAD_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_LOWER_QUARTILE,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_UPPER_QUARTILE,
                COLTYPE_FLOAT,
            ),
        ):
            # feature names are now formatting strings
            feature_name = feature % expected_suffix

            assert any(
                [
                    (column[1] == feature_name and column[2] == coltype)
                    for column in columns
                ]
            )


def test_get_measurement_columns_object_mode(module):
    image_names = ["image%d" % i for i in range(3)]

    object_names = ["object%d" % i for i in range(3)]

    module.wants_objects.value = True

    expected_suffixes = []

    for image_name in image_names:
        module.images_list.value.append(image_name)

        for object_name in object_names:
            module.objects_list.value.append(object_name)

            expected_suffixes.append("%s_%s" % (image_name, object_name))

    columns = module.get_measurement_columns(None)

    assert all([column[0] == "Image" for column in columns])

    for expected_suffix in expected_suffixes:
        for feature, coltype in (
            (
                mimc.F_TOTAL_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_MEAN_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_MIN_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_MAX_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_TOTAL_AREA,
                COLTYPE_INTEGER,
            ),
            (
                mimc.F_PERCENT_MAXIMAL,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_MAD_INTENSITY,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_LOWER_QUARTILE,
                COLTYPE_FLOAT,
            ),
            (
                mimc.F_UPPER_QUARTILE,
                COLTYPE_FLOAT,
            ),
        ):
            # feature names are now formatting strings
            feature_name = feature % expected_suffix
            assert any(
                [
                    (column[1] == feature_name and column[2] == coltype)
                    for column in columns
                ]
            )