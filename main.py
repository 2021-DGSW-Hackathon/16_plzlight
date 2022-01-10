import threading
import spidev
import time
import RPi.GPIO as GPIO
import Adafruit_DHT
import I2C_LCD_driver
from flask import Flask, request, render_template

app = Flask(__name__)

GPIO.setmode(GPIO.BCM)# GPIO 이름은 BCM 명칭 사용

bus = 0
device = 0
inputValue = 0
oncount = 0
offcount = 0
oncount2 = 0
offcount2 = 0
humidity = 0
temperature = 0

mylcd = I2C_LCD_driver.lcd()

dhtDevice = Adafruit_DHT.DHT11
DHT_PIN = 4
servo_pin = 19
led_pin = 18

spi = spidev.SpiDev()
spi.open(bus,device)
spi.max_speed_hz = 1000000

checksun = False
check = False
playercheck = False

GPIO.setup(led_pin,GPIO.OUT)
GPIO.setup(servo_pin,GPIO.OUT)

pwm2 = GPIO.PWM(servo_pin,50)
pwm2.start(0)

def analogRead(channel):
    buf = [(1<<2)|(1<<1)|(channel&4) >> 2,(channel&3)<<6,0]
    buf = spi.xfer3(buf)
    adcValue = ((buf[1] & 0xF)<<8 | buf[2])
    
    return adcValue

def t1():
    while True:
        global checksun
        inputValue = analogRead(0)/1000
        if inputValue > 4:
            checksun = True
        else:
            checksun = False
        time.sleep(2)

def t2():
    global playercheck
    global checksun
    while True:
        if playercheck == False:
            time.sleep(1)
            if checksun == True:
                GPIO.output(led_pin,False)
            else:
                GPIO.output(led_pin,True)
        else:
            pass

def t3():
    global playercheck
    global checksun
    while True:
        if playercheck == False:
            time.sleep(1)
            if checksun == True:
                pwm2.ChangeDutyCycle(7.5) # 0.6ms 0도
            else:
                pwm2.ChangeDutyCycle(3.0) #90도
        else:
            pass

def t4():
    global temperature
    global humidity
    while True:
        humidity, temperature = Adafruit_DHT.read(dhtDevice,DHT_PIN)
        Tstring = f"T = {str(temperature)}C"
        Hstring = f"H = {str(humidity)}%"
        mylcd.lcd_display_string(Tstring, 1)
        mylcd.lcd_display_string(Hstring, 2)
        time.sleep(3)
        mylcd.lcd_clear()

th1 = threading.Thread(target=t1)
th2 = threading.Thread(target=t2)
th3 = threading.Thread(target=t3)
th4 = threading.Thread(target=t4)
th1.start()
th2.start()
th3.start()
th4.start()

@app.route("/")
def home():
    global oncount
    global offcount
    global offcount2
    global playercheck
    try:
        print('호출')
        turn = request.args.get('turn','turnoff')
        print('턴 = ',turn)
        if turn == 'trunon':
            print('라이트 on')
            oncount = oncount + 1
            GPIO.output(led_pin,True)
        elif turn == 'turnoff':
            oncount = 0
            print('라이트 off')
            playercheck = True
            GPIO.output(led_pin,False)
            offcount = offcount + 1
        else:
            offcount = 0
            print('라이트 on')
            GPIO.output(led_pin,True)
            playercheck = True
            oncount = oncount + 1

        if(oncount > 2 or offcount > 2):
            oncount = 0
            offcount = 0
            GPIO.output(led_pin,False)
            print('조도센서 사용')
            playercheck = False
            print(playercheck)
        else:
            print('yet')


    except Exception as ex:
        print(ex)
    return render_template("model.html")

@app.route("/tt")
def tt():
    global oncount2
    global offcount2
    global playercheck
    turns = request.args.get("mycuton",'cutoff')
    print('mycuton ==',turns)
    try:
        if turns == 'cuton':
            print('창문 on')
            oncount2 = oncount2 + 1
            pwm2.ChangeDutyCycle(7.5) #90도
        elif turns == 'cutoff':
            oncount2 = 0
            print('창문 off')
            playercheck = True
            pwm2.ChangeDutyCycle(3.0) # 0.6ms 0도
            print('offcount2 = ', offcount2)
            offcount2 = offcount2 + 1
        else:
            offcount2 = 0
            print('창문 on')
            playercheck = True
            pwm2.ChangeDutyCycle(3.0) # 0.6ms 0도
            oncount2 = oncount2 + 1
        if(oncount2 > 2 or offcount2 > 2):
                oncount2 = 0
                offcount2 = 0
                GPIO.output(led_pin,False)
                print('조도센서 사용')
                playercheck = False
                print(playercheck)
        else:
            print('yet')
    except Exception as ex:
        print(ex)
    return 'mydata'


@app.route("/finish")
def finish():
    th1.join()
    th2.join()
    th3.join()
    th4.join()

    GPIO.cleanup()

app.run(host="192.168.137.66",port=5000)