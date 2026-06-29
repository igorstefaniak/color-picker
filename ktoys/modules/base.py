from PySide6.QtWidgets import QWidget

class BaseModule:
    def __init__(self):
        self.window = None

    def get_id(self) -> str:
        raise NotImplementedError

    def get_name(self) -> str:
        raise NotImplementedError

    def get_icon(self) -> str:
        raise NotImplementedError

    def get_description(self) -> str:
        return ""

    def launch(self, parent=None, trigger_action=None) -> QWidget:
        """Launch the module window and return it."""
        raise NotImplementedError

    def has_settings(self) -> bool:
        """Return True if this module has a settings dialog."""
        return False

    def show_settings(self, parent=None):
        """Open the settings dialog for this module."""
        pass
