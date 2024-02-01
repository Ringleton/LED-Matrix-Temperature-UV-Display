# ﻿Temperature and UV Index RGB Matrix Display

# Overview
This display utilizes a WIFI connection to read data from a weather server.  The display uses data produced by a Davis Instruments weather server and gets its data populated by its branded weather stations ([www.davisinstruments.com](http://www.davisinstruments.com)).  The source of the data used for this matrix display is produced by a Davis weather station set up in the Cadence neighborhood.  That station transmits data wirelessly to either a legacy data logger and/or a newer display console.  Those two systems separately upload their data to the Davis server, and it is that data that is then retrieved by the matrix display unit every 60 seconds, displaying the current temperature and UV Index.  The Davis server also maintains a web page for each station that shows the weather statistics for each.

![001](https://github.com/Ringleton/LED-Matrix-Temperature-UV-Display/assets/157074435/257de8e7-dc1d-4d5d-825c-b658bd5483d0)

This LED matrix display is built using a Raspberry Pi Zero 2 WH, single board computer along with an Adafruit RGB matrix “bonnet” plugged into the top of the Pi.  The bonnet converts the Pi’s 3.3V output pins to 5.0V logic along with a socket to connect a cable to the input of one of the two 64 X 32 RGB LED matrix, 3mm pitch (P3) panels.

The Pi’s external connectors are exposed at the rear inset of the enclosure, along with a separate power supply connection (5V, 10A) and a pushbutton that acts as either a reboot or shutdown trigger.  You can connect a video display to the Pi’s mini-HDMI connector and a mouse / keyboard dongle to the Pi’s micro-USB On-The-Go (OTG) port to interact and control the system.  Optionally, you can also use a terminal emulator connected over WIFI.  The Pi uses a Unix-based operating system.  The program itself is written in Python.

To capture the data from the weather station, either a Davis data logger and/or station console is used.  The Davis WeatherLinkIP device is a legacy data collection device that is now obsolete.  It is one of the earlier devices that Davis employed to upload data from a weather station to their server.  As of this writing, the 6313 Console is Davis’ latest product.  This unit is an Android-based tablet display and uploads data to their server.  If both devices are employed concurrently, even though they are receiving the data being transmitted from the same physical weather station, when uploaded, the Davis server treats these as two entirely separate weather stations.  Both produce an almost identical web page summary.  You will find both a “Cadence at the Lakes” (6313 Console) and a “Cadence at The Lakes 2” (WeatherLinkIP) weather station on the Davis map with “2” being the legacy unit’s data.

While both devices upload data every 60 seconds and the corresponding web page summaries are updated immediately, the data can only be read back every 60 seconds without a paid subscription with the legacy device station.  The data from the newer console requires a paid subscription to read the data every 5 minutes or 1 minute.  Otherwise, the free subscription only provides updated data every 15 minutes.  For this reason, while the legacy device continues to work, this display is currently configured to grab that station’s data.  Until it is changed, the webpage data for station “2” and this display should be in almost perfect synchronization.

The program is designed to be able to pull data from either station so should the legacy device eventually fail or no longer be supported on their server, you can reconfigure the display to use the data uploaded from the newer console.  But note that, unless you subscribe (pay) for one of the upgraded plans, the display will show the same information for 15 minutes before it is updated (the temperature may suddenly jump several points) and the data will not be in perfect synchronization with the web page summary of this same station.
# Shutting Down or Restarting
On the rear inset panel just below the power jack, there is a pushbutton.  Momentarily press once to restart the display (takes about 60 seconds) or press and hold for at least two seconds to safely shut down the unit (takes about 20 seconds).  Whenever possible, always use the pushbutton to shut down the unit safely before disconnecting the power.  Note that when first applying power, it will take about 40 seconds before something appears on the display.
# Removing the Display from a Wall
Taking advantage of a wall with alternating vertical panel widths, extending from the rear inset area of the enclosure near the top are two levers that act as locks to prevent easy removal of the display from a wall.  To remove the display, reach from above and slide both levers fully to one side.  Note that one lever should already be pushed fully to one side so just push the other over to the same side.  You should then be able to slightly push the opposite side of the panel up and then pull away from the wall just enough until you can slide both levers fully back towards that side.  Then you should be able to pull the other side of the display slightly up and pull away from the wall and the entire display should then release.

To re-install on the wall, reverse the steps above and once completed, separate and push the one lever away from the other towards its corresponding side of the display.  If locked correctly, you should not be able to push the display upwards to then pull off the wall.

Without the locks installed, just push the entire display slightly up and then pull away from the wall.
# Username and Passwords
The username for this Pi is “cadence” and the password is “atthelakes”.  This will provide you with access to this Pi and the ability to change the WIFI network and the weather station credentials.  If the Pi username or password is ever changed, you will need to record this new information somewhere that an administrator has access to.  If the username and password above do not work, then someone may have already made that change – check with the administrator for the updated information.

The Davis Instruments account information will also need to be known by this display if the account changes or a different station is to be monitored.  The Davis Device ID or API key and secret can all be found under the Davis account.  The Davis account information will also be required to make changes to the WIFI connection of the 6313 Console.

Optionally, a free Adafruit IoT account can be used to monitor display statistics.  This Adafruit feed can be configured to provide an email notification after a configured period of inactivity.  This can alert the administrator that the display has failed or lost its internet connection.  See Adafruit IoT Monitoring below for more information.
# Connecting to the Pi
##
## With WIFI
If the Pi is connected to a WIFI network and you know it’s IP address, use the VNC Viewer application (a terminal emulator) on either a tablet or computer connected to the same WIFI network and enter the Pi’s IP address when prompted.  If you do not know the Pi’s address, you may be able to ping it or use other software to identify its IP. 
## Without WIFI
If the Pi is not connected to a WIFI network -- maybe the network has been removed or password has changed – you will need to connect directly to the Pi itself.  With the Pi removed from the wall and powered off, locate the ports on the rear inset of the display.  Connect an HDMI display to the mini-HDMI port.  Connect an On The Go (OTG) micro-USB cable to the center USB port and connect a wireless mouse / keyboard dongle to that cable.  Then, either connect the 5V, 10A power supply to the 2.1mm barrel jack port or connect a 5V, 4A power supply to the outside USB port on the Pi.  The Pi can be operated from only the USB power supply but if the RGB display is also on, the 4A power supply may not be powerful enough to drive the display and may cause the Pi to report a low voltage condition or it may just hang.

Once you have established the WIFI connection, you may want to revert to using the VNC Viewer application noted above.
# Program Configuration
The following assumes the user has basic knowledge of navigating through the Pi’s folder structure and how to edit a text file as those are beyond the scope of this document.

The display has a few user-configured options such as which Davis weather station to monitor and its operating hours.  To change the configuration, you will need to connect to the Pi using either of the methods noted above.  From the Home directory, navigate to the LED\_matrix folder.  For an existing system, in there you will find a configuration file named “config.json”.  For new installations, there is also a “config.json.sample” file that can be renamed or copied over.  The instructions for that are found further down in the [Installing the Software](README.md#Installing-the-Software) section.

Use a text editor to make any changes.  For example, from a terminal window and in the LED\_matrix folder, type: `sudo nano config.json`

The following options are found:

Property| |Description
--- | --- | ---
|`davis_weatherlinkIP_interface`||These are used for the legacy WeatherLinkIP device.
||`user`|Contrary to its name, this is the “Device ID” (DID) found under the “Device Info” screen when logged into your Davis account.  This is also shown on the back of the WeatherLinkIP device.  If this field is left blank, then the display will use the information and data from the newer console found in the next section.  If this field is not blank, then any information found in the next Console interface section is ignored.
||`password`|This is the same password you use to log into your Davis account.
|`OR_davis_console_interface`||These are for the newer 6313 Console.
||`api_key`|This key and its secret are found under your Davis “Account Information” screen, shown as “API Key V2"
||`api_secret`|
||`station_name`|This name is **case-sensitive** and set via the 6313 Console.  It is currently set to “Cadence at The Lakes”.
|`operating_hours`||Outside of the operating hours, the display will go blank and show only a blinking cursor in the lower right corner.
||`24_hours_per_day`|Set to `true` or `false`.  If false, the next two values are used.
||`on_time`|
||`off_time`|
|`dimmer`||The display can adjust its brightness based on the ambient light levels as detected by an optional light sensor found on the front edge of the display.
||`use_sensor`| If set to `true`, the sensor is used and the remaining options in this section are ignored.  The brightness of the display is adjusted every minute based on the current ambient light level.
||`daylight_offset_minutes`|If the sensor is not used or can’t be found, then the display calculates sunrise and sunset for this location and subtracts the value noted here from the sunrise or adds it to the sunset to estimate daylight hours.  During the daylight period, it sets the display brightness to the max setting below and outside of daylight hours, it sets the display brightness to the min setting.
||`max_brightness_percent`|Daylight brightness setting.
||`min_brightness_percent`|Nighttime brightness setting.
|`UV`||When the sun is above the horizon, the UV index is shown on the right side of the display.  When the sun has set, only the day’s high and low temperatures are shown.  When the UV is shown, you can optionally alternate the UV index with the high and low temperatures.
||`sunrise_sunset_offset_minutes`|The value here is added to the sunrise and subtracted from the sunset to estimate when the sun rises above or sets below the mountains as opposed to a flat horizon.  This is used to estimate the time during the day when sun is truly in view and thus, the UV index is shown.
||`alternate_with_hi_lo_temp`|If set to true, during the daytime, the right side of the display alternates between the UV index and the high and low temperatures.  Otherwise, the UV index is always shown during the day.
||`hi_lo_temp_length_seconds`|During each 60 second period, this is the number of seconds that the high and low temperatures are shown instead of the UV index.
|`adafruit_IO`||The following information is optional.  A free IoT account can be created at Adafruit.com.  Every 10 minutes, this display uploads information about itself, for example, internal CPU temperature, error count and current uptime.  The Adafruit IoT feed can be configured to send an email after a configured amount of inactivity thereby alerting an administrator that the display may be down or has lost WIFI connectivity.
||`user`|Enter your Adafruit username here.
||`key`|Adafruit API key.
||`feed`|Adafruit feed name “key”.
|`locale`||Information for your locale.  Used to determine sunrise, sunset, and temperature colours.
||`latitude`|Enter your latitude here.
||`longitude`|Longitude.
||`really_hot`|Temperatures above this will be red.
||`really_cold`|Temperatures below this will be purple.


# Error Messages
If the display encounters any issues with either connectivity or the retrieved data, depending on the issue, it will attempt to automatically recover.  During the recovery period, it may display an error message.

**Network connection error.  Check WiFi.  Will retry...:** The display has lost its WIFI connection.  Check the local WIFI devices.  Did someone change the network’s password?  Once reestablished, the display will take up to one minute to automatically refresh.   Should you need to connect to a new WIFI network, you will need to manually connect to the Pi using the HDMI and USB connections on the rear of the display and select the new WIFI network.  See “Connecting to the Pi” above.

**Outdated data.  Check local transmitter device**: Connectivity between this display and the Davis weather server still exists but the data being returned is more than a few minutes old.  This will also be reflected in the summary web page.  This is most likely due to the local WeatherLinkIP device or the 6313 Console either being powered off or having lost their connection to their local WIFI network.  Check that device and its WIFI network.  As soon as current data is uploaded again, the display will automatically refresh.

**Network HTTP error: ###:** This could be a server issue.  There is likely nothing you can do to correct this.  The display should recover automatically once the issue is corrected.

**Possible invalid Weatherlink username or password:**  Check the user (Device ID) or password entered in the config.json file.

**Possible invalid Weatherlink station name:** If using the Console interface, verify the weather station name.  Did you just edit it via the Console interface?  The name on the Console interface must match the name in the config.json file, and it is case sensitive.

**JSON key error: 'XXXX’ or JSON error: Expecting value: line X column Y (char Z)**: The data returned by the server is corrupt.  This is likely an intermittent problem with the server and will automatically correct itself.  There is nothing that can be done to correct this on this end. The display should recover automatically once the issue is remedied.
# Preparing the Raspberry Pi
## Installing the Operating System
Should you need to prepare a new Raspberry Pi from scratch, acquire a new micro-SD card (16Gb or more should be sufficient) and use the Raspberry Pi Imager for either a PC or Mac found here: <https://www.raspberrypi.com/software/>

When selecting the operating system, choose the “Raspberry Pi OS with desktop (Recommended)”.  

You may want to pre-edit the configuration options with a default username and password and the local WIFI username and password.  Alternatively, these settings can be edited later.   These installation notes assume a non-default user of “cadence,” but any username is fine if you adjust any reference to “cadence” to that of the user you have chosen.  Record the username and password for any future administrator.

After preparing the micro-SD card, insert it into the Raspberry Pi Zero 2 W.  Connect a mouse/keyboard dongle via a USB connector plugged into the Pi’s center USB port.  Connect a screen via the mini-HDMI connector of the Pi.  Plug a 5V power supply into the outside “PWR” USB connector and power it up.  Optionally, if the RGB matrix bonnet is already installed on top of the Pi, you can connect power to the 2.1mm barrel jack on the bonnet and the Pi will use its power.

The Pi will prompt you for some basic information and will then reboot.  It will then begin updating it’s OS to the latest version.  This may take several minutes.  When complete, it will boot up to a desktop.

If not already performed during the micro-SD card configuration, enter the network configuration area, and set up your local WIFI.

Click on the Raspberry icon on the menu and select:  Preferences à Raspberry Pi Configuration.

Under the Interfaces tab, ensure that I2C and optionally, VNC is enabled.  Wait for the VNC icon to appear in the upper right corner.  Reboot if you had to make any changes.

While you can continue to prepare the Pi using your directly connected monitor and mouse/keyboard dongle, if enabled above, you may want to install the Windows or Mac VNC terminal program and connect to the Pi using that.
## Installing the Software
The following steps explain how to install the necessary software for the display operation.  Detailed information about the RGB matrix bonnet and the steps to modify it by soldering a jumper can be found here: <https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi>

The LED-matrix library is copyrighted by Henner Zeller and a more in-depth explanation can be found here: <https://github.com/hzeller/rpi-rgb-led-matrix>

While you can view the links above, the software installation steps for the RGB matrix library files included in the links above are shown here…

Start a terminal window and while in the home folder, enter these commands:

`curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/main/rgb-matrix.sh >rgb-matrix.sh`

`sudo bash rgb-matrix.sh`

As noted in their instructions, this step will take several minutes to complete.  The system will prompt you to reboot.

As we are using a jumper to implement the “quality” option on the RGB matrix (see the learn.Adafruit.com link above), the sound card in the Pi must be disabled so as not to interfere.

`sudo nano /boot/config.txt`

In this file, look for the line containing “dtparam”.  If necessary, edit this line so that it reads:

`dtparam=audio=off`

Press CTRL-X to exit the editor and if changes were made, confirm “Save modified buffer”.

With the latest OS, it is necessary to further disable the sound card by entering the following commands:

`cat <<EOF | sudo tee /etc/modprobe.d/blacklist-rgb-matrix.conf`

\> `blacklist snd_bcm2835`

\> `EOF`

`sudo update-initramfs -u`

You will need to reboot again for the changes above to take effect.

Now that the RGB library files are installed, we will install our Python programs.  After rebooting, start a terminal window again and while in the home folder, enter the following commands:

`git clone https://github.com/Ringleton/LED-Matrix-Temperature-UV-Display.git ./LED_matrix`

`cd LED_matrix`

`sudo pip install -r requirements.txt`

It is now necessary to create a configuration file.  While still in the LED\_matrix folder, type:

`cp config.json.sample config.json`

Edit this file by typing:

`sudo nano config.json`

See the [Program Configuration](README.md#Program-Configuration) section above to make the necessary changes.  Once completed, press CTRL-X to exit the editor and save your changes.

Before setting up the automatic start feature for the display and optional reboot/shutdown button, test the program now by manually launching it.  While you are still in the LED\_matrix folder, type:

`sudo python temp_display.py`

If everything is working correctly, after a few seconds, you should see temperatures shown in the display.  If any error messages appear, you will need to address them.  They will appear on the screen when the program is run interactively but some will also be placed into a file named “logfile.log”.  This log file contains information messages, warning and errors and is overwritten each time the program is started.

To manually terminate the program, press CTRL-C.

NOTE: When launching the program, you may see a warning message suggesting editing the /boot/cmdline.txt file and adding “isolcpus=3” to the very end.  If you see that, from a terminal window, type the following command:

`sudo nano /boot/cmdline.txt`

At the very end of the single line, add a space, followed by `isolcpus=3`

Press CTRL-X to exit and save the file.

You will need to reboot for this change to take effect.  Then see if the warning message has cleared by manually launching the program again from a terminal window:

`cd ~`

`cd LED_matrix`

`sudo python temp_display.py`

# Automatic Start Files
The display also includes a pushbutton that can be used to reboot or shutdown the Pi safely without having to first connect to it.  The monitoring of this pushbutton is performed by a separate program in case the main display program terminates or becomes non-responsive.  

If you want the rear button enabled to allow reboot / shutdown capability, you will need to edit the rc.local file.  From a terminal window, type:

`sudo nano /etc/rc.local`

Immediately above the “exit 0” line, add:

`python /home/cadence/LED_matrix/restart_shutdown.py &`

**NOTE: if you have prepared the Pi using a different default user other than “cadence”, replace the occurrence above with your default username.**

Don’t forget the space and ampersand at the end of the line.  Press CTRL-X to exit and save the file.

To test this, reboot the Pi.  Once it has rebooted, try momentarily pressing the pushbutton on the back of the display enclosure.  The Pi should reboot.  Pressing and holding the button for at least two seconds will cause the Pi to shutdown.  Allow at least 20 seconds before disconnecting the power.

To make the main display program automatically start every time the Pi is powered up or rebooted, you will need to create an autostart file.  Before proceeding, ensure that the display program is running correctly when invoked manually as shown above.

Then from a terminal window, type the following lines:

`cd ~`

`cd .config`

`mkdir autostart`

`cd autostart`

`sudo nano display.desktop`

Enter the following lines:
```
[Desktop Entry]

Type=Application

Name=Display

Exec=bash -c 'cd /home/cadence/LED_matrix && sudo /usr/bin/python /home/cadence/LED_matrix/temp_display.py'
```
**NOTE: If you have prepared the Pi using a different default user other than “cadence”, replace the occurrences above with your default username.**

Press CTRL-X to exit and save your changes.  

To test your autostart file, reboot the Pi – you can use the pushbutton if enabled above – and confirm that the display automatically starts.  It may take up to a minute before you see anything in the display.
# Adafruit IoT Monitoring
The display includes the optional ability to upload internal statistics to an Adafruit IoT feed.  You can set up a free Adafruit account and create a feed.  You can configure the Adafruit feed to provide an email notification after a period of inactivity.  This can alert an administrator that the display is down or has lost its WIFI connection.

Enter your account and feed information into the config.json file as noted above in the [Program Configuration](README.md#Program-Configuration) section.  The following information is sent to the feed:

**CPU T:**	The internal CPU temperature.  The Pi will withstand temperatures up to 85 degrees Celsius.  As it gets closer to its upper limit, the system will automatically begin to throttle the processor down to try to help the CPU cool back down.

**Err:**  The total number of errors encountered since the program was started.  The program is designed to automatically recover from most errors that it encounters.

**Up:**  The total number of days that the program has been running.

**Mem Use:**  The total percentage of used memory.

**Set to:**  The display brightness percentage level.  Based on either the optional light sensor or the configuration settings with the time of day.

**Lux:**  The lux value from the sensor or -1 if not found.

**Light:**  The light level from the sensor.

Note: If you are connected to the Pi while the display program is running, pressing the Space Bar will temporarily show the statistics above on the display.
# 3D Files and Display Assembly
This project is published on github.com.  Included in the source code is a folder containing the 3D print files for the display enclosure.  You can either grab these files from the “3D-files” folder on the Pi after the software installation is completed or you can download the files from this link:

<https://github.com/Ringleton/LED-Matrix-Temperature-UV-Display>

The enclosure was printed using ABS print filament which provides UV protection.  There are a total of 15 mounting holes used for the 3 back panels.  Those holes are designed to accept M3 X 3mm brass heat-set inserts.  The main enclosure is available in a full print size but there are also separate left and right files in case your 3D printer cannot support the full size.

The optional VEML7700 light sensor and restart / shutdown pushbutton are connected to the Pi via the RGB bonnet – see photos below.

One side of the pushbutton is connected to ground, the other connects to GPIO pin 19.  The light sensor connects to a 3 X 2 header on the bonnet.  Looking from the top of the bonnet with the connector towards the right:

||<p></p><p></p>|<p></p><p></p>||
| :- | :- | :- | :- |
|Top Row|<p>Black</p><p>Ground</p>|<p>Red</p><p>3\.3V</p>|Not used|
|Bottom Row|Not used|<p>Yellow</p><p>SCL</p>|<p>Blue</p><p>SCA</p>|


![002](https://github.com/Ringleton/LED-Matrix-Temperature-UV-Display/assets/157074435/2a9dbf71-9bf8-4eac-a435-fb3cadde1af1)

![003](https://github.com/Ringleton/LED-Matrix-Temperature-UV-Display/assets/157074435/b67d66e3-179f-496a-886f-ee0c47e1ac95)

![004](https://github.com/Ringleton/LED-Matrix-Temperature-UV-Display/assets/157074435/1bf071d7-f117-45a3-88bb-6c8c3fe26630)

![005](https://github.com/Ringleton/LED-Matrix-Temperature-UV-Display/assets/157074435/86b78718-b918-436b-bb26-8d69b2e01381)


# Parts List

|**Part Description**|**Supplier**|**Part #**|**Qty**|
| :- | :- | :- | :- |
|Raspberry Pi Zero 2 W|Adafruit|5291|1|
|Break-away 0.1" 2x20-pin Strip Dual Male Header|Adafruit|2822|1|
|Micro-SD card|||1|
|2 X 64x32 RGB LED Matrix panels - 3mm pitch|Adafruit|2279|2|
|RGB Matrix bonnet for Raspberry Pi|Adafruit|3211|1|
|2x8 IDC ribbon cable, 12"|Adafruit|4170|1|
|Right angle VEML7700 light sensor|Adafruit|5378|1|
|STEMMA QT / Qwiic JST SH 4-pin Cable with<br>Premium Female Sockets - 150mm Long|Adafruit|4397|1|
|5V 10A switching power supply|Adafruit|658|1|
|Right angle 2x3 connector header|DigiKey|952-2092-ND|1|
|2\.1mm power plug with cable|DigiKey|839-1246-ND|1|
|Connector jack panel mount 5.5x2.1mm|DigiKey|839-1580-ND|1|
|Pushbutton switch SPST-NO 3A|DigiKey|EG1900-ND|1|
|3D-printed enclosure|||1|
|M2.5 & M3.0 nuts/bolts/spacers|||1|
|M3 X 3mm heat set inserts|Adafruit|4256|15|

# Davis Weather Station Devices and Account Information
The weather station at Cadence uses the following Davis Instruments devices:

- Wireless Vantage Pro 2 Weather Station 6252
- Solar-powered wireless sensor transmitter 6332 (used for the anemometer)
- Solar radiation sensor 6450
- UV sensor 6490
- WeatherLinkIP data logger / transmitter 6555
- WeatherLink Console 6313

The data is uploaded to the Davis WeatherLink.com site and this matrix display uses the Davis API to grab that data from their servers.  See the [Overview](README.md#Overview) section at the beginning of this document for more information.

Anyone can set up a free Davis account where you can monitor weather stations from around the world.  Optionally, you can upload weather data from  your weather station and share it with others.  At the time of this writing, both a legacy 6555 WeatherLinkIP data collector and the newer Davis 6313 Console are both being employed to upload data for Cadence and are treated as two separate weather stations even though the data for each is being transmitted by a single physical station device.

One advantage of the legacy device is that you can download the data via the API and that data is up to the minute, even with a non-subscription account.  Using the data from the newer console is available up to the minute only with a paid subscription.  Otherwise, that data is only updated every 15 minutes.

The legacy device plugs into a network router with a wired connection.  You can configure it using the Davis WeatherLink software for either Windows or a Mac.  This software download is available from Davis if you are logged in with your free Davis account.  Note that the software is very outdated but still works.  On a Windows system, you may have to “Run as Administrator”.

The newer Console connects to your local network over WIFI.  The configuration of that is performed through the Console itself using your Davis account username and password.

Weather station data from around the world is uploaded to the Davis server.  You can access your data and that of other stations via the WeatherLink.com site, your display console or the Davis Weather app, also available for free download.

When logged into your Davis account on the weatherlink.com website, you can also let someone see your weather station data via various URL’s without them needing to sign up for a Davis account.  You can access these URL’s via the “Share and Uploads” button under your account.  At the time of writing, one of those URL’s for the weather station data being sent by the console at Cadence is: <https://www.weatherlink.com/embeddablePage/show/17a85d105372405483298eef95e886b6/summary>

If later, a new Davis account is created and the physical weather station devices are moved over to that account, the URL links will likely also change.
