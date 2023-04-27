# Home Assistant Eetlijst

This integration uses the API of the new [Eetlijst](https://eetlijst.nl/)  website, so you can check the eating status of you and your roommate from your home assistant instance.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

### Installation

You can add this as a custom repository via HACS:
- On the HACS page of your Home Assistant, in the upper right menu, click custom repositories
- Copy the link to this repository and paste it in the repository field
- Select integration as the category
- Find it on the HACS page and click download

Or copy the contents from `custom_components` directory to your home assistant `custom_components` folder.

### Setup

After restarting your instance, go to integrations and search for Eetlijst. It will first ask for your JWT token. You can get this from your local storage as follows:
<img src="https://github.com/Slalamander/Home-Assistant-Eetlijst/blob/main/images/eetlijst-token.png">

1. On the eetlijst website in your browser, open the inspector (usually, right click --> inspect) and go to the storage tab
2. Open local storage
3. Select the entry with the eetlijst url
4. Select the item with the key `persist:root`
5. In the rightmost tab, go to the `persist:root` object, right click, and select copy

After pasting the contents somewhere like a text file, copy the contents of the `"token":` key (without the opening apostrophes), and paste them in the token field.

Next you can select a few options:
1. Show User Balance: Whether the monetary balance from eetlijst for a person should be shown
2. Custom Entity Pictures: Instead of using an icon for the entities, the today sensor and resident sensors will use the custom images in `www/eetlijst_custom_pictures` in the frontend. (You have to add these manually to your `www` folder in home assistant) These change dynamically depending on a person's state for the day, however I made these for an older version for the old eetlijst website, so they may not be to your liking anymore (though, as shown later, they may also have their uses).
3. Residents name as unit of measurement: Sets the unit of measurement for a resident to their name. Useful when using badges to display the sensors.

<img src="https://github.com/Slalamander/Home-Assistant-Eetlijst/blob/main/images/sensor_options.png">

### Sensors
After setting up, the integration will add a device for the Eetlijst list to your Home Assistant. This device has four types of sensors, which refresh every 5 minutes:
- Info Sensor: shows info about the Eetlijst (For some reason, this one is only handled at the first refresh, so it will appear later).
- Today Sensor: shows a summary of today, who is cooking, who is eating along (and who isn't), and how many are.
- Shopping List Sensor: imports the contents of the shopping list
- Person sensor: Each person on the list gets their own sensor. Its state corresponds to that persons state for today, and in the attributes their status for the upcoming week is shown. If checked, the attributes will also show their balance.

### Usage
The idea of the residents sensor is that they can more or less function with badges. This is where the entity pictures and unit of measurements come in.

Using the custom card [Badge Card](https://github.com/thomasloven/lovelace-badge-card) and [Card Mod]([https://github.com/thomasloven/lovelace-badge-card](https://github.com/thomasloven/lovelace-card-mod)), you can display the sensors like this:
<img src="https://github.com/Slalamander/Home-Assistant-Eetlijst/blob/main/images/eetlijst-badges.png">

```yaml
type: custom:badge-card
badges:
  - entity: sensor.eetlijst_home_assistant_dummy_0
    name: ''
    style: |
      :host {
        --label-badge-background-color: rgba(0, 0, 0, 0.85);
        {% set sens = 'sensor.eetlijst_home_assistant_dummy_0' %}
        {% set eetst = state_attr(sens,'eetstatus_num') %} 
        {% if eetst == None %} 
        --ha-label-badge-label-color: black; --label-badge-red: #f7f5f5;
        {% else %} 
         {% if eetst < 0 %} --label-badge-red: #377330; {% elif eetst > 0 %} --label-badge-red: #bd1313; {% elif eetst == 0 %} --label-badge-red: slategrey; {% endif %}
        {% endif %}
      }
```

### TODO
This is my first custom integration, so if you encounter any issues or bugs, please let me know. It's all still very bare bones, so there's a few things I hope to add in later versions:
- ~~Handle cases for the new option where a person is only doing the groceries (Correct statuses, custom image etc.)~~
- ~~Figure out why the info sensor is not updated upon adding.~~ (For some reason the first entity in the `async_add_entitities` would not have its callback registered)
- ~~Handle changes in lijst users (like when a roommate changes).~~ (Integration is now reloaded when it notices a change in the lijst' users)
- ~~Figure out how to translate the states using localisation files. Somehow these would only work for the config.~~
- Write translations for dutch and english
- Get it added as a default repository
