import logging

from cellprofiler_core.setting import HTMLText

from measureimageintensitymultichannel import MeasureImageIntensityMultiChannel

DEPRECATION_STRING = """
                This module changed names, now it is called:
                'MeasureImageIntensityMultiChannel' (Note lack of space).
                If you save and reopen this pipeline it will automatically migrated
                to the correct module.
                This module will be removed with the next major ImcPluginsCP release!
                """


class Deprecated_MeasureImageIntensityMultiChannel(MeasureImageIntensityMultiChannel):
    module_name = "MeasureImageIntensity Multichannel"
    category = "Deprecated"
    variable_revision_number = 3

    deprecation_warning = HTMLText(
        text="Deprecation Warning", content=DEPRECATION_STRING, doc=DEPRECATION_STRING
    )

    def visible_settings(self):
        result = super().visible_settings()
        return [self.deprecation_warning] + result

    def upgrade_settings(self, setting_values, variable_revision_number, module_name):
        self.module_name = super().module_name
        return super().upgrade_settings(
            setting_values, variable_revision_number, module_name
        )
