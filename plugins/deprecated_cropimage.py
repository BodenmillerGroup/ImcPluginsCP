import logging

from cellprofiler_core.setting import HTMLText

from cropimage import CropImage

DEPRECATION_STRING = """
                This module changed names, now it is called:\n
                'CropImage' (Note lack of space).\n
                If you save and reopen this pipeline it will automatically migrated
                to the correct module.\n
                This module will be removed with the next major ImcPluginsCP release!
                """


class Deprecated_CropImage(CropImage):
    module_name = "Crop bb"
    category = "Deprecated"
    variable_revision_number = 3

    deprecation_warning = HTMLText(
        text="Deprecation Warning",
        content=DEPRECATION_STRING,
        doc=DEPRECATION_STRING,
        size=(10, 5),
    )

    def visible_settings(self):
        result = super().visible_settings()
        return [self.deprecation_warning] + result

    def upgrade_settings(self, setting_values, variable_revision_number, module_name):
        self.module_name = super().module_name
        return super().upgrade_settings(
            setting_values, variable_revision_number, module_name
        )
