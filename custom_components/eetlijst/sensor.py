"""Platform for sensor integration."""
# This file shows the setup for the sensors associated with the cover.
# They are setup in the same way with the call to the async_setup_entry function
# via HA from the module __init__. Each sensor has a device_class, this tells HA how
# to display it in the UI (for know types). The unit_of_measurement property tells HA
# what the unit is, so it can display the correct range. For predefined types (such as
# battery), the unit_of_measurement should match what's expected.

from homeassistant.helpers.entity import Entity
from homeassistant.core import callback
from .const import DOMAIN
from homeassistant.helpers.update_coordinator import CoordinatorEntity

ICON_FOLDER = "/local/eetlijst_custom_pictures/"
ICON_BASE = ICON_FOLDER + "eetlijst_{}.svg"

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    lijst = hass.data[DOMAIN][config_entry.entry_id]
    await lijst.setuplijst()
    await lijst.async_config_entry_first_refresh()
    new_devices = []
    infosensor = EetlijstInfo(lijst)
    new_devices.append(infosensor)
    new_devices.append(EetlijstVandaag(lijst))
    new_devices.append(ShoppingList(lijst))
    for idx, person_id in enumerate(lijst._residents_ordered):
        residentSensor = EetlijstResident(eetlijst=lijst, person_id=person_id, sensor_idx=idx)
        new_devices.append(residentSensor)

    if new_devices:
        async_add_entities(new_devices, update_before_add=True)

class SensorBase(CoordinatorEntity, Entity):
    """Base representation of a Hello World Sensor."""

    should_poll = False

    def __init__(self, lijst):
        """Initialize the sensor."""
        super().__init__(lijst)
        self._eetlijst = lijst
        self.idx = 0

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._eetlijst._id)},
            # If desired, the name for the device could be different to the entity
            "name": self._eetlijst._name,
            "model": self._eetlijst.model,
            "manufacturer": self._eetlijst.manufacturer,
        }

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    # async def async_added_to_hass(self):
    #     """Run when this Entity has been added to HA."""
    #     # Sensors should also register callbacks to HA when their state changes
    #     self._eetlijst.register_callback(self.async_write_ha_state)

    # async def async_will_remove_from_hass(self):
    #     """Entity being removed from hass."""
    #     # The opposite of async_added_to_hass. Remove any registered call backs here.
    #     self._eetlijst.remove_callback(self.async_write_ha_state)


class EetlijstInfo(SensorBase):
    """Sensor with information about the Eetlijst."""

    def __init__(self, eetlijst) -> None:
        """Initialize the sensor."""
        super().__init__(eetlijst)
        self._attr_unique_id = f"{self._eetlijst._id}_info"

        self._attr_name = f"Eetlijst {self._eetlijst.lijst_name} Info"
        self._attr_icon = "mdi:home-analytics"
        self._attr_state = None
        self._attr_extra_state_attributes = None

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        #This is not called when setting up; idk why
        attr_dict = {}
        attr_keys = ["city", "adress", "name"]
        info = self._eetlijst.lijst_info
        for key in attr_keys:
            if key in info:
                attr_dict[key] = info[key]

        residents = []
        for user in info["users_in_groups"]:
            person = user["user"]["name"]
            residents.append(person)
        attr_dict["residents"] = residents
        self._attr_extra_state_attributes = attr_dict
        self._attr_state = self._eetlijst.lijst_info["active"]
        self.async_write_ha_state()

    @property
    def name(self) -> str | None:
        return self._attr_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def unit_of_measurement(self) -> str | None:
        return "Active"

    @property
    def icon(self) -> str | None:
        return self._attr_icon

