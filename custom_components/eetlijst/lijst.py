"""A Eetlijst API Coordinator."""
from __future__ import annotations

# In a real implementation, this would be in an external library that's on PyPI.
# The PyPI package needs to be included in the `requirements` section of manifest.json
# See https://developers.home-assistant.io/docs/creating_integration_manifest
# for more information.
# This dummy hub always returns 3 rollers.
import aiohttp
from datetime import datetime, timedelta
import logging
from homeassistant.core import HomeAssistant
from .const import DOMAIN, REFRESH
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

APIURL = "https://api.samenn.nl/v1/graphql"
SCAN_INTERVAL = timedelta(seconds=REFRESH)

LOGGER: logging.Logger = logging.getLogger(__package__)
_LOGGER = logging.getLogger(__name__)


async def options_update_listener(hass: HomeAssistant, entry):
    _LOGGER.debug("Updating Eetlijst Entry")
    new_options = entry.options
    lijst = hass.data[DOMAIN][entry.entry_id]
    current_conf = {}
    for option in lijst._config_options:
        current_conf[option] = lijst._config_options[option]

    for option in entry.options:
        current_conf[option] = new_options[option]

    setattr(lijst, "_config_options", current_conf)
    setattr(entry, "data", current_conf)
    lijst.async_update_listeners()


async def test_token(token) -> bool:
    """Test connectivity to the API is OK."""
    _LOGGER.debug("Testing Eetlijst connection")
    Headers = {}
    Headers["content-type"] = "application/json"
    Headers["Authorization"] = f"Bearer {token}"
    body = """
        query MyQuery {
        eetschema_group {
            city
            address
            active
            default_status
            name
        }
        }
        """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=APIURL, headers=Headers, json={"query": body}
        ) as resp:
            respjson = await resp.json()
            if resp.status == 200:
                if "errors" in respjson:
                    _LOGGER.error(f"Got an error in connecting to the API {respjson}")
                    return (False, respjson)
                else:
                    try:
                        eetlijst_info = respjson["data"]["eetschema_group"][0]
                        lijst_name = eetlijst_info["name"]
                        return (True, lijst_name)
                    except Exception as exce:
                        respjson["errors"] = exce
                        return (False, respjson)
            else:
                return (False, None)


