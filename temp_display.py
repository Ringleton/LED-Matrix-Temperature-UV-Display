# LED matrix temperature / UV display

# MIT License
# Copyright (c) 2025 by Russell Ingleton

import time
from datetime import datetime
import os
import sys
import json
import colorsys
import ryb2rgb
import requests
from requests.exceptions import ConnectionError
import threading
import argparse
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import board
import adafruit_veml7700
import busio
import ephem
import textwrap
import logging

# All of these are for various testing
import pynput
from pynput import keyboard 
import functools
import psutil  # for memory testing
from gpiozero import CPUTemperature  # for testing.  CPU temperature monitoring

# For Adafruit IoT feed that montiors CPU temp but also acts as a warning
# if the feed stops receiving information
from Adafruit_IO import Client, RequestError


def args():
    parser = argparse.ArgumentParser()

    # Options for the rpi-rgb-led-matrix library
    parser.add_argument("--led-rows", action="store", help="Display rows. 16 for 16x32, 32 for 32x32. (Default: 32)",
                        default=32, type=int)
    parser.add_argument("--led-cols", action="store", help="Panel columns. Typically 32 or 64. (Default: 64)",
                        default=64, type=int)
    parser.add_argument("--led-chain", action="store", help="Daisy-chained boards. (Default: 2)", default=2, type=int)
    parser.add_argument("--led-parallel", action="store",
                        help="For Plus-models or RPi2: parallel chains. 1..3. (Default: 1)", default=1, type=int)
    parser.add_argument("--led-pwm-bits", action="store", help="Bits used for PWM. Range 1..11. (Default: 11)",
                        default=11, type=int)
    parser.add_argument("--led-brightness", action="store", help="Sets brightness level. Range: 1..100. (Default: 100)",
                        default=100, type=int)
    parser.add_argument("--led-gpio-mapping", help="Hardware Mapping: regular, adafruit-hat, adafruit-hat-pwm",
                        default='adafruit-hat-pwm', choices=['regular', 'adafruit-hat', 'adafruit-hat-pwm'], type=str)
    parser.add_argument("--led-scan-mode", action="store",
                        help="Progressive or interlaced scan. 0 = Progressive, 1 = Interlaced. (Default: 1)", default=1,
                        choices=range(2), type=int)
    parser.add_argument("--led-pwm-lsb-nanoseconds", action="store",
                        help="Base time-unit for the on-time in the lowest significant bit in nanoseconds. (Default: 130)",
                        default=130, type=int)
    parser.add_argument("--led-pwm-dither-bits", action="store",
                        help="Time dithering of lower bits (Default: 0)",
                        default=0, type=int)
    parser.add_argument("--led-show-refresh", action="store_true",
                        help="Shows the current refresh rate of the LED panel.")
    parser.add_argument("--led-slowdown-gpio", action="store",
                        help="Slow down writing to GPIO. Range: 0..4. (Default: 1)", default=2, choices=range(5),
                        type=int)
    parser.add_argument("--led-limit-refresh", action="store",
                        help="Limit refresh rate to this frequency in Hz. Useful to keep a constant refresh rate on loaded system. 0=no limit. Default: 0",
                        default=150, type=int)
    parser.add_argument("--led-no-hardware-pulse", action="store", help="Don't use hardware pin-pulse generation.")
    parser.add_argument("--led-rgb-sequence", action="store",
                        help="Switch if your matrix has led colors swapped. (Default: RGB)", default="RGB", type=str)
    parser.add_argument("--led-pixel-mapper", action="store", help="Apply pixel mappers. e.g \"Rotate:90\"", default="",
                        type=str)
    parser.add_argument("--led-row-addr-type", action="store",
                        help="0 = default; 1 = AB-addressed panels; 2 = direct row select; 3 = ABC-addressed panels; 4 = ABC Shift + DE direct",
                        default=0, type=int, choices=[0, 1, 2, 3, 4])
    parser.add_argument("--led-multiplexing", action="store",
                        help="Multiplexing type: 0 = direct; 1 = strip; 2 = checker; 3 = spiral; 4 = Z-strip; 5 = ZnMirrorZStripe; 6 = coreman; 7 = Kaler2Scan; 8 = ZStripeUneven. (Default: 0)",
                        default=0, type=int)

    parser.add_argument("--led-panel-type", action="store",
                        help="Needed to initialize special panels. Supported: 'FM6126A'", default="", type=str)
    parser.add_argument("--led-no-drop-privs", dest="drop_privileges",
                        help="Don't drop privileges from 'root' after initializing the hardware.", action='store_false')
    parser.set_defaults(drop_privileges=True)

    return parser.parse_args()


