from Analytics import Analytics
from EQExtensionID import extensionID

# Make jkRFExtensionSettings importable
from os.path import dirname, join
from sys.path import append
append(join(dirname(__file__), "externals", "jkRFExtensionSettings", "lib"))

from jkRFExtensionSettings.SettingsWindow import SettingsWindow

my_settings = SettingsWindow(extensionID, "Curve Equalizer Settings", True, Analytics())

my_settings.column = 8
my_settings.width = 276

my_settings.add("previewCurves", False, "Always show curve preview")
my_settings.add("previewHandles", False, "Always show handle preview")
my_settings.add("drawGeometry", False, "Draw triangle geometry")
#my_settings.add("stats", True, "Send debugging and usage statistics")
my_settings.add("debug", False, "Run in debug mode")

my_settings.show()
