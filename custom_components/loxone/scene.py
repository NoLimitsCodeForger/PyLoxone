"""
Loxone Scenes

For more details about this component, please refer to the documentation at
https://github.com/JoDehli/PyLoxone
"""

import logging

from .service.service_hub import add_service_hub_to_entity
from homeassistant.components.scene import Scene, DOMAIN as ENTITY_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (AddEntitiesCallback,
                                                   async_call_later)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from functools import cached_property
from . import LoxoneEntity

from .const import (CONF_SCENE_GEN, CONF_SCENE_GEN_DELAY, DEFAULT_DELAY_SCENE,
                    DOMAIN, SENDDOMAIN)

_LOGGER = logging.getLogger(__name__)
ENTITY_ID_FORMAT = ENTITY_DOMAIN + ".{}"


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up Scenes."""
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Scenes."""
    delay_scene = config_entry.options.get(CONF_SCENE_GEN_DELAY, DEFAULT_DELAY_SCENE)
    create_scene = config_entry.options.get(CONF_SCENE_GEN, False)

    async def gen_scenes(_):
        scenes = []
        entity_ids = hass.states.async_entity_ids("LIGHT")
        for _ in entity_ids:
            state = hass.states.get(_)
            att = state.attributes
            if "platform" in att and att["platform"] == DOMAIN:
                entity = hass.data["light"].get_entity(state.entity_id)
                if entity.device_class == "LightControllerV2":
                    for effect in entity.effect_list:
                        scene = {}
                        scene = add_service_hub_to_entity(hass, scene)
                        scene.update(
                            {
                                "parent_name": entity.name,
                                "name": effect,
                                "room": entity.device_entry.area_id,
                                "uuidAction": entity.uuidAction,
                                "mood_id": entity.get_id_by_moodname(effect),
                                "_attr_device_info": entity._attr_device_info,
                            }
                        )
                        scenes.append(
                            LoxoneLightScene(**scene)
                        )
        async_add_entities(scenes)

    if create_scene:
        async_call_later(hass, delay_scene, gen_scenes)

    return True


class LoxoneLightScene(LoxoneEntity, Scene):
    ENTITY_ID_FORMAT = ENTITY_ID_FORMAT

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @cached_property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self.uuidAction + "/" + str(self.mood_id)

    def activate(self):
        """Activate scene. Try to get entities into requested state."""
        self.hass.bus.fire(
            SENDDOMAIN,
            dict(uuid=self.uuidAction, value="changeTo/{}".format(self.mood_id)),
        )