class EetlijstVandaag(SensorBase):
    """Sensor with information about today."""
    def __init__(self, eetlijst):
        """Initialize the sensor."""
        super().__init__(eetlijst)

        self._attr_unique_id = f"{self._eetlijst._id}_today"
        self._attr_name = f"Eetlijst {self._eetlijst.lijst_name} Today"

        self._state = None
        self._extra_state_attributes = self.build_attr_dict()
        self._suggested_unit_of_measurement = "Cook"

    @property
    def icon(self) -> str | None:
        return "mdi:chef-hat"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    @property
    def suggested_unit_of_measurement(self):
        return self._suggested_unit_of_measurement

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        today = self.coordinator.data["today"]["eetschema_event"][0]
        attr_dict = {"total eaters": 0, "Eating": [], "Not Eating": [], "Unknown": []}
        check_dict = ["Eating", "Not Eating", "Unknown"]
        cook = "Nobody"
        for person_state in today["event_attendees_all_users"]:
            person = person_state["user"]["name"]
            person_eaters = 0
            person_text = person

            if isinstance(person_state["number_guests"], int):
                if person_state["number_guests"] > 0:
                    person_eaters = person_state["number_guests"]
                    person_text = f"{person} + {person_eaters}"

            if person_state["status"] == "cook":
                if cook == "Nobody":
                    cook = person
                else:
                    cook = "Multiple People"
                attr_dict["Eating"].append(person_text)
                attr_dict["total eaters"] += 1 + person_eaters
            elif person_state["status"] == "eat_only":
                attr_dict["Eating"].append(person_text)
                attr_dict["total eaters"] += 1 + person_eaters
            elif person_state["status"] == "not_attending":
                attr_dict["Not Eating"].append(person)
            else:
                attr_dict["Unknown"].append(person)

        if today["description"] is not None:
            attr_dict["Food"] = today["description"]

        attr_dict["Open"] = today["open"]

        for key in check_dict:
            if not attr_dict[key]:
                attr_dict[key] = "Nobody"

        # print(attr_dict)
        self._extra_state_attributes = attr_dict
        self._state = cook
        if self._eetlijst._config_options["custom_pictures"]:
            if cook == "Multiple People":
                self._attr_entity_picture = ICON_BASE.format("_kok_plus")
            elif cook == "Nobody":
                self._attr_entity_picture = ICON_BASE.format("kok_off")
            else:
                self._attr_entity_picture = ICON_BASE.format("kok_on")
        else:
            self._attr_entity_picture = None
        self.async_write_ha_state()

    def build_attr_dict(self):
        today = self.coordinator.data["today"]["eetschema_event"][0]
        attr_dict = {"cook": "Nobody", "eaters": []}
        for person_state in today["event_attendees_all_users"]:
            person = person_state["user"]["name"]
            if person_state["status"] == "cook":
                attr_dict["cook"] = person
                attr_dict["eaters"].append(person)
            if person_state["status"] == "eat_only":
                attr_dict["eaters"].append(person)

        return attr_dict


class ShoppingList(SensorBase):
    """Eetlijst Shopping List Sensor."""

    def __init__(self, eetlijst):
        """Initialize the sensor."""
        # In this sensor: handle extra people getting in/sensors changing?
        super().__init__(eetlijst)
        self._attr_unique_id = f"{self._eetlijst._id}_shopping_list"

        # The name of the entity
        self._attr_name = f"Eetlijst {self._eetlijst.lijst_name} Shopping List"
        self._attr_state = len(self.coordinator.data["list"]["eetschema_list"])
        self._attr_icon = "mdi:cart"
        shoplist = []
        for item in self.coordinator.data["list"]["eetschema_list"]:
            shoplist.append(item["text"])
        self._attr_extra_state_attributes = {"Items": shoplist}

    @property
    def state(self):
        return self._attr_state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def unit_of_measurement(self) -> str | None:
        return "Items on List"

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_state = len(self.coordinator.data["list"]["eetschema_list"])
        shoplist = []
        for item in self.coordinator.data["list"]["eetschema_list"]:
            shoplist.append(item["text"])
        self._attr_extra_state_attributes = {"Items": shoplist}
        self.async_write_ha_state()


