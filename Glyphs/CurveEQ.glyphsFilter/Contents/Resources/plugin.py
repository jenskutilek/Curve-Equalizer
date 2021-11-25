#!/usr/bin/env python
# encoding: utf-8

import objc
from AppKit import NSBundle, NSLog, NSMutableArray, NSNumber
from GlyphsApp import Glyphs
from GlyphsApp.plugins import FilterWithDialog

from eqmath import BaseCurveEqualizer

"""
    Using Interface Builder (IB):

    Your code communicates with the UI through
    - IBOutlets (.py->GUI): values available to a UI element (e.g. a string for
      a text field)
    - IBActions (GUI->.py): methods in this class, triggered by buttons or
      other UI elements

    In order to make the Interface Builder items work, follow these steps:
    1. Make sure you have your IBOutlets (other than _theView)
       defined as class variables at the beginning of this controller class.
    2. Immediately *before* the def statement of a method that is supposed to
       be triggered by a UI action (e.g., setMyValue_() triggered by the My
       Value field), put:
        @objc.IBAction
       Make sure the method name ends with an underscore, e.g. setValue_(),
       otherwise the action will not be able to send its value to the class
       method.
    3. Open the .xib file in XCode, and add and arrange interface elements.
    4. Add this .py file via File > Add Files..., Xcode will recognize
       IBOutlets and IBACtions
    5. In the left sidebar, choose Placeholders > File's Owner,
       in the right sidebar, open the Identity inspector (3rd icon),
       and put the name of this controller class in the Custom Class > Class
       field
    6. IBOutlets: Ctrl-drag from the File's Owner to a UI element (e.g. text
       field),
       and choose which outlet shall be linked to the UI element
    7. IBActions: Ctrl-drag from a UI element (e.g. button) to the File’s Owner
       in the left sidebar, and choose the class method the UI element is
    supposed to trigger.
       If you want a stepping field (change the value with up/downarrow),
       then select the Entry Field, and set Identity Inspector > Custom Class
       to:
        GSSteppingTextField
       ... and Attributes Inspector (top right, 4th icon) > Control > State to:
        Continuous
    8. Compile the .xib file to a .nib file with this Terminal command:
        ibtool xxx.xib --compile xxx.nib
       (Replace xxx by the name of your xib/nib)
       Please note: Every time the .xib is changed, it has to be recompiled to
       a .nib.
       Check Console.app for error messages to see if everything went right.
"""


