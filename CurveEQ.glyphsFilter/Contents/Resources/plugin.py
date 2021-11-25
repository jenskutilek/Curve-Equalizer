# encoding: utf-8
import objc

# from AppKit import NSMutableArray, NSNumber
from GlyphsApp import Glyphs
from GlyphsApp.plugins import FilterWithDialog

from baseCurveEqualizer import BaseCurveEqualizer
from EQExtensionID import extensionID


def fullkey(subkey):
    return f"{extensionID}.{subkey}"


class CurveEQ(FilterWithDialog, BaseCurveEqualizer):
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

        # Build UI
        self.build_ui()
        self.dialog = self.paletteView.group.getNSView()

    # On dialog show
    @objc.python_method
    def start(self):
        # Set default value
        # self.restore_state()
        pass

    @objc.python_method
    def restore_state(self):

        # Restore saved state

        # If we come in from an older version, the selected method index
        # may be out of range
        if not Glyphs.defaults[fullkey("method")]:
            Glyphs.defaults[fullkey("method")] = 0
        if Glyphs.defaults[fullkey("method")] >= len(self.methods):
            Glyphs.defaults[fullkey("method")] = 0

        self.w.group.eqMethodSelector.set(
            Glyphs.defaults[fullkey("method")]
        )
        self.method = self.methods[self.w.group.eqMethodSelector.get()]

        # default curvature for slider
        if not Glyphs.defaults[fullkey("curvatureFree")]:
            Glyphs.defaults[fullkey("curvatureFree")] = 0.5
        self.w.group.eqCurvatureSlider.set(
            Glyphs.defaults[fullkey("curvatureFree")]
        )
        self.curvatureFree = self.w.group.eqCurvatureSlider.get()

        # default curvature for Hobby's spline tension slider
        if not Glyphs.defaults[fullkey("tension")]:
            Glyphs.defaults[fullkey("tension")] = 0.5
        self.w.group.eqHobbyTensionSlider.set(
            Glyphs.defaults[fullkey("tension")]
        )
        self.tension = self.w.group.eqHobbyTensionSlider.get()

        # load preview options
        if not Glyphs.defaults[fullkey("previewCurves")]:
            Glyphs.defaults[fullkey("previewCurves")] = False
        self.alwaysPreviewCurves = Glyphs.defaults[fullkey("previewCurves")]

        if not Glyphs.defaults[fullkey("previewHandles")]:
            Glyphs.defaults[fullkey("previewHandles")] = False
        self.alwaysPreviewHandles = Glyphs.defaults[fullkey("previewHandles")]

        self._setPreviewOptions()

        if not Glyphs.defaults[fullkey("drawGeometry")]:
            Glyphs.defaults[fullkey("drawGeometry")] = False
        self.drawGeometry = Glyphs.defaults[fullkey("drawGeometry")]

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
    # def adjustFree_(self, sender):
    #     print("__adjustSlider_", sender.floatValue())
    #     # Store value coming in from dialog
    #     Glyphs.defaults['de.kutilek.CurveHQ.adjustFree'] = sender.floatValue()

    #     # Trigger redraw
    #     self.update()

    # def adjustHobby_(self, sender):
    #     print("__adjustHobby_", sender.floatValue())
    #     # Store value coming in from dialog
    #     Glyphs.defaults['de.kutilek.CurveHQ.adjustHobby'] = sender.floatValue()

    #     # Trigger redraw
    #     self.update()

    # def selectMode_(self, sender):
    #     print("__selectMode_", sender, sender.selectedRow())
    #     try:
    #         self.adjustSlider.setEnabled_(sender.selectedRow() == 0)
    #         self.hobbySlider.setEnabled_(sender.selectedRow() == 1)
    #         self.quadraticSlider.setEnabled_(sender.selectedRow() == 3)

    #     except Exception as e:
    #         self.logToConsole("selectMode_: %s" % str(e))

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
        """
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
            # super(CurveEQ, self).process_(sender)
        except Exception as e:
            self.logToConsole("process_: %s" % str(e))
        """

    @objc.python_method
    def generateCustomParameter(self):
        return "%s; adjustFree:%s;" % (
            self.__class__.__name__,
            Glyphs.defaults[fullkey("adjustFree")]
        )

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
