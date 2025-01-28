import logging

from homeassistant.helpers.entity import async_generate_entity_id
from ..const import CONF_ENTITY_NAME_PATTERN, CONF_ENTITY_ID_PATTERN, DEFAULT_ENTITY_NAME_PATTERN, DEFAULT_ENTITY_ID_PATTERN

_LOGGER = logging.getLogger(__name__)

class EntityNamingStrategyService:
    """
    Class for applying naming conventions based on patterns
    loaded from Home Assistant configuration.
    """

    def __init__(self, hass, config_entry):
        """
        Initialize the service with configuration patterns.

        :param config_entry: The configuration entry containing patterns.
        """
        self.entity_name_pattern = config_entry.options.get(CONF_ENTITY_NAME_PATTERN, DEFAULT_ENTITY_NAME_PATTERN)
        self.entity_id_pattern = config_entry.options.get(CONF_ENTITY_ID_PATTERN, DEFAULT_ENTITY_ID_PATTERN)
        self.hass = hass

        _LOGGER.debug(f"entity_name_pattern: {self.entity_name_pattern}")
        _LOGGER.debug(f"entity_id_pattern: {self.entity_id_pattern}")

    def get_entity_name(self, entity_data) -> str:
        """
        Generate the entity name based on the provided pattern and entity data.

        :param entity_data: An object (e.g., an entity) with attributes 'room', 'category', and 'name'.
        :return: The formatted entity name.
        """
        return self._apply_pattern(self.entity_name_pattern, entity_data)

    def get_entity_id(self, entity_data, entity_id_format) -> str:
        """
        Generate the entity ID based on the provided pattern and entity data.

        :param entity_data: An object (e.g., an entity) with attributes 'room', 'category', and 'name'.
        :return: The formatted entity ID.
        """
        # Generation of entity_id with specific pattern with placeholders from configuration
        entity_id = self._apply_pattern(self.entity_id_pattern, entity_data)

        # We use standard HA generation with entity id format (has platform, e.g. sensor.entity_name)
        # TODO check internal placeholders in HA
        return async_generate_entity_id(
                 entity_id_format, entity_id, hass=self.hass)


    @staticmethod
    def _apply_pattern(pattern, entity_data):
        """
        Replace placeholders in the pattern with actual values from entity data.

        :param pattern: The pattern string with placeholders (e.g., <room>, <category>, <name>).
        :param entity_data: An object (e.g., an entity) or a dictionary containing 'room', 'category', and 'name'.
        :return: The formatted string with placeholders replaced.
        """
        mapping = {
            "room": "room",
            "category": "cat",
            "name": "name"
        }

        result = pattern
        for placeholder, key in mapping.items():
            placeholder_tag = f"<{placeholder}>"
            if placeholder_tag in result:
                # Support both dictionary and object-like entity_data
                if isinstance(entity_data, dict):
                    value = entity_data.get(key, "")
                else:
                    value = getattr(entity_data, key, "")
                result = result.replace(placeholder_tag, value)
        return result