def led_matrix_options(args):
    options = RGBMatrixOptions()

    if args.led_gpio_mapping != None:
        options.hardware_mapping = args.led_gpio_mapping

    options.rows = args.led_rows
    options.cols = args.led_cols
    options.chain_length = args.led_chain
    options.parallel = args.led_parallel
    options.row_address_type = args.led_row_addr_type
    options.multiplexing = args.led_multiplexing
    options.pwm_bits = args.led_pwm_bits
    options.brightness = args.led_brightness
    options.pwm_lsb_nanoseconds = args.led_pwm_lsb_nanoseconds
    options.led_rgb_sequence = args.led_rgb_sequence
    options.panel_type = args.led_panel_type
    options.limit_refresh_rate_hz = args.led_limit_refresh
    try:
        options.pixel_mapper_config = args.led_pixel_mapper
    except AttributeError:
        logging.critical('Your compiled RGB Matrix Library is out of date.\n'
                         '                     The --led-pixel-mapper argument will not work until it is updated.')
        
    if args.led_show_refresh:
        options.show_refresh_rate = 1

    if args.led_slowdown_gpio != None:
        options.gpio_slowdown = args.led_slowdown_gpio

    if args.led_no_hardware_pulse:
        options.disable_hardware_pulsing = True

    if not args.drop_privileges:
        options.drop_privileges = False

    # Must force this to False to allow the VEML7700 light sensor to work.
    options.drop_privileges = False

    return options


class Config:
    def __init__(self):

        filename = "config.json"

        if os.path.isfile(filename):
            try:
                jdata = json.load(open(filename))
            except json.decoder.JSONDecodeError as err:
                logging.critical('Invalid json file: %s', err)
                exit(1)
        else:
            logging.critical('Could not find configuration file: %s', filename)
            exit(1)

        # If the WeatherLinkIP device is being used for uploading then
        #   the V1 API data is refreshed every minute.  Use it.
        self.davis_user = jdata["davis_weatherlinkIP_interface"]["user"]
        self.davis_password = jdata["davis_weatherlinkIP_interface"]["password"]

        # Otherwise, use the data uploaded from the newer console.
        # This data is refreshed every 15 minutes (free subscription)
        #   or every 5 or 1 minute intervals (paid subscription)
        self.davis_key = jdata["OR_davis_console_interface"]["api_key"]
        self.davis_secret = jdata["OR_davis_console_interface"]["api_secret"]
        self.davis_station_name = jdata["OR_davis_console_interface"]["station_name"]

        if self.davis_user == "" and self.davis_key == "":
            logging.critical('You must specify user account credentials for at least one interface in the configuration file: %s',
                             filename)
            exit(1)

        self.op_hours_24_hours_per_day = jdata["operating_hours"]["24_hours_per_day"]
        try:
            self.open_at = datetime.strptime(jdata["operating_hours"]["on_time"], '%H:%M').time()
            self.closed_at = datetime.strptime(jdata["operating_hours"]["off_time"], '%H:%M').time()
        except ValueError:
            logging.critical('Invalid operating hours in configuration file: %s', filename)
            exit(1)

        self.use_sensor = jdata["dimmer"]["use_sensor"]
        self.max_brightness_percent = jdata["dimmer"]["max_brightness_percent"]
        if self.max_brightness_percent > 100:
            self.max_brightness_percent = 100
        self.min_brightness_percent = jdata["dimmer"]["min_brightness_percent"]
        if self.min_brightness_percent < 0:
            self.min_brightness_percent = 0

        self.show_UV = jdata["UV"]["show_UV"]
        self.show_temp_with_UV = jdata["UV"]["alternate_with_hi_lo_temp"]
        self.hi_lo_temp_length_seconds = jdata["UV"]["hi_lo_temp_length_seconds"]
        # Main loop repeats every 60 seconds.  So the high/lo temp display must be less than that.  Let's max it at 55 seconds.
        if self.hi_lo_temp_length_seconds > 55:
            self.hi_lo_temp_length_seconds = 55

        # Using Adafruit IO feed to upload statistics and monitor if down.
        self.adafruitIO_user = jdata["adafruit_IO"]["user"]
        self.adafruitIO_key = jdata["adafruit_IO"]["key"]
        self.adafruitIO_feed = jdata["adafruit_IO"]["feed"]

        # Longitude, latitude location.  Used to determine sunrise / sunset.
        self.my_location_lat = str(jdata["locale"]["latitude"])
        self.my_location_lon = str(jdata["locale"]["longitude"])
        self.my_location_horizon = str(jdata["locale"]["horizon"])

        # This sets the max and min temperatures for what will be the most red (hot) and
        # most purple (cold) colors.  Values beyond these will stay at their max color.
        # Set appropriately for your locale
        self.really_hot = jdata["locale"]["really_hot"]
        self.really_cold = jdata["locale"]["really_cold"]
        
        self.use_Celsius = jdata["use_Celsius"]


