import logging
import hashlib
from homeassistant.helpers import entity_registry as er, label_registry as lr
from ..helpers import get_cat_name_from_cat_uuid
from ..miniserver import get_miniserver_from_hass
from ..const import CONF_LABEL_GEN

_LOGGER = logging.getLogger(__name__)

def generate_color(cat: str) -> str:
    """
    Generate a hex color based on the category.

    Args:
        cat: The category string.

    Returns:
        A hex color code as a string.
    """
    hash_value = hashlib.md5(cat.encode()).hexdigest()
    return f"#{hash_value[:6]}"  # First 6 characters of the hash value as hex color


class LabelService:
    def __init__(self, hass, config_entry) -> None:
        """
        Initialize the LabelService.

        Args:
            hass: Home Assistant instance.
            config_entry: Configuration entry.
        """
        self.hass = hass

        # Load entity and label registries
        self.entity_registry = er.async_get(hass)
        self.label_registry = lr.async_get(hass)

        # Load all existing labels
        self.existing_labels = {label.name: label for label in self.label_registry.async_list_labels()}

        _LOGGER.info(f"labels: '{self.existing_labels}'")
        self.gen_label = config_entry.options.get(CONF_LABEL_GEN, True)

    async def assign_label(self, entity_id, label_name):
        """
        Assign a label to an entity.

        Args:
            entity_id: The ID of the entity.
            label_name: The name of the label.
        """
        if self.gen_label and label_name:
            # Check if the label already exists
            label = self.existing_labels.get(label_name)
            if not label:
                # Create a new label if it does not exist
                _LOGGER.debug(f"Creating label '{label_name}'")
                label = self.label_registry.async_create(
                    name=label_name,
                    color=generate_color(label_name)  # Color based on the 'cat'
                )
                # Add the new label to the existing labels list
                self.existing_labels[label_name] = label

            # Get the current labels of the entity
            current_labels = set()
            entity = self.entity_registry.entities.get(entity_id)
            if entity and entity.labels:
                current_labels = set(entity.labels)

            # Add the new label to the current labels
            current_labels.add(label.label_id)

            _LOGGER.debug(f"entity_id: {entity_id}, labels: '{current_labels}'")

            # Update the registry
            self.entity_registry.async_update_entity(entity_id, labels=list(current_labels))

            # Update attributes in the states
            state = self.hass.states.get(entity_id)
            if state:
                self.hass.states.async_set(
                    entity_id, state.state, {**state.attributes, "labels": list(current_labels)}
                )

    def find_loxone_cat(self, unique_id, controls):
        """
        Find the corresponding control or sub-control and return the appropriate 'cat'.

        Args:
            unique_id: Unique ID of the entity in Home Assistant.
            controls: Dictionary of all controls from Loxone.

        Returns:
            The 'cat' value if it exists, otherwise None.
        """
        for control_id, control in controls.items():
            # Check the main control
            if unique_id == control.get("uuidAction"):
                return control.get("cat")

            # Check sub-controls
            sub_controls = control.get("subControls", {})
            if unique_id in sub_controls:
                # Use 'cat' from the parent control
                return control.get("cat")
        return None

    async def update_labels_from_loxone_cat(self):
        """
        Map all Home Assistant entities to their Loxone 'cat' attribute.
        """
        # Get Loxone configuration
        miniserver = get_miniserver_from_hass(self.hass)
        loxconfig = miniserver.lox_config.json
        controls = loxconfig.get("controls", {})

        # Iterate over all entities in the registry
        for entity in self.entity_registry.entities.values():
            # Get the unique_id of the entity
            if not entity.unique_id:
                # Skip entities without a unique_id
                _LOGGER.warning(f"Entity {entity.entity_id} does not have a unique_id, skipped.")
                continue

            # Find the corresponding device in Loxone configuration by uuid
            cat = self.find_loxone_cat(entity.unique_id, controls)
            cat = new_cat if (new_cat := get_cat_name_from_cat_uuid(loxconfig, cat)) else cat
            if not cat:
                continue  # Skip if the device does not have a 'cat'

            await self.assign_label(entity.entity_id, cat)