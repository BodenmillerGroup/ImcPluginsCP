# coding=utf-8

"""
ColorToGray
===========

**ColorToGray** converts an image with multiple color channels to one or more
grayscale images.

This module converts color and channel-stacked
images to grayscale. All channels can be merged into one grayscale image
(*Combine*), or each channel can be extracted into a separate grayscale image
(*Split*). If you use *Combine*, the relative weights you provide allow
adjusting the contribution of the colors relative to each other.
Note that all **Identify** modules require grayscale images.

|

============ ============ ===============
Supports 2D? Supports 3D? Respects masks?
============ ============ ===============
YES          NO           NO
============ ============ ===============

See also
^^^^^^^^

See also **GrayToColor**.
"""

import cellprofiler.modules.colortogray

YES = "Yes"
NO = "No"
NONE = "None"

COMBINE = "Combine"
SPLIT = "Split"

CH_RGB = "RGB"
CH_HSV = "HSV"
CH_CHANNELS = "Channels"

MAX_CHANNELS_PER_IMAGE = 60
SLOT_CHANNEL_COUNT = 19
SLOT_FIXED_COUNT = 20
SLOTS_PER_CHANNEL = 3
SLOT_CHANNEL_CHOICE = 0

from cellprofiler_core.setting import HTMLText

DEPRECATION_STRING = """
                The ColorToGray bb module is deprecated as the
                functionality is now integrated into the default ColorToGray.\n
                If you save and reopen this pipeline it will automatically migrated
                to the standard ColorToGray module.\n
                This module will be removed with the next major ImcPluginsCP release!
                """


class Deprecated_ColorToGrayBB(cellprofiler.modules.colortogray.ColorToGray):
    module_name = "ColorToGray bb"
    variable_revision_number = 3
    category = "Deprecated"

    deprecation_warning = HTMLText(
        text="Deprecation Warning", content=DEPRECATION_STRING, doc=DEPRECATION_STRING
    )

    def visible_settings(self):
        result = super().visible_settings()
        return [self.deprecation_warning] + result

    def upgrade_settings(self, setting_values, variable_revision_number, module_name):
        module_name = "ColorToGray"
        self.module_name = module_name
        return super().upgrade_settings(
            setting_values, variable_revision_number, module_name
        )