class Data:
    def __init__(self, config, matrix):
        self.config = config
        self.matrix = matrix

        self.temp_now = None
        self.UV = None
        self.show_hi_low_temp = False
        self.after_hours = False  # to keep track of opening / closing hours
        self.error_count = 5  # to keep track of consecutive API failures
        self.master_error_count = 0  # for testing purposes.  Overall # of API errors.  Prints in log file.
        self.start_time = datetime.now()

        # timer threads
        self.timer_main = None
        self.timer_blink = None
        self.timer_show_UV = None

        self.canvas = self.matrix.CreateFrameCanvas()

        # Load our fonts
        self.font_small = graphics.Font()
        self.font_small.LoadFont("./fonts/4x6.bdf")
        self.font_med = graphics.Font()
        self.font_med.LoadFont("./fonts/8x13B.bdf")
        self.font_large = graphics.Font()
        self.font_large.LoadFont("./fonts/Helvetica38.bdf")
        self.font_msg = graphics.Font()
        self.font_msg.LoadFont("./fonts/7x13.bdf")

        # Used for text titles
        self.title_color = graphics.Color(255, 255, 255)  # white

        filename = "high-lows.data"

        if os.path.isfile(filename):
            with open(filename, "r") as file:
                data = file.read().replace('\n', '')
                self.hi_low_date, self.temp_high, self.temp_low = map(float, data.split(" "))

        else:  # no file.  Fake hi/low date to be outdated.
            self.hi_low_date = datetime.now().timetuple().tm_yday - 1
            self.temp_high = self.temp_low = None

        self.light = None
        self.lux_sensor_available = False 
        if self.config.use_sensor:
            try:
                self.i2c = board.I2C()

                # Grab first reading to ensure sensor is available
                sensor = adafruit_veml7700.VEML7700(self.i2c)
                self.lux_sensor_available = True

            except:
                logging.warning('Light sensor not found or not connected, falling back to software mode.')

        # create a REST client instance for the IoT feed
        self.io_client = Client(self.config.adafruitIO_user, self.config.adafruitIO_key)


