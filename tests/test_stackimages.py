"""test_stackimages.py - test the stackimages module
"""

import unittest

import numpy as np

from cellprofiler_core.preferences import set_headless

set_headless()

import cellprofiler_core.workspace as cpw
import cellprofiler_core.image as cpi
import cellprofiler_core.object as cpo
import cellprofiler_core.pipeline as cpp
import cellprofiler_core.measurement as cpmeas

import plugins.stackimages as S

INPUT_IMAGE_BASENAME = "myimage"

OUTPUT_IMAGE_NAME = "mystackedimage"


class TestStackImages(unittest.TestCase):
    def make_workspace(self, images):
        """Make a workspace """
        module = S.StackImages()
        pipeline = cpp.Pipeline()
        object_set = cpo.ObjectSet()
        image_set_list = cpi.ImageSetList()
        image_set = image_set_list.get_image_set(0)
        workspace = cpw.Workspace(
            pipeline,
            module,
            image_set,
            object_set,
            cpmeas.Measurements(),
            image_set_list,
        )

        # setup the input images
        names = [INPUT_IMAGE_BASENAME + str(i) for i, img in enumerate(images)]
        for img, nam in zip(images, names):
            image_set.add(nam, cpi.Image(img))

        # setup the input images settings
        module.stack_image_name.value = OUTPUT_IMAGE_NAME
        nimgs = len(images)
        while len(module.stack_channels) < nimgs:
            module.add_stack_channel_cb()
        for sc, imname in zip(module.stack_channels, names):
            sc.image_name.value = imname

        return workspace, module

    def assert_stack(self, images, result):
        # test if this is equal to the stacked images
        lb = 0
        for im in images:
            if len(im.shape) > 2:
                offset = im.shape[2]
            else:
                offset = 1
            ub = lb + offset
            np.testing.assert_equal(np.squeeze(result.pixel_data[:, :, lb:ub]), im)
            lb = ub

    def assert_shape(self, images, result):
        new_shape = list(images[0].shape)[:2]
        c = 0
        for im in images:
            if len(im.shape) > 2:
                c += im.shape[2]
            else:
                c += 1
        new_shape += [c]
        np.testing.assert_equal(result.pixel_data.shape, new_shape)

    def test_stack_multichannel(self):
        img_shape = (10, 10, 5)
        image1 = np.zeros(img_shape)
        image2 = np.copy(image1)
        image2[:] = 1
        input_imgs = [image1, image2]
        workspace, module = self.make_workspace(input_imgs)
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assert_stack(input_imgs, result)
        self.assert_shape(input_imgs, result)

    def test_stack_multi_gray(self):
        img_shape = (10, 10, 5)
        image1 = np.zeros(img_shape)
        image1[:] = 1
        img_shape2 = (10, 10)
        image2 = np.zeros(img_shape2)
        input_imgs = [image1, image2]
        workspace, module = self.make_workspace(input_imgs)
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assert_stack(input_imgs, result)
        self.assert_shape(input_imgs, result)

    def test_stack_gray(self):
        img_shape = (10, 10)
        image1 = np.zeros(img_shape)
        image2 = np.copy(image1)
        image2[:] = 1
        input_imgs = [image1, image2]
        workspace, module = self.make_workspace(input_imgs)
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assert_stack(input_imgs, result)
        self.assert_shape(input_imgs, result)

    def test_stack_3multichannel(self):
        nimgs = 5
        img_shape = (10, 10, 5)
        image = np.zeros(img_shape)
        input_imgs = []
        for i in range(nimgs):
            img = np.copy(image)
            img[:] = i
            input_imgs.append(img)
        workspace, module = self.make_workspace(input_imgs)
        module.run(workspace)
        result = workspace.image_set.get_image(OUTPUT_IMAGE_NAME)
        self.assert_stack(input_imgs, result)
        self.assert_shape(input_imgs, result)
