import math

import centrosome.outline
import numpy
import numpy.testing
import pytest
import skimage.measure
import skimage.segmentation

import cellprofiler_core.image
import cellprofiler_core.measurement
from cellprofiler_core.constants.measurement import (
    EXPERIMENT,
    COLTYPE_FLOAT,
    C_LOCATION,
)


import cellprofiler_core.object
import cellprofiler_core.pipeline
import cellprofiler_core.preferences
import cellprofiler_core.workspace

cellprofiler_core.preferences.set_headless()

import plugins.measureobjectintensitymultichannel as momc

IMAGE_NAME = "MyImage"
OBJECT_NAME = "MyObjects"
N_CHANNELS = 4


@pytest.fixture(scope="function")
def image():
    return cellprofiler_core.image.Image()


@pytest.fixture(scope="function")
def measurements():
    return cellprofiler_core.measurement.Measurements()


@pytest.fixture(scope="function")
def module():
    module = momc.MeasureObjectIntensityMultichannel()

    module.images_list.value = IMAGE_NAME

    module.objects_list.value = OBJECT_NAME

    return module


@pytest.fixture(scope="function")
def objects(image):
    objects = cellprofiler_core.object.Objects()

    objects.parent_image = image

    return objects


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
    x = momc.MeasureObjectIntensityMultichannel()


def assert_features_and_columns_match(measurements, module):
    object_names = [
        x
        for x in measurements.get_object_names()
        if x
        not in (
            "Image",
            EXPERIMENT,
        )
    ]

    features = [
        [f for f in measurements.get_feature_names(object_name) if f != "Exit_Status"]
        for object_name in object_names
    ]

    columns = module.get_measurement_columns(None)

    assert sum([len(f) for f in features]) == len(columns)

    for column in columns:
        index = object_names.index(column[0])

        assert column[1] in features[index]

        assert column[2] == COLTYPE_FLOAT


def test_supplied_measurements(module):
    """Test the get_category / get_measurements, get_measurement_images functions"""
    module.images_list.value = "MyImage"

    module.objects_list.value = "MyObjects1, MyObjects2"

    expected_categories = tuple(
        sorted(
            [
                momc.INTENSITY,
                C_LOCATION,
            ]
        )
    )

    assert (
        tuple(sorted(module.get_categories(None, "MyObjects1"))) == expected_categories
    )

    assert module.get_categories(None, "Foo") == []

    measurements = module.get_measurements(None, "MyObjects1", momc.INTENSITY)

    assert len(measurements) == len(momc.ALL_MEASUREMENTS)

    measurements = module.get_measurements(None, "MyObjects1", C_LOCATION)

    assert len(measurements) == len(momc.ALL_LOCATION_MEASUREMENTS)

    assert all([m in momc.ALL_LOCATION_MEASUREMENTS for m in measurements])

    assert (
        module.get_measurement_images(
            None,
            "MyObjects1",
            momc.INTENSITY,
            momc.MAX_INTENSITY,
        )
        == ["MyImage"]
    )


def test_get_measurement_columns(module):
    """test the get_measurement_columns method"""
    module.images_list.value = "MyImage"

    module.objects_list.value = "MyObjects1, MyObjects2"

    module.nchannels.value = N_CHANNELS

    columns = module.get_measurement_columns(None)

    assert len(columns) == N_CHANNELS * 2 * (
        len(momc.ALL_MEASUREMENTS) + len(momc.ALL_LOCATION_MEASUREMENTS)
    )

    for column in columns:
        assert column[0] in ("MyObjects1", "MyObjects2")

        assert column[2], COLTYPE_FLOAT

        category = column[1].split("_")[0]

        assert category in (
            momc.INTENSITY,
            C_LOCATION,
        )

        if category == momc.INTENSITY:
            assert column[1][column[1].find("_") + 1 :] in [
                m + "_MyImage" + f"_c{c+1}"
                for m in momc.ALL_MEASUREMENTS
                for c in range(N_CHANNELS)
            ]
        else:
            assert column[1][column[1].find("_") + 1 :] in [
                m + "_MyImage" + f"_c{c+1}"
                for m in momc.ALL_LOCATION_MEASUREMENTS
                for c in range(N_CHANNELS)
            ]


