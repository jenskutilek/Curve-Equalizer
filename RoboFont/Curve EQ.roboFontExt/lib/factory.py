# helper function for defcon representation factories

def CurveEQRepresentationFactory(glyph, font, method, value):
    glyph = RGlyph(glyph)
    font = glyph.getParent()
    return None

def _registerFactory():
    # From https://github.com/typesupply/glyph-nanny/blob/master/Glyph%20Nanny.roboFontExt/lib/glyphNanny.py
    # always register if debugging
    # otherwise only register if it isn't registered
    from defcon import addRepresentationFactory, removeRepresentationFactory
    from defcon.objects import glyph as _xxxHackGlyph
    if DEBUG:
        if "de.kutilek.curveEQ.factory" in _xxxHackGlyph._representationFactories:
            for font in AllFonts():
                for glyph in font:
                    glyph.naked().destroyAllRepresentations()
            removeRepresentationFactory("de.kutilek.curveEQ.factory")
        addRepresentationFactory("de.kutilek.curveEQ.factory", CurveEQRepresentationFactory)
    else:
        if "de.kutilek.curveEQ.factory" not in _xxxHackGlyph._representationFactories:
            addRepresentationFactory("de.kutilek.curveEQ.factory", CurveEQRepresentationFactory)

def _unregisterFactory():
    from defcon import removeRepresentationFactory
    removeRepresentationFactory("de.kutilek.curveEQ.factory")
