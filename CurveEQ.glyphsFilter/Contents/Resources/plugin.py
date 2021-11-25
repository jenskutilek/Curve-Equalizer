# encoding: utf-8
import objc

# from AppKit import NSMutableArray, NSNumber
from GlyphsApp import Glyphs
from GlyphsApp.plugins import FilterWithDialog

from baseCurveEqualizer import BaseCurveEqualizer
from EQExtensionID import extensionID


def fullkey(subkey):
    return f"{extensionID}.{subkey}"


METHOD_KEY = fullkey("method")
ADJUST_FREE_KEY = fullkey("curvatureFree")
TENSION_KEY = fullkey("tension")


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
        self.restore_state()
        self.update()

    @objc.python_method
    def restore_state(self):

        # Restore saved state

        # If we come in from an older version, the selected method index
        # may be out of range
        if not Glyphs.defaults[METHOD_KEY]:
            Glyphs.defaults[METHOD_KEY] = 0
        if Glyphs.defaults[METHOD_KEY] >= len(self.methods):
            Glyphs.defaults[METHOD_KEY] = 0

        self.paletteView.group.eqMethodSelector.set(
            Glyphs.defaults[METHOD_KEY]
        )
        self.method = self.methods[
            self.paletteView.group.eqMethodSelector.get()
        ]

        # default curvature for slider
        if not Glyphs.defaults[ADJUST_FREE_KEY]:
            Glyphs.defaults[ADJUST_FREE_KEY] = 0.5
        self.paletteView.group.eqCurvatureSlider.set(
            Glyphs.defaults[ADJUST_FREE_KEY]
        )

        # default curvature for Hobby's spline tension slider
        if not Glyphs.defaults[TENSION_KEY]:
            Glyphs.defaults[TENSION_KEY] = 0.5
        self.paletteView.group.eqHobbyTensionSlider.set(
            Glyphs.defaults[TENSION_KEY]
        )

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