def test_zero(image, measurements, module, objects, workspace):
    """Make sure we can process a blank image"""
    image.pixel_data = numpy.zeros((10, 10, N_CHANNELS))

    objects.segmented = numpy.zeros((10, 10))

    module.nchannels.value = N_CHANNELS

    module.run(workspace)

    for category, features in (
        (
            momc.INTENSITY,
            momc.ALL_MEASUREMENTS,
        ),
        (
            C_LOCATION,
            momc.ALL_LOCATION_MEASUREMENTS,
        ),
    ):
        for meas_name in features:
            for c in range(N_CHANNELS):
                feature_name = "%s_%s_%s_c%s" % (category, meas_name, "MyImage", c + 1)

                data = measurements.get_current_measurement("MyObjects", feature_name)

                assert numpy.product(data.shape) == 0, (
                    "Got data for feature %s" % feature_name
                )

        assert_features_and_columns_match(measurements, module)


def test_masked(image, measurements, module, objects, workspace):
    """Make sure we can process a completely masked image
    Regression test of IMG-971
    """
    image.pixel_data = numpy.zeros((10, 10, N_CHANNELS))

    image.mask = numpy.zeros((10, 10), bool)

    objects.segmented = numpy.ones((10, 10), int)

    module.nchannels.value = N_CHANNELS

    module.run(workspace)

    for meas_name in momc.ALL_MEASUREMENTS:
        for c in range(N_CHANNELS):
            feature_name = "%s_%s_%s_c%s" % (
                momc.INTENSITY,
                meas_name,
                "MyImage",
                c + 1,
            )

            data = measurements.get_current_measurement("MyObjects", feature_name)

            assert numpy.product(data.shape) == 1

            assert numpy.all(numpy.isnan(data) | (data == 0))

    assert_features_and_columns_match(measurements, module)


def test_one(image, measurements, module, objects, workspace):
    """Check measurements on a 3x3 square of 1's"""
    data = numpy.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )

    image.pixel_data = data.astype(float)

    objects.segmented = data.astype(int)

    module.nchannels.value = 1

    module.run(workspace)

    for category, meas_name, value in (
        (
            momc.INTENSITY,
            momc.INTEGRATED_INTENSITY,
            9,
        ),
        (
            momc.INTENSITY,
            momc.MEAN_INTENSITY,
            1,
        ),
        (
            momc.INTENSITY,
            momc.STD_INTENSITY,
            0,
        ),
        (
            momc.INTENSITY,
            momc.MIN_INTENSITY,
            1,
        ),
        (
            momc.INTENSITY,
            momc.MAX_INTENSITY,
            1,
        ),
        (
            momc.INTENSITY,
            momc.INTEGRATED_INTENSITY_EDGE,
            8,
        ),
        (
            momc.INTENSITY,
            momc.MEAN_INTENSITY_EDGE,
            1,
        ),
        (
            momc.INTENSITY,
            momc.STD_INTENSITY_EDGE,
            0,
        ),
        (
            momc.INTENSITY,
            momc.MIN_INTENSITY_EDGE,
            1,
        ),
        (
            momc.INTENSITY,
            momc.MAX_INTENSITY_EDGE,
            1,
        ),
        (
            momc.INTENSITY,
            momc.MASS_DISPLACEMENT,
            0,
        ),
        (
            momc.INTENSITY,
            momc.LOWER_QUARTILE_INTENSITY,
            1,
        ),
        (
            momc.INTENSITY,
            momc.MEDIAN_INTENSITY,
            1,
        ),
        (
            momc.INTENSITY,
            momc.UPPER_QUARTILE_INTENSITY,
            1,
        ),
        (
            C_LOCATION,
            momc.LOC_CMI_X,
            3,
        ),
        (
            C_LOCATION,
            momc.LOC_CMI_Y,
            2,
        ),
    ):
        feature_name = "%s_%s_%s_c%s" % (category, meas_name, "MyImage", 1)

        data = measurements.get_current_measurement("MyObjects", feature_name)

        assert numpy.product(data.shape) == 1

        assert data[0] == value, "%s expected %f != actual %f" % (
            meas_name,
            value,
            data[0],
        )


