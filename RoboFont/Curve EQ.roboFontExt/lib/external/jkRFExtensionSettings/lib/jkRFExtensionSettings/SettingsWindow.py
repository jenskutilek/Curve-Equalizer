from defconAppKit.windows.baseWindow import BaseWindowController
from mojo.extensions import getExtensionDefault, setExtensionDefault
import vanilla
from .Setting import Setting


class SettingsWindow(BaseWindowController):
    def __init__(self, extension_id, name, save_on_edit=False, analytics=None):
        self._extension_id = extension_id
        self._name = name
        self._save_on_edit = save_on_edit
        self.analytics = analytics
        self.settings_list = []
        self.settings = {}

        self.column = 80
        self.width = 300
        self.height = 200

    def add(self, settings_key, default_value, display_name=None):
        self.settings_list.append(settings_key)
        self.settings[settings_key] = Setting(
            settings_key, default_value, display_name
        )

    def _init_settings(self):
        self.settings_list = []
        self.settings = {}

    def _load_settings(self):
        for settings_key, setting in self.settings.items():
            self.settings[settings_key].value = getExtensionDefault(
                "%s.%s" % (self._extension_id, settings_key),
                setting.default_value,
            )

    def _save_settings(self):
        for settings_key, setting in self.settings.items():
            # print(
            #     "Saving", "%s.%s" % (
            #         self._extension_id, settings_key
            #     ), setting.value, setting.ui_object
            # )
            setExtensionDefault(
                "%s.%s" % (self._extension_id, settings_key), setting.value
            )

    def _build_ui(self):
        self.height = 20 + 26 * len(self.settings)
        self.w = vanilla.Window((self.width, self.height), self._name)
        i = 0
        for key in self.settings_list:
            setting = self.settings[key]
            ui_objects = []
            if type(setting.default_value) == bool:
                checkbox = vanilla.CheckBox(
                    (self.column + 10, 10 + 26 * i, -10, 22),
                    setting.name,
                    value=setting.value,
                    callback=self._edit_value,
                )
                setting.ui_object = checkbox
                ui_objects.append(checkbox)
            elif type(setting.default_value) == float:
                slider = vanilla.Slider(
                    (self.column + 10, 10 + 26 * i, -10, 22),
                    value=setting.value,
                    callback=self._edit_value,
                    continuous=False,
                )
                setting.ui_object = slider
                ui_objects.append(slider)
                ui_objects.append(
                    vanilla.TextBox(
                        (10, 10 + 26 * i, self.column, 22),
                        setting.name,
                    )
                )
            for j in range(len(ui_objects)):
                setattr(self.w, "%s_%i" % (setting.key, j), ui_objects[j])
            i += 1

    def _edit_value(self, sender):
        if self._save_on_edit:
            self._save_settings()
        if self.analytics:
            self.analytics.log("%s_%s" % (sender.getTitle(), sender.get()))

    def windowCloseCallback(self, sender):
        self._save_settings()
        if self.analytics:
            self.analytics.save()
        super(SettingsWindow, self).windowCloseCallback(sender)

    def show(self):
        self._load_settings()
        self._build_ui()
        self.setUpBaseWindowBehavior()
        if self.analytics:
            self.analytics.start_session()
        self.w.open()


def test():
    my_settings = SettingsWindow("de.kutilek.test", "My Settings", True)
    my_settings.add("mySlider", 0.0, "My Slider")
    my_settings.add("myCheckbox", True)
    my_settings.show()


if __name__ == "__main__":
    test()
