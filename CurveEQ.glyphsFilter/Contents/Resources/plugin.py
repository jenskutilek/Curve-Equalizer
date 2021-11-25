# encoding: utf-8
import objc

# from AppKit import NSMutableArray, NSNumber
from GlyphsApp import Glyphs, GSCURVE, GSLINE
from GlyphsApp.plugins import FilterWithDialog

from baseCurveEqualizer import BaseCurveEqualizer
from EQExtensionID import extensionID
from EQMethods import eqBalance, eqPercentage, eqSpline


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
            "de": "Auf Auswahl anwenden",
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

    @objc.method
    def read_selection(self, layer):
        self.segments = []
        for p in layer.paths:
            segment = []
            seenOnCurve = False
            for n in p.nodes:
                if n.selected:
                    if seenOnCurve:
                        if n.type == GSCURVE:
                            if segment:
                                # End segment
                                segment.append(n)
                                self.segments.append(segment)
                                segment = [n]
                        else:
                            segment.append(n)
                    else:
                        if n.type in (GSCURVE, GSLINE):
                            # Start of selected segment
                            seenOnCurve = True
                            segment.append(n)
                else:
                    if segment:
                        # Remove "dangling" selection
                        segment = []

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

    # Callbacks

    @objc.python_method
    def _changeMethod(self, sender):
        Glyphs.defaults[METHOD_KEY] = sender.get()
        self.update()

    @objc.python_method
    def _changeCurvatureFree(self, sender):
        Glyphs.defaults[ADJUST_FREE_KEY] = sender.get()
        self.update()

    @objc.python_method
    def _changeTension(self, sender):
        Glyphs.defaults[TENSION_KEY] = sender.get()
        self.update()

    @objc.python_method
    def filter(self, layer, inEditView, customParameters):

        # Called on font export, get value from customParameters
        if customParameters:
            print("Curve Equalizer should not be used on export.")
            return

        self.read_selection(layer)

        if self.method == "balance":
            [self.balance_segment(s) for s in self.segments]
        elif self.method == "free":
            [self.adjust_segment(s) for s in self.segments]
        elif self.method == "hobby":
            [self.adjust_tension_segment(s) for s in self.segments]
        else:
            print(f"WARNING: Unknown equalize method: {self.method}")

    @objc.python_method
    def balance_segment(self, segment):
        # Balance handles
        p0, p1, p2, p3 = segment
        eqBalance(p0, p1, p2, p3)

    @objc.python_method
    def adjust_segment(self, segment):
        # Adjust free
        p0, p1, p2, p3 = segment
        eqPercentage(p0, p1, p2, p3, Glyphs.defaults[ADJUST_FREE_KEY])

    @objc.python_method
    def adjust_tension_segment(self, segment):
        # Adjust Hobby
        p0, p1, p2, p3 = segment
        eqSpline(p0, p1, p2, p3, Glyphs.defaults[TENSION_KEY])

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
