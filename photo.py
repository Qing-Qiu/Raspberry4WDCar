import RPi.GPIO as GPIO
import time
import argparse
import datetime
import cv2
import urllib.parse
import base64
import json
import urllib
import requests
import pyttsx3
import re

API_KEY = "#"
SECRET_KEY = "#"


def get_text():
    url = "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting?access_token=" + get_access_token()
    payload = 'image=' + get_file_content_as_base64("img.png", True)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def get_file_content_as_base64(path, urlencoded=False):
    """
    获取文件base64编码
    :param path: 文件路径
    :param urlencoded: 是否对结果进行urlencoded
    :return: base64编码信息
    """
    with open(path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf8")
        if urlencoded:
            content = urllib.parse.quote_plus(content)
    return content


def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))


def take_photo():
    from pip._vendor import requests
    with open("img.png", 'wb') as f:
        f.write(requests.get("http://192.168.50.1:8080/?action=snapshot").content)
        # 图片存在当前路径下
        pos = "img.png"
        print("getImgSuccess!")


# 小车电机引脚定义
IN1 = 20
IN2 = 21
IN3 = 19
IN4 = 26
ENA = 16
ENB = 13

# 小车按键定义
key = 8
flag = False

# 灭火电机引脚设置
OutfirePin = 2

# 超声波引脚定义
EchoPin = 0
TrigPin = 1

# RGB三色灯引脚定义
LED_R = 22
LED_G = 27
LED_B = 24

# 循迹红外引脚定义
TrackSensorLeftPin1 = 3  # 定义左边第一个循迹红外传感器引脚为3口
TrackSensorLeftPin2 = 5  # 定义左边第二个循迹红外传感器引脚为5口
TrackSensorRightPin1 = 4  # 定义右边第一个循迹红外传感器引脚为4口
TrackSensorRightPin2 = 18  # 定义右边第二个循迹红外传感器引脚为18口

# 舵机引脚定义
ServoPin = 23

# 蜂鸣器引脚定义
buzzer = 8

# 红外避障引脚定义
AvoidSensorLeft = 12
AvoidSensorRight = 17

# 设置GPIO口为BCM编码方式
GPIO.setmode(GPIO.BCM)

# 忽略警告信息
GPIO.setwarnings(False)


