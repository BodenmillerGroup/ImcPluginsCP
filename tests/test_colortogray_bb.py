import numpy
import pytest
import six.moves
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

import cellprofiler.modules.colortogray
import plugins.colortograybb as colortogray
cpmodules.fill_modules()
cpmodules.add_module_for_tst(colortogray.ColorToGray)
def get_my_image():
    """A color image with red in the upper left, green in the lower left and blue in the upper right"""
    img = numpy.zeros((50, 50, 3))
    img[0:25, 0:25, 0] = 1
    img[0:25, 25:50, 1] = 1
    img[25:50, 0:25, 2] = 1
    return img


def test_init():
    x = colortogray.ColorToGray()


def test_combine():
    img = get_my_image()
    inj = cellprofiler_core.modules.injectimage.InjectImage("my_image", img)
    inj.set_module_num(1)
    ctg = colortogray.ColorToGray()
    ctg.set_module_num(2)
    ctg.image_name.value = "my_image"
    ctg.combine_or_split.value = cellprofiler.modules.colortogray.COMBINE
    ctg.red_contribution.value = 1
    ctg.green_contribution.value = 2
    ctg.blue_contribution.value = 3
    ctg.grayscale_name.value = "my_grayscale"
    pipeline = cellprofiler_core.pipeline.Pipeline()
    pipeline.add_module(inj)
    pipeline.add_module(ctg)
    pipeline.test_valid()

    measurements = cellprofiler_core.measurement.Measurements()
    object_set = cellprofiler_core.object.ObjectSet()
    image_set_list = cellprofiler_core.image.ImageSetList()
    workspace = cellprofiler_core.workspace.Workspace(
        pipeline, inj, None, None, measurements, image_set_list, None
    )
    inj.prepare_run(workspace)
    inj.prepare_group(workspace, {}, [1])
    image_set = image_set_list.get_image_set(0)
    inj.run(
        cellprofiler_core.workspace.Workspace(
            pipeline, inj, image_set, object_set, measurements, None
        )
    )
    ctg.run(
        cellprofiler_core.workspace.Workspace(
            pipeline, ctg, image_set, object_set, measurements, None
        )
    )
    grayscale = image_set.get_image("my_grayscale")
    assert grayscale
    img = grayscale.image
    numpy.testing.assert_almost_equal(img[0, 0], 1.0 / 6.0)
    numpy.testing.assert_almost_equal(img[0, 25], 1.0 / 3.0)
    numpy.testing.assert_almost_equal(img[25, 0], 1.0 / 2.0)
    numpy.testing.assert_almost_equal(img[25, 25], 0)


def test_split_all():
    img = get_my_image()
    inj = cellprofiler_core.modules.injectimage.InjectImage("my_image", img)
    inj.set_module_num(1)
    ctg = colortogray.ColorToGray()
    ctg.set_module_num(2)
    ctg.image_name.value = "my_image"
    ctg.combine_or_split.value = cellprofiler.modules.colortogray.SPLIT
    ctg.use_red.value = True
    ctg.use_blue.value = True
    ctg.use_green.value = True
    ctg.red_name.value = "my_red"
    ctg.green_name.value = "my_green"
    ctg.blue_name.value = "my_blue"
    pipeline = cellprofiler_core.pipeline.Pipeline()
    pipeline.add_module(inj)
    pipeline.add_module(ctg)
    pipeline.test_valid()

    measurements = cellprofiler_core.measurement.Measurements()
    object_set = cellprofiler_core.object.ObjectSet()
    image_set_list = cellprofiler_core.image.ImageSetList()
    workspace = cellprofiler_core.workspace.Workspace(
        pipeline, inj, None, None, measurements, image_set_list, None
    )
    inj.prepare_run(workspace)
    inj.prepare_group(workspace, {}, [1])
    image_set = image_set_list.get_image_set(0)
    inj.run(
        cellprofiler_core.workspace.Workspace(
            pipeline, inj, image_set, object_set, measurements, None
        )
    )
    ctg.run(
        cellprofiler_core.workspace.Workspace(
            pipeline, ctg, image_set, object_set, measurements, None
        )
    )
    red = image_set.get_image("my_red")
    assert red
    img = red.image
    numpy.testing.assert_almost_equal(img[0, 0], 1)
    numpy.testing.assert_almost_equal(img[0, 25], 0)
    numpy.testing.assert_almost_equal(img[25, 0], 0)
    numpy.testing.assert_almost_equal(img[25, 25], 0)
    green = image_set.get_image("my_green")
    assert green
    img = green.image
    numpy.testing.assert_almost_equal(img[0, 0], 0)
    numpy.testing.assert_almost_equal(img[0, 25], 1)
    numpy.testing.assert_almost_equal(img[25, 0], 0)
    numpy.testing.assert_almost_equal(img[25, 25], 0)
    blue = image_set.get_image("my_blue")
    assert blue
    img = blue.image
    numpy.testing.assert_almost_equal(img[0, 0], 0)
    numpy.testing.assert_almost_equal(img[0, 25], 0)
    numpy.testing.assert_almost_equal(img[25, 0], 1)
    numpy.testing.assert_almost_equal(img[25, 25], 0)


