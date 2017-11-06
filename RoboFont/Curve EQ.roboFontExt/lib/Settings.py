from EQExtensionID import extensionID

# Make jkRFExtensionSettings importable
from os.path import dirname, join
import sys
sys.path.append(join(dirname(__file__), "external", "jkRFExtensionSettings", "lib"))

from jkRFExtensionSettings.SettingsWindow import SettingsWindow

my_settings = SettingsWindow(extensionID, "Curve Equalizer Settings", True)

my_settings.column = 8
my_settings.width = 276

my_settings.add("previewCurves", False, "Always show curve preview")
my_settings.add("previewHandles", False, "Always show handle preview")
my_settings.add("drawGeometry", False, "Draw triangle geometry")
my_settings.add("debug", False, "Run in debug mode")

my_settings.show()
