import adafruit_dht
import board
import time
import RPi.GPIO as GPIO

#センサータイプとピン番号を指定
dht_device = adafruit_dht.DHT11(board.D3)

#set LED pin
pin_out_green = 18
pin_out_red = 12
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_out_green, GPIO.OUT)
GPIO.setup(pin_out_red, GPIO.OUT)

print("センサーの監視を開始します...")
print("※終了するにはCtrl + Cを押してください。")

temperature = 0
humidity = 0

hot_temp = 26
cold_temp = 22

while True:
    try:

        if temperature is not None and humidity is not None:
            temperature = dht_device.temperature
            humidity = dht_device.humidity

            print(f"温度：{temperature:.1f}℃　湿度：{humidity:.1f}%")
            
            Msnal = temperature - (temperature - 10) * (0.8 - humidity / 100) / 2.3
            
            print(f"体感温度:{Msnal:.1f}℃")

        if Msnal >= hot_temp:
            GPIO.output(pin_out_green, GPIO.HIGH)
        elif Msnal <= cold_temp:
            GPIO.output(pin_out_red, GPIO.HIGH)
        else:
            GPIO.output(pin_out_green, GPIO.LOW)
            GPIO.output(pin_out_red, GPIO.LOW)
        
            print(f"温度は丁度いい。エアコンをつける必要がない。")
        
        
        
            
            
    except RuntimeError as error:
        #読み取り失敗エラーをキャッチして無視し、処理を続行
        print(f"読み取りエラー：{error.args[0]}")
        continue

    except Exception as error:
        #プログラムを強制終了するような深刻なエラーが起きた場合はセンサを開放
        dht_device.exit()
        raise error

    time.sleep(2.5)