class EetlijstResident(SensorBase):
    """Eetlijst Resident Sensor."""

    def __init__(self, eetlijst, person_id, sensor_idx):
        super().__init__(eetlijst)

        # unique id: use order?
        # As per the sensor, this must be a unique value within this domain. This is done
        # by using the device ID, and appending "_battery"
        self._attr_unique_id = f"{self._eetlijst._id}_{sensor_idx}"
        #self._person_order = person_order
        self._attr_name = f"Eetlijst {self._eetlijst.lijst_name} {sensor_idx}"
        self._person_name = self._eetlijst._residents_ordered[person_id]
        self._person_id = person_id #self._eetlijst._residents_ordered[person_order]["id"]
        self._attr_unit_of_measurement = self._person_name
        self._attr_device_class = "eetlijst_user"
        self._attr_translation_key = "eetlijst_user"
        self._attr_extra_state_attributes = None
        self._attr_state = None
        self._attr_icon = "mdi:silverware-variant"
        self._attr_entity_picture = ICON_FOLDER + "eetlijst_logo.svg"

    @property
    def icon(self) -> str | None:
        return self._attr_icon

    @property
    def translation_key(self) -> str | None:
        return self._attr_translation_key

    @property
    def unit_of_measurement(self) -> str | None:
        if self._eetlijst._config_options["resident_units"]:
            return self._attr_unit_of_measurement
        else:
            return None

    @property
    def state(self):
        return self._attr_state

    @property
    def state_attributes(self):
        return self._attr_extra_state_attributes

    @property
    def entity_picture(self) -> str | None:
        return self._attr_entity_picture

    @property
    def device_class(self) -> str | None:
        return self._attr_device_class

    @callback
    def _handle_coordinator_update(self) -> None:
        person_future = self.coordinator.data["future"][self._person_id]
        self._attr_unit_of_measurement = self._person_name
        attr_dict = {}
        #print(f"Updating Person {self._person_name}")
        if self._eetlijst._config_options["show_balance"]:
            for entry in self.coordinator.data["info"]["eetschema_group"][0]["summary"]:
                if entry["user_id"] == self._person_id:
                    balance = entry["payed_total"] / 100
                    #self._attr_extra_state_attributes["Balance"] = f"€{balance:.2f}"
                    attr_dict["Balance"] = f"€{balance:.2f}"

        attr_dict["eetstatus_num"] = None
        for day in person_future["next_week"]:
            #if day == "Today": continue

            day_state = person_future["next_week"][day]
            day_text = None if day_state["status"] == "dont_know_yet" else day_state["status"]

            if day_state["status"] == "cook" or day_state["status"] == "eat_only":
                if day == "Today":
                    attr_dict["eetstatus_num"] = 1 if day_state["status"] == "cook" else -1

                if isinstance(day_state["number_guests"], int):
                    if day_state["number_guests"] > 0:
                        day_eaters = day_state["number_guests"]
                        if day == "Today":
                            attr_dict["eetstatus_num"] = 1 + day_eaters if day_state["status"] == "cook" else -1 - day_eaters
                            self._attr_unit_of_measurement = f'{self._person_name} + {day_state["number_guests"]}'
                        else:
                            day_text = f"{day_text} + {day_eaters}"

            if day == "Today":
                self._attr_state = day_text
                if day_state["status"] == "not_attending":
                    attr_dict["eetstatus_num"] = 0
                elif day_state["status"] is None or day_state["status"] is "dont_know_yet":
                    attr_dict["eetstatus_num"] = None
            else:
                attr_dict[day] = day_text

        if attr_dict["eetstatus_num"] == None:
            self._attr_entity_picture = ICON_BASE.format("none")
        else:
            if attr_dict["eetstatus_num"] > 4:
                eetnum = 5
            elif attr_dict["eetstatus_num"] < -4:
                eetnum = -5
            else:
                eetnum = attr_dict["eetstatus_num"]
            self._attr_entity_picture = ICON_BASE.format(eetnum)

        if not self._eetlijst._config_options["custom_pictures"]:
            self._attr_entity_picture = None

        self._attr_extra_state_attributes = attr_dict
        self._attr_name = f"Eetstatus {self._person_name}"
        self.async_write_ha_state()
        # Use an attr eetstatus_num as an integer value for the badge cards
