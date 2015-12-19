from EQExtensionID import extensionID
from jkRFExtensionSettings.SettingsWindow import SettingsWindow

my_settings = SettingsWindow(extensionID, "Curve Equalizer Settings", True)

my_settings.column = 8
my_settings.width = 276

my_settings.add("previewCurves", False, "Always show curve preview")
my_settings.add("previewHandles", False, "Always show handle preview")
my_settings.add("drawGeometry", False, "Draw triangle geometry")
my_settings.add("stats", True, "Send debugging and usage statistics")
my_settings.add("debug", False, "Run in debug mode")

my_settings.show()