def test_one_masked(image, measurements, module, objects, workspace):
    """Check measurements on a 3x3 square of 1's"""
    img = numpy.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )

    mask = img > 0

    image.pixel_data = img.astype(float)

    image.mask = mask

    objects.segmented = img.astype(int)

    module.run(workspace)

    for meas_name, value in (
        (momc.INTEGRATED_INTENSITY, 9),
        (momc.MEAN_INTENSITY, 1),
        (momc.STD_INTENSITY, 0),
        (momc.MIN_INTENSITY, 1),
        (momc.MAX_INTENSITY, 1),
        (momc.INTEGRATED_INTENSITY_EDGE, 8),
        (momc.MEAN_INTENSITY_EDGE, 1),
        (momc.STD_INTENSITY_EDGE, 0),
        (momc.MIN_INTENSITY_EDGE, 1),
        (momc.MAX_INTENSITY_EDGE, 1),
        (momc.MASS_DISPLACEMENT, 0),
        (momc.LOWER_QUARTILE_INTENSITY, 1),
        (momc.MEDIAN_INTENSITY, 1),
        (momc.MAD_INTENSITY, 0),
        (momc.UPPER_QUARTILE_INTENSITY, 1),
    ):
        feature_name = "%s_%s_%s_c%s" % (momc.INTENSITY, meas_name, "MyImage", 1)

        data = measurements.get_current_measurement("MyObjects", feature_name)

        assert numpy.product(data.shape) == 1

        assert data[0] == value, "%s expected %f != actual %f" % (
            meas_name,
            value,
            data[0],
        )


def test_intensity_location(image, measurements, module, objects, workspace):
    data = (
        numpy.array(
            [
                [0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 2, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0],
            ]
        ).astype(float)
        / 2.0
    )

    image.pixel_data = data

    labels = (data != 0).astype(int)

    objects.segmented = labels

    module.run(workspace)

    for feature, value in (
        (momc.LOC_MAX_X, 5),
        (momc.LOC_MAX_Y, 2),
    ):
        feature_name = "%s_%s_%s_c%s" % (C_LOCATION, feature, "MyImage", 1)

        values = measurements.get_current_measurement(OBJECT_NAME, feature_name)

        assert len(values) == 1

        assert values[0] == value


def test_mass_displacement(image, measurements, module, objects, workspace):
    """Check the mass displacement of three squares"""

    labels = numpy.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )

    data = numpy.zeros(labels.shape, dtype=float)
    #
    # image # 1 has a single value in one of the corners
    # whose distance is sqrt(8) from the center
    #
    data[1, 1] = 1

    # image # 2 has a single value on the top edge
    # and should have distance 2
    #
    data[7, 3] = 1

    # image # 3 has a single value on the left edge
    # and should have distance 2
    data[15, 1] = 1

    image.pixel_data = data

    objects.segmented = labels

    module.run(workspace)

    feature_name = "%s_%s_%s_c%s" % (
        momc.INTENSITY,
        momc.MASS_DISPLACEMENT,
        "MyImage",
        1,
    )

    mass_displacement = measurements.get_current_measurement("MyObjects", feature_name)

    assert numpy.product(mass_displacement.shape) == 3

    numpy.testing.assert_almost_equal(mass_displacement[0], math.sqrt(8.0))

    numpy.testing.assert_almost_equal(mass_displacement[1], 2.0)

    numpy.testing.assert_almost_equal(mass_displacement[2], 2.0)


