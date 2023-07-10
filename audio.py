import os
import base64
import urllib
import requests
import json
import RPi.GPIO as GPIO
import time
import urllib.request
import re
import pyttsx3
import pygame
from pygame.locals import *
import urllib.parse
from bs4 import BeautifulSoup

API_KEY = "#"
SECRET_KEY = "#"
# 小车电机引脚定义
IN1 = 20
IN2 = 21
IN3 = 19
IN4 = 26
ENA = 16
ENB = 13
# 小车按键定义
key = 8
# 设置RGB三色灯为BCM编码方式
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
# RGB三色灯引脚定义
LED_R = 22
LED_G = 27
LED_B = 24
# RGB三色灯设置为输出模式
GPIO.setup(LED_R, GPIO.OUT)
GPIO.setup(LED_G, GPIO.OUT)
GPIO.setup(LED_B, GPIO.OUT)


def get_text1():
    url = "https://vop.baidu.com/server_api"
    payload = json.dumps({
        "format": "wav",
        "rate": 16000,
        "channel": 1,
        "cuid": "XI7MPC6zVfkwWkHOJfR3dG5HJq11fhD4",
        "token": get_access_token(),
        "speech": get_file_content_as_base64("test.wav", False),
        "len": os.path.getsize("test.wav")
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def get_text2(tex):
    url = "https://tsn.baidu.com/text2audio"
    payload = 'tex=' + urllib.parse.quote(urllib.parse.quote(
        tex)) + '&tok=' + get_access_token() + '&cuid=#&ctp=1&lan=zh&spd=5&pit=5&vol=5&per=106&aue=3'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.content


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


def motor_init():
    global pwm_ENA
    global pwm_ENB
    global delaytime
    GPIO.setup(ENA, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN1, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN2, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(ENB, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(IN3, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(IN4, GPIO.OUT, initial=GPIO.LOW)
    # 设置pwm引脚和频率为2000hz
    pwm_ENA = GPIO.PWM(ENA, 2000)
    pwm_ENB = GPIO.PWM(ENB, 2000)
    pwm_ENA.start(0)
    pwm_ENB.start(0)
    GPIO.setup(key, GPIO.IN)


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


def key_scan():
    while GPIO.input(key):
        pass
    while not GPIO.input(key):
        time.sleep(0.01)
        if not GPIO.input(key):
            time.sleep(0.01)
            while not GPIO.input(key):
                pass


def voice(date, win, temp, weather):
    date = date.replace('（', '。')
    date = date.replace('）', '')
    # print(date + "。")
    # print('天气：' + weather + "。")
    pattern = r'\d+'
    temps = re.findall(pattern, temp)
    temp_len = len(temps)
    # if temp_len == 1:
    #     print('温度：' + temps[0] + "。")
    # else:
    #     print('最高温度：' + temps[0] + "℃。")
    #     print('最低温度：' + temps[1] + "℃。")
    win = win.replace('<', '小于')
    win = win.replace('>', '大于')
    # print('风级：' + win + "。")
    # print('\n')
    # engine.say(date + "。")
    # engine.say('天气：' + weather + "。")
    report = date + "。"
    report = report + '天气：' + weather + "。"
    if temp_len == 1:
        # engine.say('温度：' + temps[0] + "。")
        report = report + '温度：' + temps[0] + "。"
    else:
        # engine.say('最高温度：' + temps[0] + "℃。")
        report = report + '最高温度：' + temps[0] + "℃。"
        # engine.say('最低温度：' + temps[1] + "℃。")
        report = report + '最低温度：' + temps[1] + "℃。"
    # engine.say('风级：' + win + "。")
    # engine.runAndWait()
    report = report + '风级：' + win + "。"
    print(report)
    return report


def parse_weather_infor(url):
    headers = ("User-Agent",
               "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/61.0.3163.100 Safari/537.36")
    opener = urllib.request.build_opener()
    opener.addheaders = [headers]
    resp = opener.open(url).read()
    soup = BeautifulSoup(resp, 'html.parser')
    tagDate = soup.find('ul', class_="t clearfix")
    tgs = soup.findAll('h1', tagDate)
    dates = tgs[0:3]
    tagAllTem = soup.findAll('p', class_="tem")
    tagAllWea = soup.findAll('p', class_="wea")
    tagAllWin = soup.findAll('p', class_="win")
    location = soup.find('div', class_='crumbs fl')
    text = location.getText()
    report = '以下播报' + str(text.split(">")[2]) + '未来3天天气情况。'
    # engine.say('以下播报' + str(text.split(">")[2]) + '未来3天天气情况。')
    # engine.runAndWait()
    for k in range(len(dates)):
        report = report + voice(dates[k].getText(), tagAllWin[k].i.string, tagAllTem[k].getText(), tagAllWea[k].string)
    # engine.say('天气播报完毕。')
    # engine.runAndWait()
    report = report + '天气播报完毕。'
    text = get_text2(report)
    with open('weather.mp3', 'wb') as file:
        file.write(text)
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((640, 0))
    pygame.display.set_caption("Media Player")
    pygame.mixer.music.load("weather.mp3")
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_SPACE:
                    pygame.mixer.music.stop()
    pygame.mixer.music.stop()
    pygame.mixer.quit()
    pygame.quit()


engine = pyttsx3.init()
engine.setProperty('rate', 120)  # 设置语速
engine.setProperty('voice', 'zh')
# engine.setProperty('volume', 0.2)  # 设置音量
voices = engine.getProperty('voices')
# engine.setProperty('voice', voices[0].id)  # 设置第一个语音合成器
motor_init()

while True:
    key_scan()
    os.system('arecord -D "plughw:1,0" -f dat -c 1 -r 16000 -d 5 test.wav')
    text = get_text1()
    data = json.loads(text)
    words = data['result']
    content = ""
    for word in words:
        content = content + word
    if "天气" in content:
        engine.say("好的")
        engine.runAndWait()
        parse_weather_infor("http://www.weather.com.cn/weather/101210101.shtml")
    elif "转圈" in content:
        spin_left(10, 10)
        time.sleep(10)
        spin_right(10, 10)
        time.sleep(10)
        brake()
    elif "音乐" in content or "歌" in content:
        pygame.init()
        pygame.mixer.init()
        screen = pygame.display.set_mode((640, 0))
        pygame.display.set_caption("Media Player")
        pygame.mixer.music.load("song.mp3")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key == K_SPACE:
                        pygame.mixer.music.stop()
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        pygame.quit()
    elif "亮灯" in content or "发光" in content:
        engine.say("好的")
        engine.runAndWait()
        try:
            GPIO.output(LED_R, GPIO.HIGH)
            GPIO.output(LED_G, GPIO.LOW)
            GPIO.output(LED_B, GPIO.LOW)
            time.sleep(1)
            GPIO.output(LED_R, GPIO.LOW)
            GPIO.output(LED_G, GPIO.HIGH)
            GPIO.output(LED_B, GPIO.LOW)
            time.sleep(1)
            GPIO.output(LED_R, GPIO.LOW)
            GPIO.output(LED_G, GPIO.LOW)
            GPIO.output(LED_B, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(LED_R, GPIO.HIGH)
            GPIO.output(LED_G, GPIO.HIGH)
            GPIO.output(LED_B, GPIO.LOW)
            time.sleep(1)
            GPIO.output(LED_R, GPIO.HIGH)
            GPIO.output(LED_G, GPIO.LOW)
            GPIO.output(LED_B, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(LED_R, GPIO.LOW)
            GPIO.output(LED_G, GPIO.HIGH)
            GPIO.output(LED_B, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(LED_R, GPIO.LOW)
            GPIO.output(LED_G, GPIO.LOW)
            GPIO.output(LED_B, GPIO.LOW)
            time.sleep(1)
        except:
            print("except")
            # 使用try except语句，当CTRL+C结束进程时会触发异常后
            # 会执行gpio.cleanup()语句清除GPIO管脚的状态
            GPIO.cleanup()
    else:
        engine.say("我不知道你在说什么")
        engine.runAndWait()
