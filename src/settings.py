# I2C settings (for the ENS160)
i2c_bus:int = 1
i2c_sda:int = 16
i2c_scl:int = 17

# DHT-22 settings
dht22_gpio:int = 10

# Wifi login
ssid = ""
password = ""

# sample time (how many seconds should elapse in between sampling and uploading)
sample_time_seconds:int = 60

# What URL to make an HTTP POST request to with the sampled data
post_url:str = ""