def test_mass_displacement_masked(image, measurements, module, objects, workspace):
    """Regression test IMG-766 - mass displacement of a masked image"""
    labels = numpy.array(
        [
            [0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 2, 2, 2, 2, 2, 0],
            [0, 0, 0, 0, 0, 0, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 3, 3, 3, 3, 3, 0],
            [0, 0, 0, 0, 0, 0, 0],
        ]
    )

    data = numpy.zeros(labels.shape, dtype=float)

    #
    # image # 1 has a single value in one of the corners
    # whose distance is sqrt(8) from the center
    #
    data[1, 1] = 1

    # image # 2 has a single value on the top edge
    # and should have distance 2
    #
    data[7, 3] = 1

    # image # 3 has a single value on the left edge
    # and should have distance 2
    data[15, 1] = 1

    mask = numpy.zeros(data.shape, bool)

    mask[labels > 0] = True

    image.pixel_data = data

    image.mask = mask

    objects.segmented = labels

    module.run(workspace)

    feature_name = "%s_%s_%s_c%s" % (
        momc.INTENSITY,
        momc.MASS_DISPLACEMENT,
        "MyImage",
        1,
    )

    mass_displacement = measurements.get_current_measurement("MyObjects", feature_name)

    assert numpy.product(mass_displacement.shape) == 3

    numpy.testing.assert_almost_equal(mass_displacement[0], math.sqrt(8.0))

    numpy.testing.assert_almost_equal(mass_displacement[1], 2.0)

    numpy.testing.assert_almost_equal(mass_displacement[2], 2.0)


def test_quartiles_uniform(image, measurements, module, objects, workspace):
    """test quartile values on a 250x250 square filled with uniform values"""
    labels = numpy.ones((250, 250), int)

    numpy.random.seed(0)

    data = numpy.random.uniform(size=(250, 250))

    image.pixel_data = data

    objects.segmented = labels

    module.run(workspace)

    feature_name = "%s_%s_%s_c%s" % (
        momc.INTENSITY,
        momc.LOWER_QUARTILE_INTENSITY,
        "MyImage",
        1,
    )

    data = measurements.get_current_measurement("MyObjects", feature_name)

    numpy.testing.assert_almost_equal(data[0], 0.25, 2)

    feature_name = "%s_%s_%s_c%s" % (
        momc.INTENSITY,
        momc.MEDIAN_INTENSITY,
        "MyImage",
        1,
    )

    data = measurements.get_current_measurement("MyObjects", feature_name)

    numpy.testing.assert_almost_equal(data[0], 0.50, 2)

    feature_name = "%s_%s_%s_c%s" % (momc.INTENSITY, momc.MAD_INTENSITY, "MyImage", 1)

    data = measurements.get_current_measurement("MyObjects", feature_name)

    numpy.testing.assert_almost_equal(data[0], 0.25, 2)

    feature_name = "%s_%s_%s_c%s" % (
        momc.INTENSITY,
        momc.UPPER_QUARTILE_INTENSITY,
        "MyImage",
        1,
    )

    data = measurements.get_current_measurement("MyObjects", feature_name)

    numpy.testing.assert_almost_equal(data[0], 0.75, 2)


def test_quartiles_one_pixel(image, module, objects, workspace):
    """Regression test a bug that occurs in an image with one pixel"""
    labels = numpy.zeros((10, 20))

    labels[2:7, 3:8] = 1

    labels[5, 15] = 2

    numpy.random.seed(0)

    data = numpy.random.uniform(size=(10, 20))

    image.pixel_data = data

    objects.segmented = labels

    # Crashes when pipeline runs in measureobjectintensity.py revision 7146
    module.run(workspace)


