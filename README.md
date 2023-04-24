# Home Assistant Eetlijst

This integration uses the API of the new [Eetlijst](https://eetlijst.nl/)  website, so you can check the eating status of you and your roommate from your home assistant instance.

### Installation

You can add this as a custom repository via HACS:
- On the HACS page of your Home Assistant, in the upper right menu, click custom repositories
- Copy the link to this repository and paste it in the repository field
- Select integration as the category

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
2. Custom Entity Pictures: Instead of using an icon for the entities, the today sensor and resident sensors will use the custom images in `www/eetlijst_custom_pictures` in the frontend. These change dynamically depending on a person's state for the day, however I made these for an older version for the old eetlijst website, so they may not be to your liking anymore (though, as shown later, they may also have their uses).
3. Residents name as unit of measurement: Sets the unit of measurement for a resident to their name. Useful when using badges to display the sensors.

### Sensors
After setting up, the integration will add a device for the Eetlijst list to your Home Assistant. This device has four types of sensors:
- Info Sensor: shows info about the Eetlijst
- Today Sensor: shows a summary of today, who is cooking, who is eating along (and who isn't), and how many are.
- Shopping List Sensor: imports the contents of the shopping list
- Person sensor: Each person on the list gets their own sensor. Its state corresponds to that persons state for today, and in the attributes their status for the upcoming week is shown. If checked, the attributes will also show their balance.



