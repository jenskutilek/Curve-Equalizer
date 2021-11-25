from vanilla import Button, FloatingWindow, Group, RadioGroup, Slider, Window


class BaseCurveEqualizer:
    def build_ui(self, useFloatingWindow=True):
        self.methods = {
            0: "balance",
            1: "free",
            2: "hobby",
        }

        self.methodNames = [
            "Balance",
            "Adjust:",
            "Hobby:",
        ]

        height = 108
        width = 200
        sliderX = 76

        if useFloatingWindow:
            self.w = FloatingWindow(
                posSize=(width, height),
                title="Curve EQ",
                minSize=(width, height + 16),
                maxSize=(1000, height + 16),
            )
        else:
            self.w = Window((width, height))

        self.w.group = Group((0, 0, width, height))

        y = 8
        self.w.group.eqMethodSelector = RadioGroup(
            (8, y, -8, -36),
            titles=self.methodNames,
            callback=self._changeMethod,
            sizeStyle="small",
        )

        y += 22
        self.w.group.eqCurvatureSlider = Slider(
            (sliderX, y, -8, 17),
            callback=self._changeCurvatureFree,
            minValue=0.5,
            maxValue=1.0,
            value=0.75,  # Will be replaced by saved value
            sizeStyle="small",
        )

        y += 25
        self.w.group.eqHobbyTensionSlider = Slider(
            (sliderX, y, -8, 17),
            tickMarkCount=5,
            callback=self._changeTension,
            minValue=0.5,
            maxValue=1.0,
            sizeStyle="small",
        )

        y = height - 32
        self.w.group.eqSelectedButton = Button(
            (8, y, -8, 25),
            "Equalize Selected",
            callback=self._eqSelected,
            sizeStyle="small",
        )
