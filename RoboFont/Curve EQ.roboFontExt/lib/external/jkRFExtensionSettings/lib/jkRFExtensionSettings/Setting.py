class Setting(object):
    def __init__(self, key, default_value, name=None):
        self._key = key
        self._default_value = default_value
        self._name = name
        self._ui_object = None

    def _get_key(self):
        return self._key

    def _set_key(self, value):
        self._key = value

    key = property(_get_key, _set_key)

    def _get_value(self):
        if self._ui_object is None:
            return self._value
        else:
            return self._ui_object.get()

    def _set_value(self, value):
        self._value = value

    value = property(_get_value, _set_value)

    def _get_default_value(self):
        return self._default_value

    def _set_default_value(self, value):
        self._default_value = value

    default_value = property(_get_default_value, _set_default_value)

    def _get_name(self):
        if self._name is None:
            return self._key
        return self._name

    def _set_name(self, value):
        self._name = value

    name = property(_get_name, _set_name)

    def _get_ui_object(self):
        return self._ui_object

    def _set_ui_object(self, value):
        self._ui_object = value

    ui_object = property(_get_ui_object, _set_ui_object)

    def is_default(self):
        if self._value == self._default_value:
            return True
        return False
