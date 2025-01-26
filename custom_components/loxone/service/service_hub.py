from .label_sevice import LabelService

class ServiceHub:
    def __init__(self, hass, config_entry):
        """
        Initializes all services as attributes of this class.
        """
        self.label_service = LabelService(hass, config_entry)