# 电机引脚初始化为输出模式
# 按键引脚初始化为输入模式
# 超声波,RGB三色灯,舵机引脚初始化
# 红外避障引脚初始化
# 引脚初始化函数
def init():
    global pwm_ENA
    global pwm_ENB
    global pwm_servo
    GPIO.setup(ENA, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN1, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN2, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ENB, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN3, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN4, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(key, GPIO.IN)
    GPIO.setup(TrackSensorLeftPin1, GPIO.IN)
    GPIO.setup(TrackSensorLeftPin2, GPIO.IN)
    GPIO.setup(TrackSensorRightPin1, GPIO.IN)
    GPIO.setup(TrackSensorRightPin2, GPIO.IN)
    GPIO.setup(EchoPin, GPIO.IN)
    GPIO.setup(TrigPin, GPIO.OUT)
    GPIO.setup(LED_R, GPIO.OUT)
    GPIO.setup(LED_G, GPIO.OUT)
    GPIO.setup(LED_B, GPIO.OUT)
    GPIO.setup(ServoPin, GPIO.OUT)
    GPIO.setup(buzzer, GPIO.OUT)
    GPIO.setup(OutfirePin, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(AvoidSensorLeft, GPIO.IN)
    GPIO.setup(AvoidSensorRight, GPIO.IN)
    # 设置pwm引脚和频率为2000hz
    pwm_ENA = GPIO.PWM(ENA, 2000)
    pwm_ENB = GPIO.PWM(ENB, 2000)
    pwm_ENA.start(0)
    pwm_ENB.start(0)
    # 设置舵机的频率和起始占空比
    pwm_servo = GPIO.PWM(ServoPin, 50)
    pwm_servo.start(0)


# 蜂鸣器函数
def whistle():
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(buzzer, GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(buzzer, GPIO.HIGH)
    time.sleep(0.1)


# 小车前进
def run(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)


# 小车后退
def back(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)


# 小车左转
def left(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)


# 小车右转
def right(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)


# 小车原地左转
def spin_left(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.HIGH)
    GPIO.output(IN3, GPIO.HIGH)
    GPIO.output(IN4, GPIO.LOW)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)


# 小车原地右转
def spin_right(leftspeed, rightspeed):
    GPIO.output(IN1, GPIO.HIGH)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.HIGH)
    pwm_ENA.ChangeDutyCycle(leftspeed)
    pwm_ENB.ChangeDutyCycle(rightspeed)


# 小车停止
def brake():
    GPIO.output(IN1, GPIO.LOW)
    GPIO.output(IN2, GPIO.LOW)
    GPIO.output(IN3, GPIO.LOW)
    GPIO.output(IN4, GPIO.LOW)


# 按键检测
def key_scan():
    while GPIO.input(key):
        pass
    while not GPIO.input(key):
        time.sleep(0.01)
        if not GPIO.input(key):
            time.sleep(0.01)
            while not GPIO.input(key):
                pass


def Distance():
    GPIO.output(TrigPin, GPIO.LOW)
    time.sleep(0.000002)
    GPIO.output(TrigPin, GPIO.HIGH)
    time.sleep(0.000015)
    GPIO.output(TrigPin, GPIO.LOW)

    t3 = time.time()

    while not GPIO.input(EchoPin):
        t4 = time.time()
        if (t4 - t3) > 0.03:
            return -1

    t1 = time.time()
    while GPIO.input(EchoPin):
        t5 = time.time()
        if (t5 - t1) > 0.03:
            return -1

    t2 = time.time()
    time.sleep(0.01)
    #    print "distance is %d " % (((t2 - t1)* 340 / 2) * 100)
    return ((t2 - t1) * 340 / 2) * 100


# 超声波函数
def Distance_test():
    num = 0
    ultrasonic = []
    while num < 5:
        distance = Distance()
        while int(distance) == -1:
            distance = Distance()
            print("Tdistance is %f" % (distance))
        while (int(distance) >= 500 or int(distance) == 0):
            distance = Distance()
            print("Edistance is %f" % (distance))
        ultrasonic.append(distance)
        num = num + 1
        time.sleep(0.01)
    print(ultrasonic)
    distance = (ultrasonic[1] + ultrasonic[2] + ultrasonic[3]) / 3
    print("distance is %f" % (distance))
    return distance


# 避障函数
def avoid():
    GPIO.output(LED_R, GPIO.HIGH)
    GPIO.output(LED_G, GPIO.LOW)
    GPIO.output(LED_B, GPIO.HIGH)
    spin_left(20, 20)
    time.sleep(0.5)
    run(20, 20)
    time.sleep(1)
    spin_right(20, 20)
    time.sleep(0.5)
    run(20, 20)
    time.sleep(1.2)
    spin_right(20, 20)
    time.sleep(0.54)
    run(20, 20)
    time.sleep(0.6)
    spin_left(20, 20)
    time.sleep(0.65)


def backPark():
    # 启动倒车入库
    brake()
    time.sleep(0.5)
    back(15, 15)
    time.sleep(0.5)
    back(40, 0)
    time.sleep(0.7)
    back(15, 15)
    time.sleep(0.5)


# try/except语句用来检测try语句块中的错误，
# 从而让except语句捕获异常信息并处理。
try:
    init()
    key_scan()
    # 检测第几次到达黑线

    while True:
        distance = Distance_test()
        # 如果超声波距离大于20，采用循迹
        if distance > 25:
            TrackSensorLeftValue1 = GPIO.input(TrackSensorLeftPin1)
            TrackSensorLeftValue2 = GPIO.input(TrackSensorLeftPin2)
            TrackSensorRightValue1 = GPIO.input(TrackSensorRightPin1)
            TrackSensorRightValue2 = GPIO.input(TrackSensorRightPin2)

            # 超车模块的检测
            LeftSensorValue = GPIO.input(AvoidSensorLeft)
            RightSensorValue = GPIO.input(AvoidSensorRight)
            # 四路循迹引脚电平状态
            # 0 0 X 0
            # 1 0 X 0
            # 0 1 X 0
            # 以上6种电平状态时小车原地右转
            # 处理右锐角和右直角的转动
            if TrackSensorLeftValue1 == False and TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False and TrackSensorRightValue2 == False:
                brake()
                break
            elif (TrackSensorLeftValue1 == False or TrackSensorLeftValue2 == False) and TrackSensorRightValue2 == False:
                spin_right(10, 10)


            # 四路循迹引脚电平状态
            # 0 X 0 0
            # 0 X 0 1
            # 0 X 1 0
            # 处理左锐角和左直角的转动
            elif TrackSensorLeftValue1 == False and (
                    TrackSensorRightValue1 == False or TrackSensorRightValue2 == False):
                spin_left(10, 10)


            # 0 X X X
            # 最左边检测到
            elif TrackSensorLeftValue1 == False:
                spin_left(10, 10)

            # X X X 0
            # 最右边检测到
            elif TrackSensorRightValue2 == False:
                spin_right(10, 10)

            # 四路循迹引脚电平状态
            # X 0 1 X
            # 处理左小弯
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == True:
                left(0, 10)

            # 四路循迹引脚电平状态
            # X 1 0 X
            # 处理右小弯
            elif TrackSensorLeftValue2 == True and TrackSensorRightValue1 == False:
                right(10, 0)

            # 四路循迹引脚电平状态
            # X 0 0 X
            # 处理直线
            elif TrackSensorLeftValue2 == False and TrackSensorRightValue1 == False:
                run(10, 10)

            # 当为1 1 1 1时小车保持上一个小车运行状态

        else:
            brake()
            take_photo()
            engine = pyttsx3.init()  # 初始化语音引擎
            engine.setProperty('rate', 120)  # 设置语速
            engine.setProperty('voice', 'zh')
            # engine.setProperty('volume', 0.2)  # 设置音量
            voices = engine.getProperty('voices')
            # engine.setProperty('voice', voices[0].id)  # 设置第一个语音合成器
            text = get_text()
            data = json.loads(text)
            words = [result['words'] for result in data['words_result']]
            res = ""
            for word in words:
                res = res + word
            pattern = r'\d+'
            nums = re.findall(pattern, res)
            if len(nums) == 2:
                engine.say(nums[0] + "加" + nums[1] + "等于" + str(int(nums[0]) + int(nums[1])))
                engine.runAndWait()
            avoid()
            brake()

        # servo_color_carstate()
except KeyboardInterrupt:
    pass
# 小车停车
pwm_ENA.stop()
pwm_ENB.stop()
GPIO.cleanup()