# This function will get all temperature values and store for use
def get_temp(data):

    # Use the V1 API if a username was specified in the config file.
    if data.config.davis_user != "":
        DAVIS_V1_API_BASE = "https://api.weatherlink.com/v1/NoaaExt.json?user="
        DAVIS_V1_API_URL = DAVIS_V1_API_BASE + data.config.davis_user + "&pass=" + data.config.davis_password

        try:
            response = requests.get(DAVIS_V1_API_URL)
            
            # Force close to free resources / stop slow memory leak
            response.close()

            if response.status_code == 200:
                if response.text == 'Invalid Request!':
                    data.error_count += 1
                    data.master_error_count += 1
                    logging.critical('Consecutive error count: %d.  Total error count: %d.\n'
                                  '                     Possible invalid Davis WeatherlinkIP username or password.\n'
                                  '                     Verify credentials and check config.json file.',
                                  data.error_count, data.master_error_count)

                    # This is likely a permanent error until fixed.  We will always return a failure regardless as to error count
                    return (0, "Possible invalid Weatherlink user name or password")

                else:  # We have a valid V1 response request
                    try:
                        results = response.json()
                        
                        # Set defaults in case no valid temp or UV readings returned.
                        data.temp_now = data.UV = None
                        data.temp_high = -999
                        data.temp_low = 999
                        
                        try:
                            age = int(results['davis_current_observation']['observation_age'])
                            if age > (5 * 60):  # if data is older than 5 minutes
                                data.error_count += 1
                                data.master_error_count += 1
                                logging.warning('Consecutive error count: %d.  Total error count: %d.\n'
                                                '                     Outdated data.  Data is %d minutes old.\n'
                                                '                     Check the local Davis Weatherlink transmitter device and its network\n'
                                                '                     connectivity.  There is nothing wrong with this display system!',
                                                data.error_count, data.master_error_count, int(age / 60))

                                # The first time we are here, data is already 5 minutes old so waiting 5 times = 10 minutes to error.
                                if data.error_count > 5:
                                    return (0, "Outdated data.  Check local transmitter device")

                                # else we will just fall through and continue to grab the data even though it will be the same as last

                            # if not an age issue, then reset our consecutive error count back to zero.
                            else:
                                data.error_count = 0
                                
                            # Get current temp
                            try:
                                if data.config.use_Celsius:
                                    data.temp_now = float(results['temp_c'])
                                else:
                                    data.temp_now = float(results['temp_f'])
                                    
                            # Key could be missing if battery on main station is dead
                            # If so, continue without error.  Value will be displayed as "---"
                            except KeyError:
                                pass

                            try:
                                data.temp_high = float(results['davis_current_observation']['temp_day_high_f'])
                                data.temp_low = float(results['davis_current_observation']['temp_day_low_f'])

                                if data.config.use_Celsius:
                                    data.temp_high = round((data.temp_high - 32) * 5 / 9, 1)
                                    data.temp_low = round((data.temp_low - 32) * 5 / 9, 1)

                            except KeyError:
                                pass

                            try:
                                data.UV = float(results['davis_current_observation']['uv_index'])
                                
                            except KeyError:
                                pass

                            return (1, "Success")

                        except KeyError as err:
                            data.error_count += 1
                            data.master_error_count += 1
                            logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                                          '                     There was json error in the Davis data feed trying to read key: %s',
                                          data.error_count, data.master_error_count, err)

                            if data.error_count > 5:
                                return (0, f"JSON key error: {err}")
                            else:
                                return (1, f"JSON key error: {err}")

                    except json.decoder.JSONDecodeError as err:
                        data.error_count += 1
                        data.master_error_count += 1
                        logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                                      '                     Invalid JSON file: %s',
                                      data.error_count, data.master_error_count, err)

                        if data.error_count > 5:
                            return (0, f"JSON error: {err}")
                        else:
                            return (1, "Warning")

            else:  # we got a V1 response code != 200
                data.error_count += 1
                data.master_error_count += 1
                logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                              '                     HTTP Error: %s',
                              data.error_count, data.master_error_count, response.status_code)

                if data.error_count > 5:
                    return (0, f"Network HTTP error: {response.status_code}")
                else:
                    return (1, "Warning")


        except requests.exceptions.ConnectionError as err:

            # Internet / network is lost
            data.error_count += 1
            data.master_error_count += 1
            logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                          '                     Encountered a network connection error: %s',
                          data.error_count, data.master_error_count, err)

            if data.error_count > 5:
                return (0, f"Network connection error.  Check WiFi Will retry...")
            else:
                return (1, "Warning")

    else:  # V1 username was blank so use V2 interface
        DAVIS_V2_API_BASE = "https://api.weatherlink.com/v2/stations?"
        DAVIS_V2_API_URL = DAVIS_V2_API_BASE + "api-key=" + data.config.davis_key

        try:
            response = requests.get(
                headers={
                    "X-Api-Secret": data.config.davis_secret
                },
                url=DAVIS_V2_API_URL,
                verify=True,
            )
            response.close()
            
            if response.status_code == 200:
                try:
                    results = response.json()
                    try:
                        station_id = ''
                        # If only one station on this WeatherLink account, use it regardless of name match
                        if len(results) == 1:
                            station_id = results['stations'][0]['station_id']
                        else:  # Loop through all stations until we find the matching one
                            for i in range(len(results)):
                                if results['stations'][i]['station_name'] == data.config.davis_station_name:
                                    # Grab the internal ID for that station to be used below
                                    station_id = results['stations'][i]['station_id']
                                    break

                        if station_id:
                            # we now have the ID of the V2 API station that we will be using so let's get
                            # the current readings from all the sensors associated with that station.
                            DAVIS_V2_API_BASE = "https://api.weatherlink.com/v2/current/"
                            DAVIS_V2_API_URL = DAVIS_V2_API_BASE + str(station_id) + "?api-key=" + data.config.davis_key

                            response = requests.get(
                                headers={
                                    "X-Api-Secret": data.config.davis_secret
                                },
                                url=DAVIS_V2_API_URL,
                                verify=True,
                            )
                            response.close()

                            if response.status_code == 200:
                                results = response.json()

                                temp = uv = timestamp = None  # Set a default in case no valid temp or UV readings returned.
                                try:
                                    i = 0
                                    while True:  # loop through the various sensors found on this station
                                        keys = []
                                        if results['sensors'][i]['data_structure_type'] == 23:
                                            # This is from a Davis 6313 Console
                                            keys = ["temp", "uv_index", "ts"]
                                        elif results['sensors'][i]['data_structure_type'] == 2:
                                            # This is from a WeatherLinkIP device
                                            keys = ["temp_out", "uv", "ts"]

                                        if keys:
                                            if temp is None:
                                                try:
                                                    temp = results['sensors'][i]['data'][0][keys[0]]
                                                    if temp is not None:
                                                        # Get the timestamp belonging to this sensor that we grabbed temperature from.
                                                        timestamp = int(results['sensors'][i]['data'][0][keys[2]])
                                                # Ignore error if temp sensor fails.  UV will still display.
                                                # User should see sensor is missing in local console.
                                                except KeyError:
                                                    pass

                                            if uv is None:
                                                try:
                                                    uv = results['sensors'][i]['data'][0][keys[1]]
                                                    if uv is not None and timestamp is None:
                                                        timestamp = int(results['sensors'][i]['data'][0][keys[2]])
                                                # Ignore error if UV sensor fails.  Temperature will still display.
                                                # User should see sensor is missing in local console.
                                                except KeyError:
                                                    pass

                                        i += 1  # next sensor
                                except IndexError:  # end of sensor loop
                                    pass

                                #  A zero-cost subscription provides 15 minute interval updates so anything over that means out of date.
                                if timestamp is not None and ((datetime.now()-datetime.fromtimestamp(timestamp)).total_seconds() / 60) > 16:
                                    data.error_count += 1
                                    data.master_error_count += 1
                                    logging.warning('Consecutive error count: %d.  Total error count: %d.\n'
                                                    '                     Outdated data.  Data is %d minutes old.\n'
                                                    '                     Check the local Davis Weatherlink transmitter device and its network\n'
                                                    '                     connectivity.  There is nothing wrong with this display system!',
                                                    data.error_count, data.master_error_count,
                                                    round((datetime.now()-datetime.fromtimestamp(timestamp)).total_seconds() / 60))

                                    # The first time we are here, data is already 15 minutes old so waiting 5 more times = 20 minutes to error.
                                    if data.error_count > 5:
                                        return (0, "Outdated data.  Check local transmitter device")

                                # if not an age issue, then data is all good. Reset our consecutive error count back to zero.
                                else:
                                    data.error_count = 0

                                # Even if age was too old, but under 5 consecutive times, we will just fall through
                                #  and continue to grab the data even though it will be the same as last

                                if temp is not None:
                                    if data.config.use_Celsius:
                                        data.temp_now = round((float(temp) - 32) / 9 * 5, 1)
                                    else:
                                        data.temp_now = float(temp)
                                else:
                                    data.temp_now = None

                                if uv is not None:
                                    data.UV = float(uv)
                                else:
                                    data.UV = None

                                # Check to see if we have a new daily high or low
                                # if previous hi/lo date is different than now or if we have a new high or new low,
                                # then set our new hi/lo values and update the file
                                if data.hi_low_date != datetime.now().timetuple().tm_yday:
                                    #  we have a new day for highs and lows
                                    data.hi_low_date = datetime.now().timetuple().tm_yday
                                    data.temp_high = -999
                                    data.temp_low = 999

                                # new high or new low?
                                if data.temp_now is not None:
                                    if data.temp_now > data.temp_high or data.temp_now < data.temp_low:
                                        if data.temp_now > data.temp_high:
                                            data.temp_high = data.temp_now
                                        if data.temp_now < data.temp_low:
                                            data.temp_low = data.temp_now

                                        filename = "high-lows.data"

                                        with open(filename, "w") as file:
                                            file.write(f"{data.hi_low_date} {data.temp_high} {data.temp_low}")

                                return 1, "Success"

                            else:
                                # One possible error here is 404 {"code":"404","message":"Unable to find weather station settings"}
                                # But don't know if others are possible
                                data.error_count += 1
                                data.master_error_count += 1

                                results = response.json()
                                logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                                              '                     HTTP Error: %s.  %s',
                                              data.error_count, data.master_error_count, response.status_code, results['message'])

                                if data.error_count > 5:
                                    return (0, f"Network HTTP error: {response.status_code}")
                                else:
                                    return (1, "Warning")
                                
                        else:  # Could not find V2 station name
                            data.error_count += 1
                            data.master_error_count += 1
                            logging.critical('Consecutive error count: %d.  Total error count: %d.\n'
                                             '                     Could not find station named: %s\n'
                                             '                     Verify credentials and check config.json file.',
                                             data.error_count, data.master_error_count, data.config.davis_station_name)

                            # This is likely a permanent error until fixed.  We will always return a failure regardless as to error count
                            return (0, "Possible invalid Weatherlink station name")

                    except KeyError as err:
                        data.error_count += 1
                        data.master_error_count += 1
                        logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                                      '                     There was json error in the Davis data feed trying to read key: %s',
                                      data.error_count, data.master_error_count, err)

                        if data.error_count > 5:
                            return (0, f"JSON key error: {err}")
                        else:
                            return (1, f"JSON key error: {err}")

                except json.decoder.JSONDecodeError as err:
                    data.error_count += 1
                    data.master_error_count += 1
                    logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                                  '                     Invalid JSON file: %s',
                                  data.error_count, data.master_error_count, err)

                    if data.error_count > 5:
                        return (0, f"JSON error: {err}")
                    else:
                        return (1, "Warning")

            else:  # Was not a 200 response code for V2.  Possible 401 code?
                # Bad key:  401 {"message":"Invalid authentication credentials"}
                # Bad secret: 401 {"code":"401","message":"Invalid API Key/API Secret."}
                # Could be others?
                data.error_count += 1
                data.master_error_count += 1
                if response.status_code == 401:
                    logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                                  '                     HTTP Error: %s\n'
                                  '                     Possible invalid Davis Weatherlink API V2 key or secret.\n'
                                  '                     Verify credentials and check config.json file.',
                                  data.error_count, data.master_error_count, response.status_code)
                else:
                    logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                                  '                     HTTP Error: %s',
                                  data.error_count, data.master_error_count, response.status_code)

                if data.error_count > 5:
                    if response.status_code == 401:
                        return (0, f"Network HTTP error: {response.status_code}. Bad API key or secret?")
                    else:
                        return (0, f"Network HTTP error: {response.status_code}")
                else:
                    return (1, "Warning")

        except requests.exceptions.ConnectionError as err:

            # Internet / network is lost
            data.error_count += 1
            data.master_error_count += 1
            logging.error('Consecutive error count: %d.  Total error count: %d.\n'
                          '                     Encountered a network connection error: %s',
                          data.error_count, data.master_error_count, err)

            if data.error_count > 5:
                return (0, f"Network connection error.  Check WiFi Will retry...")
            else:
                return (1, "Warning")