class LijstCoordinator(DataUpdateCoordinator):
    """Dummy Home for Eetlijst testing."""

    manufacturer = "Eetlijst"

    def __init__(
        self, hass: HomeAssistant, config_entry: str, config_data: None
    ) -> None:
        """Init dummy hub."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Eetlijst",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=SCAN_INTERVAL,
        )
        self._token = config_data["token"]  # token
        self._name = False
        self._hass = hass
        self._id = config_data["lijst_dev_id"]
        self.entry_id = config_entry.entry_id
        self._callbacks = set()
        # self.firmware_version = f"0.0.{random.randint(1, 9)}"
        self.model = "Eetlijst"
        self.is_setup = False
        self.last_idx = 0
        self._config_options = config_data
        Headers = {}
        Headers["content-type"] = "application/json"
        Headers["Authorization"] = f"Bearer {self._token}"
        self.api_headers = Headers

    async def _async_update_data(self) -> None:
        queries = {}
        data = {}
        queries["info"] = self.query_body_info()
        queries["today"] = self.query_body_today()
        queries["list"] = self.query_body_list()
        queries["future"] = self.query_body_future()

        async with aiohttp.ClientSession() as session:
            for query_type in queries:
                body = queries[query_type]
                async with session.post(
                    url=APIURL, headers=self.api_headers, json={"query": body}
                ) as resp:
                    respjson = await resp.json()
                    if resp.status != 200:
                        _LOGGER.error("Error Connecting to the Eetlijst API")
                        break
                    data[query_type] = respjson["data"]
        data["future"] = self.format_future_dict(data["future"])
        return data

    async def setuplijst(self) -> None:
        body = """
            query MyQuery {
            eetschema_group {
                city
                address
                active
                default_status
                name
                users_in_groups(where: {active: {_eq: true}}) {
                order
                user {
                    name
                    id
                }
                }
            }
            }
        """

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=APIURL, headers=self.api_headers, json={"query": body}
            ) as resp:
                respjson = await resp.json()

                if not "data" in respjson:
                    _LOGGER.error(f"No data key in eetlijst response: {respjson}")

                _LOGGER.warning(f"Eetlijst got response {respjson}")
                eetlijst_info = respjson["data"]["eetschema_group"][0]
                self.lijst_name = eetlijst_info["name"]
                self._name = "Eetlijst {}".format(eetlijst_info["name"])
                self.lijst_info = eetlijst_info
                residents = []
                residents_order = {}
                for user in eetlijst_info["users_in_groups"]:
                    person = user["user"]["name"]
                    residents.append(person)
                    # person_num = user["order"]
                    # if person_num in residents_order:
                    #     while person_num in residents_order:
                    #         person_num += 1
                    # residents_order[person_num] = {
                    #     "name": person,
                    #     "id": user["user"]["id"],
                    # }
                    residents_order[user["user"]["id"]] = person

                self.residents = residents
                self._residents_ordered = residents_order
                self.model = self.lijst_name

    async def test_connection(self) -> bool:
        """Test connectivity to the Dummy hub is OK."""
        body = """
            query MyQuery {
            eetschema_group {
                city
                address
                active
                default_status
                name
            }
            }
            """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=APIURL, headers=self.api_headers, json={"query": body}
            ) as resp:
                respjson = await resp.json()
                if resp.status == 200:
                    if "errors" in respjson:
                        print("Got an error in connecting to the API")
                        return False
                    else:
                        lijstinfo = respjson["data"]["eetschema_group"][0]
                        self._name = "Eetlijst {}".format(lijstinfo["name"])
                        # self.name = self._name
                        self._id = "{}_{}".format(
                            self._token.lower(), lijstinfo["name"]
                        )
                        for callback in self._callbacks:
                            callback()
                        return True

    def query_body_info(self) -> str:
        return """
                query MyQuery {
                    eetschema_group {
                        city
                        address
                        active
                        default_status
                        name
                        summary(order_by: {}) {
                            payed_total
                            user_id
                            }
                        users_in_groups(where: {active: {_eq: true}}) {
                        order
                        user {
                            name
                            id
                        }
                        }
                    }
                    }
                """

    def query_body_today(self) -> str:
        today_str = datetime.today().date().strftime("%Y-%m-%d")
        today_filt = f"{today_str}T00:00:00+00:00"

        body = (
            """
        query MyQuery {
        eetschema_event(where: {start_date: {_eq: \"%s\"}}) {
            start_date
            end_date
            name
            type
            open
            description
            event_attendees_all_users(where: {active: {_eq: true}}, order_by: {order: asc}) {
            status
            order
            number_guests
            user {
                name
                id
            }
            }
        }
        }
        """
            % today_filt
        )
        return body

    def query_body_future(self):
        today_str = datetime.today().date().strftime("%Y-%m-%d")
        today_filt = f"{today_str}T00:00:00+00:00"
        body = (
            """
            query MyQuery($_gt: timestamptz = "") {
            eetschema_event(
                order_by: {start_date: asc}
                where: {start_date: {_gte:  \"%s\"}}
                limit: 7
            ) {
                start_date
                event_attendees_all_users(where: {active: {_eq: true}}, order_by: {order: asc}) {
                user {
                    name
                    id
                }
                status
                order
                number_guests
                }
            }
            }
            """
            % today_filt
        )
        return body

    def format_future_dict(self, response):
        persons_dict = {}
        for idx, eet_event in enumerate(response["eetschema_event"]):
            date = eet_event["start_date"]
            dtobj = datetime.fromisoformat(date)
            daystr = datetime.strftime(dtobj, "%A")
            if idx == 0:
                daystr = "Today"

            for person in eet_event["event_attendees_all_users"]:
                if not person["user"]["id"] in persons_dict:
                    persons_dict[person["user"]["id"]] = person["user"]
                    persons_dict[person["user"]["id"]]["next_week"] = {}
                persons_dict[person["user"]["id"]]["next_week"][daystr] = {
                    "status": person["status"],
                    "number_guests": person["number_guests"],
                }
        return persons_dict

    def query_body_list(self) -> str:
        return """
            query MyQuery {
            eetschema_list(where: {checked: {_eq: false}, active: {_eq: true}}) {
                text
                checked
            }
            }
            """
