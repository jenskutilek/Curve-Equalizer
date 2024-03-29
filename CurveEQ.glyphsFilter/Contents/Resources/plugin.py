import objc

from GlyphsApp import GSOFFCURVE, Glyphs
from GlyphsApp.plugins import FilterWithDialog

from baseCurveEqualizer import BaseCurveEqualizer
from EQExtensionID import extensionID
from EQMethods import eqBalance, eqPercentage, eqSpline, eqThirds


def fullkey(subkey):
    return f"{extensionID}.{subkey}"


METHOD_KEY = fullkey("method")
ADJUST_KEY = fullkey("curvature")
ADJUST_FREE_KEY = fullkey("curvatureFree")
TENSION_KEY = fullkey("tension")


class CurveEQ(FilterWithDialog, BaseCurveEqualizer):
    @objc.python_method
    def settings(self):
        self.menuName = Glyphs.localize(
            {
                "en": "Curve Equalizer",
                "de": "Kurven-Equalizer",
                # "fr": "Mon filtre",
                # "es": "Mi filtro",
                # "pt": "Meu filtro",
                # "jp": "私のフィルター",
                # "ko": "내 필터",
                # "zh": "我的过滤器",
            }
        )

        # Word on Run Button (default: Apply)
        self.actionButtonLabel = Glyphs.localize(
            {
                "en": "Equalize selected",
                "de": "Auf Auswahl anwenden",
                "fr": "Appliquer",
                "es": "Aplicar",
                "pt": "Aplique",
                "jp": "申し込む",
                "ko": "대다",
                "zh": "应用",
            }
        )

        # Build UI
        self.build_ui(useFloatingWindow=False)
        self.dialog = self.paletteView.group.getNSView()

    # On dialog show
    @objc.python_method
    def start(self):
        # Set default value
        self.restore_state()
        self.check_ui_activation()
        # self.update()

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
        self.method = self.methods[Glyphs.defaults[METHOD_KEY]]

        # default curvature for radio buttons
        if not Glyphs.defaults[ADJUST_KEY]:
            Glyphs.defaults[ADJUST_KEY] = 0
        self.paletteView.group.eqCurvatureSelector.set(
            Glyphs.defaults[ADJUST_KEY]
        )

        # default curvature for slider
        if not Glyphs.defaults[ADJUST_FREE_KEY]:
            Glyphs.defaults[ADJUST_FREE_KEY] = 0.75
        self.paletteView.group.eqCurvatureSlider.set(
            Glyphs.defaults[ADJUST_FREE_KEY] * 100
        )

        # default curvature for Hobby's spline tension slider
        if not Glyphs.defaults[TENSION_KEY]:
            Glyphs.defaults[TENSION_KEY] = 0.75
        self.paletteView.group.eqHobbyTensionSlider.set(
            Glyphs.defaults[TENSION_KEY] * 100
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
        i = sender.get()
        m = self.methods[i]
        if m != self.method:
            self.method = m
            Glyphs.defaults[METHOD_KEY] = i
            self.check_ui_activation()
            self.update()

    @objc.python_method
    def _changeCurvature(self, sender):
        Glyphs.defaults[ADJUST_KEY] = sender.get()
        self.update()

    @objc.python_method
    def _changeCurvatureFree(self, sender):
        Glyphs.defaults[ADJUST_FREE_KEY] = sender.get() / 100
        self.update()

    @objc.python_method
    def _changeTension(self, sender):
        Glyphs.defaults[TENSION_KEY] = sender.get() / 100
        self.update()

    @objc.python_method
    def check_ui_activation(self):
        m = self.method
        if m == "free":
            self.paletteView.group.eqCurvatureSelector.enable(False)
            self.paletteView.group.eqCurvatureSlider.enable(True)
            self.paletteView.group.eqHobbyTensionSlider.enable(False)
        elif m == "hobby":
            self.paletteView.group.eqCurvatureSelector.enable(False)
            self.paletteView.group.eqCurvatureSlider.enable(False)
            self.paletteView.group.eqHobbyTensionSlider.enable(True)
        elif m == "adjust":
            self.paletteView.group.eqCurvatureSelector.enable(True)
            self.paletteView.group.eqCurvatureSlider.enable(False)
            self.paletteView.group.eqHobbyTensionSlider.enable(False)
        else:
            self.paletteView.group.eqCurvatureSelector.enable(False)
            self.paletteView.group.eqCurvatureSlider.enable(False)
            self.paletteView.group.eqHobbyTensionSlider.enable(False)

    @objc.python_method
    def filter(self, layer, inEditView, customParameters):

        # Called on font export, get value from customParameters
        if customParameters:
            print("Curve Equalizer should not be used on export.")
            return

        segments = []
        for path in layer.paths:
            node_index = 0
            for node_index, n in enumerate(path.nodes):
                if n.type == GSOFFCURVE:
                    # Skip first offcurve
                    if path.nodeAtIndex_(node_index + 1).type == GSOFFCURVE:
                        continue

                    if n in layer.selection:
                        segments.append(
                            [
                                path.nodeAtIndex_(node_index - 2),
                                path.nodeAtIndex_(node_index - 1),
                                n,
                                path.nodeAtIndex_(node_index + 1),
                            ]
                        )

        if self.method == "balance":
            [self.balance_segment(s) for s in segments]
        elif self.method == "adjust":
            [self.adjust_segment(s) for s in segments]
        elif self.method == "free":
            [self.adjust_free_segment(s) for s in segments]
        elif self.method == "hobby":
            [self.adjust_tension_segment(s) for s in segments]
        elif self.method == "fl":
            [self.fl_segment(s) for s in segments]
        elif self.method == "thirds":
            [self.thirds_segment(s) for s in segments]
        else:
            print(f"WARNING: Unknown equalize method: {self.method}")

    @objc.python_method
    def adjust_segment(self, segment):
        # Adjust fixed
        p0, p1, p2, p3 = segment
        eqPercentage(p0, p1, p2, p3, self.curvatures[Glyphs.defaults[ADJUST_KEY]])

    @objc.python_method
    def adjust_free_segment(self, segment):
        # Adjust free
        p0, p1, p2, p3 = segment
        eqPercentage(p0, p1, p2, p3, Glyphs.defaults[ADJUST_FREE_KEY])

    @objc.python_method
    def adjust_tension_segment(self, segment):
        # Adjust Hobby
        p0, p1, p2, p3 = segment
        eqSpline(p0, p1, p2, p3, Glyphs.defaults[TENSION_KEY])

    @objc.python_method
    def balance_segment(self, segment):
        # Balance handles
        p0, p1, p2, p3 = segment
        eqBalance(p0, p1, p2, p3)

    @objc.python_method
    def fl_segment(self, segment):
        # Apply FL circle fitting
        p0, p1, p2, p3 = segment
        eqPercentage(p0, p1, p2, p3)

    @objc.python_method
    def thirds_segment(self, segment):
        # Apply rule of thirds
        p0, p1, p2, p3 = segment
        eqThirds(p0, p1, p2, p3)

    @objc.python_method
    def __file__(self):
        """Please leave this method unchanged"""
        return __file__
