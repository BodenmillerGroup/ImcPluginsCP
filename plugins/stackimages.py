# coding=utf-8

"""
Stackimages
===========
TODO: Improve documentation
**StackImages** takes a grayscale or color images and stacks them.

============ ============ ===============
Supports 2D? Supports 3D? Respects masks?
============ ============ ===============
YES          NO           NO
============ ============ ===============

See also
^^^^^^^^

See also **ColorToGray** and **GrayToColor**.
"""
# This is almost 1:1 copied from GrayToColor from CellProfiler
import numpy as np

import cellprofiler_core.image as cpi
import cellprofiler_core.module as cpm
import cellprofiler_core.setting as cps

OFF_STACK_CHANNEL_COUNT = 1

NONE = 'None'

class StackImages(cpm.Module):
    module_name = "StackImages"
    variable_revision_number = 2
    category = "Image Processing"

    def create_settings(self):

        # # # # # # # # # # # # # #
        #
        # Stack settings
        #
        # # # # # # # # # # # # # #
        self.stack_image_name = cps.text.ImageName(
            "Name the output image",
            "ColorImage",
            doc="""Enter a name for the resulting image.""",
        )

        self.stack_channels = []
        self.stack_channel_count = cps.HiddenCount(self.stack_channels)
        self.add_stack_channel_cb(can_remove=False)
        self.add_stack_channel_cb(can_remove=False)
        self.add_stack_channel = cps.do_something.DoSomething(
            "Add another channel",
            "Add another channel",
            self.add_stack_channel_cb,
            doc="""\
    Press this button to add another image to the stack.
    """,
        )

    def add_stack_channel_cb(self, can_remove=True):
        group = cps.SettingsGroup()
        group.append(
            "image_name",
            cps.subscriber.ImageSubscriber(
                "Image name",
                NONE,
                doc="""\
Select the input image to add to the stacked image.
"""
                % globals(),
            ),
        )

        if can_remove:
            group.append(
                "remover",
                cps.do_something.RemoveSettingButton(
                    "", "Remove this image", self.stack_channels, group
                ),
            )
        self.stack_channels.append(group)

    def settings(self):
        result = [self.stack_image_name, self.stack_channel_count]
        for stack_channel in self.stack_channels:
            result += [stack_channel.image_name]
        return result

    def prepare_settings(self, setting_values):
        num_stack_images = int(setting_values[OFF_STACK_CHANNEL_COUNT])
        # Why is the following needed? Taken over from graytocolor but
        # I do not see that this would be actually needed...
        del self.stack_channels[num_stack_images:]
        while len(self.stack_channels) < num_stack_images:
            self.add_stack_channel_cb()

    def visible_settings(self):
        result = [self.stack_image_name]
        for sc_group in self.stack_channels:
            result.append(sc_group.image_name)
            if hasattr(sc_group, "remover"):
                result.append(sc_group.remover)
        result += [self.add_stack_channel]
        return result

    def validate_module(self, pipeline):
        """
        nothing to do at the moment
        """
        pass

    def run(self, workspace):
        parent_image = None
        parent_image_name = None
        imgset = workspace.image_set
        stack_pixel_data = None
        input_image_names = []
        channel_names = []
        input_image_names = [sc.image_name.value for sc in self.stack_channels]
        channel_names = input_image_names
        source_channels = [
            imgset.get_image(name, must_be_grayscale=False).pixel_data
            for name in input_image_names
        ]
        parent_image = imgset.get_image(input_image_names[0])
        for idx, pd in enumerate(source_channels):
            if pd.shape[:2] != source_channels[0].shape[:2]:
                raise ValueError(
                    "The %s image and %s image have different sizes (%s vs %s)"
                    % (
                        self.stack_channels[0].image_name.value,
                        self.stack_channels[idx].image_name.value,
                        source_channels[0].shape[:2],
                        pd.pixel_data.shape[:2],
                    )
                )
        stack_pixel_data = np.dstack(source_channels)

        ##############
        # Save image #
        ##############
        stack_image = cpi.Image(stack_pixel_data, parent_image=parent_image)
        stack_image.channel_names = channel_names
        imgset.add(self.stack_image_name.value, stack_image)

        ##################
        # Display images #
        ##################
        if self.show_window:
            workspace.display_data.input_image_names = input_image_names
            workspace.display_data.stack_pixel_data = stack_pixel_data
            workspace.display_data.images = [
                imgset.get_image(name, must_be_grayscale=False).pixel_data
                for name in input_image_names
            ]

    def display(self, workspace, figure):
        # TODO: do a meaningfull display
        input_image_names = workspace.display_data.input_image_names
        images = workspace.display_data.images
        nsubplots = len(input_image_names)
        subplots = (min(nsubplots + 1, 4), int(nsubplots / 4) + 1)
        subplot_indices = [(i % 4, int(i / 4)) for i in range(nsubplots)]
        color_subplot = (nsubplots % 4, int(nsubplots / 4))
        figure.set_subplots(subplots)
        for i, (input_image_name, image_pixel_data) in enumerate(
            zip(input_image_names, images)
        ):
            x, y = subplot_indices[i]
            # figure.subplot_imshow_grayscale(x, y, image_pixel_data,
            #                                title=input_image_name,
            #                                sharexy=figure.subplot(0, 0))
            # figure.subplot(x, y).set_visible(True)
        for x, y in subplot_indices[len(input_image_names) :]:
            figure.subplot(x, y).set_visible(False)
        # figure.subplot_imshow(color_subplot[0], color_subplot[1],
        #                      workspace.display_data.stack_pixel_data[:, :, :3],
        #                      title=self.stack_image_name.value,
        #                      sharexy=figure.subplot(0, 0))

    def upgrade_settings(
        self, setting_values, variable_revision_number, module_name
    ):
        return setting_values, variable_revision_number