def test_quartiles_four_objects(image, measurements, module, objects, workspace):
    """test quartile values on a 250x250 square with 4 objects"""
    labels = numpy.ones((250, 250), int)

    labels[125:, :] += 1

    labels[:, 125:] += 2

    numpy.random.seed(0)

    data = numpy.random.uniform(size=(250, 250))

    #
    # Make the distributions center around .5, .25, 1/6 and .125
    #
    data /= labels.astype(float)

    image.pixel_data = data

    objects.segmented = labels

    module.run(workspace)

    feature_name = "%s_%s_%s_c%s" % (
        momc.INTENSITY,
        momc.LOWER_QUARTILE_INTENSITY,
        "MyImage",
        1,
    )

    data = measurements.get_current_measurement("MyObjects", feature_name)

    numpy.testing.assert_almost_equal(data[0], 1.0 / 4.0, 2)

    numpy.testing.assert_almost_equal(data[1], 1.0 / 8.0, 2)

    numpy.testing.assert_almost_equal(data[2], 1.0 / 12.0, 2)

    numpy.testing.assert_almost_equal(data[3], 1.0 / 16.0, 2)

    feature_name = "%s_%s_%s_c%s" % (
        momc.INTENSITY,
        momc.MEDIAN_INTENSITY,
        "MyImage",
        1,
    )

    data = measurements.get_current_measurement("MyObjects", feature_name)

    numpy.testing.assert_almost_equal(data[0], 1.0 / 2.0, 2)

    numpy.testing.assert_almost_equal(data[1], 1.0 / 4.0, 2)

    numpy.testing.assert_almost_equal(data[2], 1.0 / 6.0, 2)

    numpy.testing.assert_almost_equal(data[3], 1.0 / 8.0, 2)

    feature_name = "%s_%s_%s_c%s" % (
        momc.INTENSITY,
        momc.UPPER_QUARTILE_INTENSITY,
        "MyImage",
        1,
    )

    data = measurements.get_current_measurement("MyObjects", feature_name)

    numpy.testing.assert_almost_equal(data[0], 3.0 / 4.0, 2)

    numpy.testing.assert_almost_equal(data[1], 3.0 / 8.0, 2)

    numpy.testing.assert_almost_equal(data[2], 3.0 / 12.0, 2)

    numpy.testing.assert_almost_equal(data[3], 3.0 / 16.0, 2)

    feature_name = "%s_%s_%s_c%s" % (momc.INTENSITY, momc.MAD_INTENSITY, "MyImage", 1)

    data = measurements.get_current_measurement("MyObjects", feature_name)

    numpy.testing.assert_almost_equal(data[0], 1.0 / 4.0, 2)

    numpy.testing.assert_almost_equal(data[1], 1.0 / 8.0, 2)

    numpy.testing.assert_almost_equal(data[2], 1.0 / 12.0, 2)

    numpy.testing.assert_almost_equal(data[3], 1.0 / 16.0, 2)


def test_median_intensity_masked(image, measurements, module, objects, workspace):
    numpy.random.seed(37)

    labels = numpy.ones((10, 10), int)

    mask = numpy.ones((10, 10), bool)

    mask[:, :5] = False

    pixel_data = numpy.random.uniform(size=(10, 10, N_CHANNELS)).astype(numpy.float32)

    pixel_data[~mask, :] = 1

    image.pixel_data = pixel_data

    image.mask = mask

    objects.segmented = labels

    expected = [
        numpy.sort(pixel_data[mask, c])[numpy.sum(mask) // 2] for c in range(N_CHANNELS)
    ]

    module.nchannels.value = N_CHANNELS

    module.run(workspace)

    assert isinstance(measurements, cellprofiler_core.measurement.Measurements)

    for c, exp in enumerate(expected):
        values = measurements.get_current_measurement(
            OBJECT_NAME,
            "_".join((momc.INTENSITY, momc.MEDIAN_INTENSITY, IMAGE_NAME, f"c{c+1}")),
        )

        assert len(values) == 1

        assert exp == values[0]