def test_combine_channels():
    numpy.random.seed(13)
    image = numpy.random.uniform(size=(20, 10, 5))
    image_set_list = cellprofiler_core.image.ImageSetList()
    image_set = image_set_list.get_image_set(0)
    image_set.add(IMAGE_NAME, cellprofiler_core.image.Image(image))

    module = colortogray.ColorToGray()
    module.set_module_num(1)
    module.image_name.value = IMAGE_NAME
    module.combine_or_split.value = cellprofiler.modules.colortogray.COMBINE
    module.grayscale_name.value = OUTPUT_IMAGE_F % 1
    module.rgb_or_channels.value = cellprofiler.modules.colortogray.CH_CHANNELS
    module.add_channel()
    module.add_channel()

    channel_indexes = numpy.array([2, 0, 3])
    factors = numpy.random.uniform(size=3)
    divisor = numpy.sum(factors)
    expected = numpy.zeros((20, 10))
    for i, channel_index in enumerate(channel_indexes):
        module.channels[i].channel_choice.value = channel_index + 1
        module.channels[i].contribution.value_text = "%.10f" % factors[i]
        expected += image[:, :, channel_index] * factors[i] / divisor

    pipeline = cellprofiler_core.pipeline.Pipeline()

    def callback(caller, event):
        assert not isinstance(event, cellprofiler_core.pipeline.event.RunException)

    pipeline.add_listener(callback)
    pipeline.add_module(module)
    workspace = cellprofiler_core.workspace.Workspace(
        pipeline,
        module,
        image_set,
        cellprofiler_core.object.ObjectSet(),
        cellprofiler_core.measurement.Measurements(),
        image_set_list,
    )
    module.run(workspace)
    pixels = image_set.get_image(module.grayscale_name.value).pixel_data
    assert pixels.ndim == 2
    assert tuple(pixels.shape) == (20, 10)
    numpy.testing.assert_almost_equal(expected, pixels)


def test_split_channels():
    numpy.random.seed(13)
    image = numpy.random.uniform(size=(20, 10, 5))
    image_set_list = cellprofiler_core.image.ImageSetList()
    image_set = image_set_list.get_image_set(0)
    image_set.add(IMAGE_NAME, cellprofiler_core.image.Image(image))

    module = colortogray.ColorToGray()
    module.set_module_num(1)
    module.image_name.value = IMAGE_NAME
    module.combine_or_split.value = cellprofiler.modules.colortogray.SPLIT
    module.rgb_or_channels.value = cellprofiler.modules.colortogray.CH_CHANNELS
    module.add_channel()
    module.add_channel()
    module.add_channel()
    module.add_channel()

    channel_indexes = numpy.array([1, 4, 2])
    for i, channel_index in enumerate(channel_indexes):
        module.channels[i].channel_choice.value = channel_index + 1
        module.channels[i].image_name.value = OUTPUT_IMAGE_F % i

    pipeline = cellprofiler_core.pipeline.Pipeline()

    def callback(caller, event):
        assert not isinstance(event, cellprofiler_core.pipeline.event.RunException)

    pipeline.add_listener(callback)
    pipeline.add_module(module)
    workspace = cellprofiler_core.workspace.Workspace(
        pipeline,
        module,
        image_set,
        cellprofiler_core.object.ObjectSet(),
        cellprofiler_core.measurement.Measurements(),
        image_set_list,
    )
    module.run(workspace)
    for i, channel_index in enumerate(channel_indexes):
        pixels = image_set.get_image(module.channels[i].image_name.value).pixel_data
        assert pixels.ndim == 2
        assert tuple(pixels.shape) == (20, 10)
        numpy.testing.assert_almost_equal(image[:, :, channel_index], pixels)

def test_old_color2gray():
    data = r"""CellProfiler Pipeline: http://www.cellprofiler.org
    Version:4
    DateRevision:318
    ModuleCount:12
    HasImagePlaneDetails:False

    ColorToGray bb:[module_num:6|svn_version:\'Unknown\'|variable_revision_number:3|show_window:False|notes:\x5B\x5D|batch_state:array(\x5B\x5D, dtype=uint8)|enabled:True|wants_pause:False]
    Select the input image:FullSpillCorr
    Conversion method:Split
    Image type:Channels
    Name the output image:OrigGray
    Relative weight of the red channel:1.0
    Relative weight of the green channel:1.0
    Relative weight of the blue channel:1.0
    Convert red to gray?:Yes
    Name the output image:OrigRed
    Convert green to gray?:Yes
    Name the output image:OrigGreen
    Convert blue to gray?:Yes
    Name the output image:OrigBlue
    Convert hue to gray?:Yes
    Name the output image:OrigHue
    Convert saturation to gray?:Yes
    Name the output image:OrigSaturation
    Convert value to gray?:Yes
    Name the output image:OrigValue
    Channel count:2
    Channel number:36
    Relative weight of the channel:1.0
    Image name:Er167
    Channel number:38
    Relative weight of the channel:1.0
    Image name:Tm169

    """
    pipeline = cellprofiler_core.pipeline.Pipeline()
    cpmodules.fill_modules()
    cpmodules.add_module_for_tst(colortogray.ColorToGray)
    pipeline.load(io.StringIO(data))
    assert len(pipeline.modules()) == 1
    smooth = pipeline.modules()[0]
    assert isinstance(smooth, colortogray.ColorToGray)