def get_colour(data, temp):

    really_hot = data.config.really_hot
    really_cold = data.config.really_cold
    
    # cap out at the max temps allowed
    if temp > really_hot:
        temp = really_hot
    elif temp < really_cold:
        temp = really_cold

    # Anything below freezing will be blue or purple
    # If using that other scale, must convert to Celsius to make this work
    if not data.config.use_Celsius:
        temp = (temp - 32) * 5 / 9
        really_hot = (really_hot - 32) * 5 / 9
        really_cold = (really_cold - 32) * 5 / 9

    if temp >= 0:
        full_range = really_hot
        z = (really_hot - temp) / full_range * 210  # 0 - 210
    else:
        full_range = -really_cold
        z = (-temp) / full_range * 90 + 210  # 210 - 300

    # Convert degrees (of a circle) to the RYB colour wheel
    # RYB colour wheel provides best rainbow of colours
    r, yellow, b = colorsys.hsv_to_rgb(z / 360.0, 1.0, 1.0)

    R, Y, B = int(255 * r), int(255 * yellow), int(255 * b)

    # Convert RYB to RGB
    R, G, B = ryb2rgb.ryb2rgb(R, Y, B)

    return (R, G, B)


def get_colour_UV(UV):
    # This will return Environment Canada UV Index colours

    if UV < 3.0:  # low - green
        return (79, 179, 0)
    elif UV < 6.0:  # moderate - yellow
        return (253, 205, 0)
    elif UV < 8.0:  # high - orange
        return (255, 102, 0)
    elif UV < 11.0:  # very high - red
        return (255, 0, 0)
    else:  # extreme - purple
        return (206, 49, 254)