class CurveEQ(FilterWithDialog):

    # Definitions of IBOutlets

    # The NSView object from the User Interface. Keep this here!
    dialog = objc.IBOutlet()

    modeSelect = objc.IBOutlet()
    adjustSlider = objc.IBOutlet()
    hobbySlider = objc.IBOutlet()
    freeAdjustMin = objc.IBOutlet()
    freeAdjustMax = objc.IBOutlet()
    tensionMin = objc.IBOutlet()
    tensionMax = objc.IBOutlet()

    @objc.python_method
    def settings(self):
        self.menuName = Glyphs.localize({
            "en": "Curve Equalizer",
            "de": "Kurven-Equalizer",
            # "fr": "Mon filtre",
            # "es": "Mi filtro",
            # "pt": "Meu filtro",
            # "jp": "私のフィルター",
            # "ko": "내 필터",
            # "zh": "我的过滤器",
        })

        # Word on Run Button (default: Apply)
        self.actionButtonLabel = Glyphs.localize({
            "en": "Equalize selected",
            "de": "Anwenden",
            "fr": "Appliquer",
            "es": "Aplicar",
            "pt": "Aplique",
            "jp": "申し込む",
            "ko": "대다",
            "zh": "应用",
        })

        # Load dialog from .nib (without .extension)
        self.loadNib("IBdialog", __file__)

    # On dialog show
    @objc.python_method
    def start(self):
        # Set default value
        Glyphs.registerDefault("de.kutilek.CurveHQ.freeAdjustMin", 10)
        Glyphs.registerDefault("de.kutilek.CurveHQ.freeAdjustMax", 100)

        # Set value of text field
        # self.myTextField.setStringValue_(
        #     Glyphs.defaults['com.myname.myfilter.value']
        # )

        # Set focus to text field
        # self.myTextField.becomeFirstResponder()

    # def keyEquivalent(self):
    #     """
    #     The key together with Cmd+Shift will be the shortcut for the filter.
    #     Return None if you do not want to set a shortcut.
    #     Users can set their own shortcuts in System Prefs.
    #     """
    #     try:
    #         return None
    #     except Exception as e:
    #         self.logToConsole("keyEquivalent: %s" % str(e))

    # Action triggered by UI
    @objc.IBAction
    def adjustFree_(self, sender):
        print("__adjustSlider_", sender.floatValue())
        # Store value coming in from dialog
        Glyphs.defaults['de.kutilek.CurveHQ.adjustFree'] = sender.floatValue()

        # Trigger redraw
        self.update()

    @objc.IBAction
    def adjustHobby_(self, sender):
        print("__adjustHobby_", sender.floatValue())
        # Store value coming in from dialog
        Glyphs.defaults['de.kutilek.CurveHQ.adjustHobby'] = sender.floatValue()

        # Trigger redraw
        self.update()

    @objc.IBAction
    def selectMode_(self, sender):
        print("__selectMode_", sender, sender.selectedRow())
        try:
            self.adjustSlider.setEnabled_(sender.selectedRow() == 0)
            self.hobbySlider.setEnabled_(sender.selectedRow() == 1)
            self.quadraticSlider.setEnabled_(sender.selectedRow() == 3)

        except Exception as e:
            self.logToConsole("selectMode_: %s" % str(e))

    def processLayerWithValues(self, Layer, myValue, NochWas,):
        """
        This is where your code for processing each layer goes.
        This method is the one eventually called by either the Custom Parameter
        or Dialog UI. Don't call your class variables here, just add a method
        argument for each Dialog option.
        """
        try:
            # do stuff with Layer and your arguments
            pass
        except Exception as e:
            self.logToConsole("processLayerWithValues: %s" % str(e))

    # Actual filter
    @objc.python_method
    def filter(self, layer, inEditView, customParameters):

        # Called on font export, get value from customParameters
        if "adjustFree" in customParameters:
            value = customParameters["adjustFree"]

        # Called through UI, use stored value
        else:
            value = float(Glyphs.defaults["de.kutilek.CurveEQ.adjustFree"])

        # Shift all nodes in x and y direction by the value
        # for path in layer.paths:
        #     for node in path.nodes:
        #         node.position = NSPoint(
        #             node.position.x + value, node.position.y + value
        #         )

        return

        try:
            # Create Preview in Edit View, and save & show original in
            # ShadowLayers:
            ShadowLayers = self.valueForKey_("shadowLayers")
            Layers = self.valueForKey_("layers")
            checkSelection = True
            for k in range(len(ShadowLayers)):
                ShadowLayer = ShadowLayers[k]
                Layer = Layers[k]
                Layer.setPaths_(
                    NSMutableArray.alloc().initWithArray_copyItems_(
                        ShadowLayer.pyobjc_instanceMethods.paths(), True
                    )
                )
                Layer.setSelection_(NSMutableArray.array())
                if len(ShadowLayer.selection()) > 0 and checkSelection:
                    for i in range(len(ShadowLayer.paths)):
                        currShadowPath = ShadowLayer.paths[i]
                        currLayerPath = Layer.paths[i]
                        for j in range(len(currShadowPath.nodes)):
                            currShadowNode = currShadowPath.nodes[j]
                            if ShadowLayer.selection().containsObject_(
                                currShadowNode
                            ):
                                Layer.addSelection_(currLayerPath.nodes[j])
                # add your class variables here
                self.processLayerWithValues(Layer, self.myValue)
            Layer.clearSelection()

            # Safe the values in the FontMaster. But could be saved in
            # UserDefaults, too.
            FontMaster = self.valueForKey_("fontMaster")
            FontMaster.userData["myValue"] = NSNumber.numberWithInteger_(
                self.myValue
            )

            # call the superclass to trigger the immediate redraw:
            super(CurveEQ, self).process_(sender)
        except Exception as e:
            self.logToConsole("process_: %s" % str(e))

    def logToConsole(self, message):
        """
        The variable "message" will be passed to Console.app.
        Use self.logToConsole("bla bla") for debugging.
        """
        myLog = "Filter %s:\n%s" % (self.title(), message)
        NSLog(myLog)

    @objc.python_method
    def generateCustomParameter(self):
        return "%s; shift:%s;" % (
            self.__class__.__name__,
            Glyphs.defaults["com.myname.myfilter.shift"]
        )

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
