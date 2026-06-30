import adafruit_dht
import time
import board

dht_device = adafruit_dht.DHT11(board.D4)

print("start sensing")

temperature = 0
humidity = 0

while True:
	try:
		temperature = dht_device.temperature
		humidity = dht_device.humidity
		print(f"temperature: {temperature}")
		print(f"humidity: {humidity}")
		time.sleep(2.5)
	except RuntimeError as error:
		print(f"blah blkah")
		continue
