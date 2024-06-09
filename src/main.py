import time
import machine
import ENS160
import dht
import network
import settings
import urequests

# define an infinite error pattern we will call to if we need to
def error_pattern() -> None:
    while True:
        led.on()
        time.sleep(1)
        led.off()
        time.sleep(1)

        if wdt != None: # if the watchdog timer is active and started, feed it to prevent a reboot.
            wdt.feed()

# boot pattern
led = machine.Pin("LED", machine.Pin.OUT)
print("Playing LED boot pattern...")
led.on()
time.sleep(0.5)
led.off()
time.sleep(0.5)
led.on()
time.sleep(0.5)
led.off()
time.sleep(0.5)
led.on()
time.sleep(0.5)
led.off()
time.sleep(0.5)

# connect to wifi
print("Preparing for wifi connection...")
wifi_con_attempt:int = 0
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
while wlan.isconnected() == False:

    wifi_con_attempt = wifi_con_attempt + 1

    # blip light
    led.on()
    time.sleep(0.1)
    led.off()
    
    print("Attempt #" + str(wifi_con_attempt) + " to connect to wifi...")
    wlan.connect(settings.ssid, settings.password)
    time.sleep(3)
print("Connected to wifi after " + str(wifi_con_attempt) + " tries!")
my_ip:str = str(wlan.ifconfig()[0])
print("My IP Address: " + my_ip)

# set up DHT-22 sensor
print("Setting up DHT22...")
dht22 = dht.DHT22(machine.Pin(10, machine.Pin.IN))

# Set up ENS160 + AHT21
print("Setting up I2C...")
i2c = machine.I2C(0, scl=machine.Pin(17), sda=machine.Pin(16))
print("I2C devices: " + str(i2c.scan()))
if len(i2c.scan()) == 0:
    error_pattern()
print("Setting up ENS160...")
ens = ENS160.ENS160(i2c)

# turn on ENS160 (opearing mode)
print("Setting ENS160 operating mode to 2 (gas sensing)...")
ens.operating_mode = 2

# wait some time for the ENS160 to warm up
print("Allowing 10 seconds for warm up...")
time.sleep(10)

# start watchdog timer
wdt = machine.WDT(timeout=8388) # 8,388 ms is the limit (8.388 seconds)
wdt.feed()
print("Watchdog timer now activated.")

# inifinite loop
samples_uploaded:int = 0
while True:

    # before proceeding to sample + upload, confirm that we are still online
    wifi_con_attempt = 0
    while wlan.isconnected() == False:
        print("Ready to upload data but not connected!")
        wifi_con_attempt = wifi_con_attempt + 1

        # blip light
        led.on()
        time.sleep(0.1)
        led.off()
        
        print("Attempt #" + str(wifi_con_attempt) + " to connect to wifi...")
        wdt.feed()
        wlan.connect(settings.ssid, settings.password)
        wdt.feed()
        time.sleep(3)


    # start cycle
    print("Sampling cycle starting at " + str(time.ticks_ms()) + " ticks")
    led.on() # LED on during measurement + upload

    # create body we will post
    body = {}

    # measure temp + humidity via DHT22
    print("\tReading temperature and humidity from DHT-22...")
    dht22_attempts:int = 0
    humidity = None
    temperature_f = None
    while (humidity == None or temperature_f == None) and dht22_attempts < 10:
        try:
            wdt.feed()
            print("\t\tMeasuring from DHT-22 on attempt # " + str(dht22_attempts + 1) + "...")
            dht22.measure()
            humidity = dht22.humidity()
            temperature_c = dht22.temperature()
            temperature_f = (temperature_c * (9/5)) + 32
        except Exception as e:
            print("Reading attempt failed! Exception msg: " + str(e))
        dht22_attempts = dht22_attempts + 1
        time.sleep(0.25)

    # log if successful
    wdt.feed()
    if humidity == None or temperature_f == None:
        print("\tUnable to get humidity/temperature from DHT-22... maxiumum try count surpassed!")
    else:
        print("\tTemperature + Humidity successfully captured by DHT-22!")
        body["temperature"] = temperature_f
        body["humidity"] = humidity / 100 # as a percentage

    # measure from ENS160
    wdt.feed()
    ens160_attempts:int = 0
    AQI:int = 0
    TVOC:int = 0
    ECO2:int = 0
    while (AQI == 0 and TVOC == 0 and ECO2 == 0) and ens160_attempts < 10: # straight 0's in the readings means it doesnt work. Please note, it IS possible for TVOC to be 0. That is common in very air clean settings.
        try:
            wdt.feed()
            print("\tMeasuring air quality data from ENS160 attempt # " + str(ens160_attempts + 1) + "...")
            AQI:int = ens.AQI
            TVOC:int = ens.TVOC
            ECO2:int = ens.CO2
        except Exception as e:
            print("Reading attempt failed! Exception msg: " + str(e))
        ens160_attempts = ens160_attempts + 1
        time.sleep(0.25)

    # log if successful
    wdt.feed()
    if AQI == 0 and TVOC == 0 and ECO2 == 0:
        print("\tUnable to read valid air quality readings from ENS160. Surpassed max try attempt!")
    else:
        print("\tENS160 Air Quality Readings captured!")
        body["aqi"] = AQI
        body["tvoc"] = TVOC
        body["eco2"] = ECO2

    # print
    print("\tReadings: " + str(body))

    

    # upload
    if len(body) > 0: # the body has properties
        try:
            print("\tUploading to '" + settings.post_url + "'...")
            wdt.feed()
            pr = urequests.post(settings.post_url, json=body)
            wdt.feed()
            pr.close()

            # handle
            if str(pr.status_code)[0:1] != "2": # if the upload was not successful (not in the 200 range), go into infinite error loop. This indicates that the receiving input is no longer accepting. No point in continuing to collect and try an upload.
                error_pattern()
            else:
                samples_uploaded = samples_uploaded + 1
                print("\tUpload successful!")

        except Exception as e:
            print("\tUpload to endpoint '" + settings.post_url + "' failed! Exception msg: " + str(e))

    else:
        print("\tNothing to upload! Both the air quality and air temp/humidity readings were unsuccesful!")

    # wait 
    led.off() # led off while doing nothing (just waiting)
    next_loop:int = time.ticks_ms() + (1000 * settings.sample_time_seconds)
    while (time.ticks_ms() < next_loop):
        print("Sampling #" + str(samples_uploaded + 1) + " next in " + str(round((next_loop - time.ticks_ms()) / 1000, 0)) + " seconds...")
        time.sleep(1)
        wdt.feed()
