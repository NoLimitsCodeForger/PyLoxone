from ..const import DOMAIN, SERVICE_HUB
from .entity_naming_strategy_service import EntityNamingStrategyService
from .label_sevice import LabelService

class ServiceHub:
    def __init__(self, hass, config_entry):
        """
        Initializes all services as attributes of this class.
        """
        self.label_service = LabelService(hass, config_entry)
        self.entity_naming_strategy_service = EntityNamingStrategyService(hass, config_entry)

def add_service_hub_to_entity(hass, entity: dict):
    """
    Add the Service Hub reference to the given entity.

    This function updates the provided entity dictionary by adding a reference
    to the Service Hub from the Home Assistant instance (`hass`). The Service
    Hub is retrieved from the global `hass.data` dictionary using the domain
    constant.

    :param hass: Home Assistant instance containing the application's runtime data.
    :param entity: A dictionary representing the entity to which the Service Hub reference will be added.
    :return: The updated entity dictionary with the Service Hub reference added.
    """
    entity.update(
        {
            SERVICE_HUB: hass.data[DOMAIN][SERVICE_HUB]
        }
    )

    return entity