def get_sunrise_sunset(data, horizon):
    my_location = ephem.Observer()

    my_location.lat = data.config.my_location_lat
    my_location.lon = data.config.my_location_lon
    my_location.horizon = horizon

    sun = ephem.Sun()

    current = ephem.now()
    
    try:
        sunrise = my_location.next_rising(sun)
        sunset = my_location.next_setting(sun)

        # if the next sunrise and/or sunset is now tomorrow, then we need to get the previous one (= today's)
        # so that this function always returns today's sunrise and sunset regardless as to the current time of day
        if ephem.localtime(sunrise).day != ephem.localtime(current).day:
            sunrise = my_location.previous_rising(sun)

        if ephem.localtime(sunset).day != ephem.localtime(current).day:
            sunset = my_location.previous_setting(sun)

        return sunrise, sunset, current
    
    # And just in case you are in a very high +/- latitude
    except ephem.NeverUpError:
        return current +1, current -1 , current
    
    except ephem.AlwaysUpError:
        return current -1, current + 1, current


def estimate_brightness(data):
    # How bright is it outside?  Sun may not be above the horizon but it could be dawn or dusk.
    # Looks at nighttime, daytime and twilight hours to esimate light level.  Returns 0.0 to 1.0.
    # Used to determine display brightness if not using light sensor

    # Get sunrise, sunset based on our true horizon
    sunrise, sunset, current = get_sunrise_sunset(data, data.config.my_location_horizon)
    
    # Civil twilight is considered to be 6.0 degrees below horizon.
    twilight_start, twilight_end, current = get_sunrise_sunset(data, str(float(data.config.my_location_horizon) - 6.0))

    # Is the sky dark?
    if current < twilight_start or current > twilight_end:
        return 0.0
    
    # Is it the middle of the day?
    elif sunrise < current < sunset:
        return 1.0
    
    # Else, we are in The Twilight Zone!
    elif current < sunrise:
        return 1.0 - (sunrise - current) / (sunrise - twilight_start)
    else:
        return 1.0 + (sunset - current) / (twilight_end - sunset)


def is_sun_above(data):
    # Is the sun above the horizon?
    # Used to determine when we start showing the UV value.  No point when sun not above our horizon.

    sunrise, sunset, current = get_sunrise_sunset(data, data.config.my_location_horizon)
    return sunrise < current < sunset


def set_brightness(data):

    if data.config.use_sensor and data.lux_sensor_available:
        try:
            sensor = adafruit_veml7700.VEML7700(data.i2c)

            data.light=sensor.light

            # map sensor brightness levels to matrix brightness percentage equivalent
            light_in =   [2000, 500, 200, 50,  0]
            percent_out = [100,  60,  40, 30, 20]

            for i, level in enumerate(light_in):
                if data.light >= level:
                    break

            if i == 0:
                b = percent_out[0]
            else:
                b = int((data.light - light_in[i]) / (light_in[i-1] - light_in[i]) *
                        (percent_out[i-1] - percent_out[i]) + percent_out[i])
        except:
            logging.warning('Light sensor lost.  Falling back to software mode.')
            data.lux_sensor_available = False 


    if not data.config.use_sensor or not data.lux_sensor_available: # no sensor - estimate light
        data.light = estimate_brightness(data)
        b = int((data.config.max_brightness_percent - data.config.min_brightness_percent) *
                data.light + data.config.min_brightness_percent)
        
        data.light *= 100  # For display purposes only

    data.matrix.brightness = b


# When after hours, clear the display but show a blinking cursor so we know that the display is still active.
class Blink_pixel:

    def __init__(self, data):
        self.data = data
        self.on = False
        
        self.data.canvas.Clear()

    def blink(self):

        self.on = not self.on
        if self.on:
            x = 150  # lighter white
        else:
            x = 0

        # See if we are still in the non-operational hours and if so, display the cursor and fire this to run again in one second.
        # Otherwise, this method just ends and does not retrigger until the main loop fires it up at the start of the next end-of-day.
        if self.data.after_hours == True:
            # closed hours

            h = self.data.matrix.height
            w = self.data.matrix.width

            # Place a 2 X 2 cursor in the lower right corner
            graphics.DrawLine(self.data.canvas, w - 2, h - 2, w - 1, h - 2, graphics.Color(x, x, x))
            graphics.DrawLine(self.data.canvas, w - 2, h - 1, w - 1, h - 1, graphics.Color(x, x, x))

            self.data.matrix.SwapOnVSync(self.data.canvas)

            # Fire this method again in one second to toggle the cursor
            self.data.timer_blink = threading.Timer(1, self.blink)
            self.data.timer_blink.start()


def enable_UV(data):
    data.show_hi_lo_temp = False
    refresh_display(data)


