from __future__ import annotations

import logging

from vanilla import Button, FloatingWindow, Group, RadioGroup, Slider, Window


logger = logging.getLogger(__name__)


class BaseCurveEqualizer:
    def build_ui(self, useFloatingWindow: bool = True) -> None:
        self.methods = {
            0: "fl",
            1: "thirds",
            2: "balance",
            3: "adjust",
            4: "free",
            5: "hobby",
        }

        self.methodNames = [
            "Circle",
            "Thirds",
            "Balance",
            "Fixed:",
            "Adjust:",
            "Hobby:",
        ]

        self.curvatures = {
            0: 0.552,
            1: 0.577,
            2: 0.602,
            3: 0.627,
            4: 0.652,
        }

        height = 180
        width = 200
        sliderX = 76

        if useFloatingWindow:
            self.paletteView = FloatingWindow(
                posSize=(width, height),
                title="Curve EQ",
                minSize=(width, height + 16),
                maxSize=(1000, height + 16),
            )
        else:
            self.paletteView = Window((width, height))

        self.paletteView.group = Group((0, 0, -0, -0))

        y = 8
        self.paletteView.group.eqMethodSelector = RadioGroup(
            (8, y, -8, -36),
            titles=self.methodNames,
            callback=self._changeMethod,
            sizeStyle="small",
        )

        y = 76
        self.paletteView.group.eqCurvatureSelector = RadioGroup(
            (sliderX, y, -0, 17),
            isVertical=False,
            titles=[
                "",
                "",
                "",
                "",
            ],
            callback=self._changeCurvature,
            sizeStyle="small",
        )

        y += 21
        self.paletteView.group.eqCurvatureSlider = Slider(
            (sliderX, y, -8, 17),
            callback=self._changeCurvatureFree,
            minValue=50,
            maxValue=100,
            value=75,  # Will be replaced by saved value
            sizeStyle="small",
        )

        y += 23
        self.paletteView.group.eqHobbyTensionSlider = Slider(
            (sliderX, y, -8, 17),
            tickMarkCount=5,
            callback=self._changeTension,
            minValue=50,
            maxValue=100,
            sizeStyle="small",
        )

        if useFloatingWindow:
            y = height - 32
            self.paletteView.group.eqSelectedButton = Button(
                (8, y, -8, 25),
                "Equalize Selected",
                callback=self._eqSelected,
                sizeStyle="small",
            )

    def _changeCurvature(self) -> None:
        raise NotImplementedError

    def _changeCurvatureFree(self) -> None:
        raise NotImplementedError

    def _changeMethod(self) -> None:
        raise NotImplementedError

    def _changeTension(self) -> None:
        raise NotImplementedError

    def _eqSelected(self) -> None:
        raise NotImplementedError

    def _setPreviewOptions(self) -> None:
        if self.method == "balance":
            if self.alwaysPreviewCurves:
                self.previewCurves = True
            else:
                self.previewCurves = False
            self.previewHandles = True
        else:
            self.previewCurves = True
            if self.alwaysPreviewHandles:
                self.previewHandles = True
            else:
                self.previewHandles = False