def refresh_display(data):

    if data.temp_now is None:
        sTemp = ' ---'
        r = g = b = 255
    else:
        if data.temp_now >= 100.0:
            # Can't fit 4-digit temps on this display so grab 3.  Will add decimal later.
            sTemp = '%d' % data.temp_now
        else:
            sTemp = '%.1f' % data.temp_now
            
        r, g, b = get_colour(data, data.temp_now)

    temp_color = graphics.Color(r, g, b)

    if data.temp_high == -999:
        sHi = '---'
        r = g = b = 255
    else:
        sHi = '%.1f' % data.temp_high
        r, g, b = get_colour(data, data.temp_high)

    temp_high_color = graphics.Color(r, g, b)

    if data.temp_low == 999:
        sLo = '---'
        r = g = b = 255
    else:
        sLo = '%.1f' % data.temp_low
        r, g, b = get_colour(data, data.temp_low)

    temp_low_color = graphics.Color(r, g, b)

    if data.UV is None:
        sUV = '---'
        r = g = b = 255
    else:
        sUV = '%.1f' % data.UV
        r, g, b = get_colour_UV(data.UV)
    
    UV_color = graphics.Color(r, g, b)

    sHiLoTitle = 'High-Low'
    sUVTitle = 'UV'

    # Determine pixel length required for each string / font.  Needs to draw on a canvas to determine - we will clear shortly
    lenHiLoTitle = graphics.DrawText(data.canvas, data.font_small, 0, 0, data.title_color, sHiLoTitle)
    lenUVTitle = graphics.DrawText(data.canvas, data.font_med, 0, 0, data.title_color, sUVTitle)
    lenTemp = graphics.DrawText(data.canvas, data.font_large, 0, 0, data.title_color, sTemp)
    lenHi = graphics.DrawText(data.canvas, data.font_med, 0, 0, data.title_color, sHi)
    lenLo = graphics.DrawText(data.canvas, data.font_med, 0, 0, data.title_color, sLo)
    lenUV = graphics.DrawText(data.canvas, data.font_med, 0, 0, data.title_color, sUV)
    lenMaxHiLo = max(lenHi, lenLo)
    panel_width = data.canvas.width

    data.canvas.Clear()
    graphics.DrawText(data.canvas, data.font_large, 0, 29, temp_color, sTemp)

    # If >= 100 (Fahrenheit), it won't all fit so put decimal portion in a smaller font
    if data.temp_now and data.temp_now >= 100.0:
        graphics.DrawText(data.canvas, data.font_med, lenTemp-5, 29, temp_color, ('%.1f' % data.temp_now)[3:5])

    # Knowing the lengths in pixels, determine the starting pixel positions for each string
    # The display is split into two halves; current temperature always on the left and hi/lo Temps / UV on the right
    end_pos = panel_width

    if data.show_hi_lo_temp:

        if lenHiLoTitle > lenMaxHiLo and int((lenHiLoTitle - lenMaxHiLo) / 2) + end_pos > panel_width:
            end_pos -= int((lenHiLoTitle - lenMaxHiLo) / 2) + end_pos - panel_width

        end_pos += 1
        HiLoTitle_pos = end_pos - (lenMaxHiLo - lenHiLoTitle) / 2 - lenHiLoTitle
        Hi_pos = end_pos - lenHi
        Lo_pos = end_pos - lenLo

        graphics.DrawText(data.canvas, data.font_small, HiLoTitle_pos, 6, data.title_color, sHiLoTitle)
        graphics.DrawText(data.canvas, data.font_med, Hi_pos, 19, temp_high_color, sHi)
        graphics.DrawText(data.canvas, data.font_med, Lo_pos, 31, temp_low_color, sLo)

    else:  # showing UV

        # This "if" should never occur if the title stays very short such as "UV"
        if lenUVTitle > lenUV and int((lenUVTitle - lenUV) / 2) + end_pos > panel_width:
            end_pos -= int((lenUVTitle - lenUV) / 2) + end_pos - panel_width

        end_pos += 1
        UVTitle_pos = end_pos - (lenUV - lenUVTitle) / 2 - lenUVTitle
        UV_pos = end_pos - lenUV

        graphics.DrawText(data.canvas, data.font_med, UVTitle_pos, 14, data.title_color, sUVTitle)
        graphics.DrawText(data.canvas, data.font_med, UV_pos, 28, UV_color, sUV)

    data.matrix.SwapOnVSync(data.canvas)


def error_display(data, text):
    # Possible error messages

    # "Possible invalid Weatherlink user name or password"
    # "Possible invalid Weatherlink station name"
    # "Outdated data.  Check local transmitter device"
    # "JSON key error: 'davis_current_observation'"
    # "JSON error: Expecting value: line 1 column 1 (char 0)"
    # "Network connection error.  Check WiFi Will retry..."
    # "Network HTTP error: ###"
    
    line = textwrap.wrap(text, 18)

    data.canvas.Clear()

    for i in range(len(line)):
        graphics.DrawText(data.canvas, data.font_msg, 0, i * 11 + 9, data.title_color, line[i])

    data.matrix.SwapOnVSync(data.canvas)

# testing
# press 0-9 to set 100%, 10 - 90% brightness
# press space to have above confirmed, along with current light setting.
def on_key_press(data, key):
    
    try:
        if key.char is not None and '0' <= key.char <= '9':
            i = int(key.char) * 10
            if (i == 0):
                i = 100
            data.matrix.brightness = i
            refresh_display(data)

    except AttributeError:

        if key.space:
            # Create a string of status info
            
            # Up:### Mem Use:##%
            # CPU T:##.# Err:###
            # Lt:### Bright:###%
            message="Up:%3d Mem Use:%2d%%" % ((datetime.now()-data.start_time).days, psutil.virtual_memory().percent)
            message += " CPU T:%4.1f Err:%3d" % (CPUTemperature().temperature, data.master_error_count )
            message += " Lt:"
            if data.light > 999:
                message += "%2dk" % int(data.light/1000)
            else:
                message += "%3d" % data.light
            message += " Bright:%3d%%" % data.matrix.brightness
            
            error_display(data, message)

    
def main_loop(data):
    # this loop is executed every 60 seconds

    # go get and set the matrix brightness
    set_brightness(data)

    # see if we are in the non-operational hours
    current = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M").time()

    if not data.config.op_hours_24_hours_per_day and not (data.config.open_at <= current < data.config.closed_at):
        # closed hours
        
        # Even if it is after hours, if we are using the V2 API, we must continuously
        # read the temperature so that the daily highs and lows can be maintained
        # by this program even though we are not displaying anything during this period.
        # FYI: The V1 API maintains its own high/lows and when using V1, we read
        # those directly.
        if data.config.davis_user == "":  # Using V2 API
            get_temp(data)
            
        # if the after hours timer has never been initialize or we are just entering after hours for the first time today...
        if not data.timer_blink or not data.after_hours:

            data.after_hours = True
            Blink_pixel(data).blink()

    else:  # opening hours

        success, msg = get_temp(data)

        # This will cause the after hours blinking to not re-trigger itself.
        data.after_hours = False

        if success:
            # We have good data for displaying
            
            if not data.config.show_UV:
                data.show_hi_lo_temp = True

            elif not is_sun_above(data):
                # This sun is not high in the sky so show the high/lows
                data.show_hi_lo_temp = True

            elif data.config.show_temp_with_UV:
                # Sun high in the sky (show UV) but you wanted to still show high/lows initially
                data.show_hi_lo_temp = True

                # Set a timer to flip back to UV in a few (configurable) seconds
                data.timer_show_UV = threading.Timer(data.config.hi_lo_temp_length_seconds, enable_UV, [data])
                data.timer_show_UV.start()

            else:  # The sun is above and we want only UV
                data.show_hi_lo_temp = False

            refresh_display(data)

        else:  # We had an error while attempting to get our weather data
            error_display(data, msg)

    # For monitoring purposes, send IoT feed CPU temperature every 10 minutes
    # If enabled, an email notification is sent if nothing received after one hour.
    if datetime.now().minute % 10 == 0:
        try:
            #  CPU T:61.3 Err:123 Up:123 Mem Use:45% Light:30k Brightness:100%
            message = "CPU T:%4.1f Err:%3d" % (CPUTemperature().temperature, data.master_error_count )
            message += " Up:%3d Mem Use:%2d%%" % ((datetime.now()-data.start_time).days, psutil.virtual_memory().percent)
            message += " Light:"
            if data.light > 999:
                message += "%2dk" % int(data.light/1000)
            else:
                message += "%3d" % data.light
            message += " Brightness:%3d%%" % data.matrix.brightness

            data.io_client.send(data.config.adafruitIO_feed, message)
            
        except (requests.exceptions.RequestException, RequestError):
            pass
            # We don't care if this fails or why as we will
            # receive the email notification after one hour
            # First exception above captures Connection error timeouts
            # and second exception captures a bad API key
            
        except Exception as err:
            # Catch anything else here
            data.master_error_count += 1
            logging.error(f'Total error count: {data.master_error_count}.\n'
                f'                     An unhandled exception occurred. {type(err).__name__}: {err}')

    # Fire this main loop again in 60 seconds
    data.timer_main = threading.Timer(60, main_loop, [data])
    data.timer_main.start()


def run():

    # Set up logging to write to both a file and to the console
    logFormatter = logging.Formatter('%(asctime)s %(levelname)s Line:%(lineno)4d %(message)s', datefmt='%Y-%m-%d, %H:%M:%S')
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)

    fileHandler = logging.FileHandler("logfile.log", "w")
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    logging.info('Executing temperature display')
    # Get command line arguments, if any
    commandArgs = args()

    # Initialize matrix option with defaults and override with any command line arguments
    matrixOptions = led_matrix_options(commandArgs)

    # Initialize the matrix
    matrix = RGBMatrix(options=matrixOptions)

    # Get the configuration values
    config = Config()

    # initialize our global data variables
    data = Data(config, matrix)
    
    # testing
    # set up keyboard listener for stats and testing purposes
    listener = keyboard.Listener(functools.partial(on_key_press, data))
    listener.start()

    try:
        main_loop(data)

        while True:
            pass

    except KeyboardInterrupt:

        # Kill any timers that were running
        if data.timer_main:
            data.timer_main.cancel()
        if data.timer_blink:
            data.timer_blink.cancel()
        if data.timer_show_UV:
            data.timer_show_UV.cancel()
            
        logging.info('Exiting temperature display')
        raise KeyboardInterrupt


if __name__ == "__main__":
    try:
        run()

    except KeyboardInterrupt:
        sys.exit(0)
