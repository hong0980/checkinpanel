# -*- coding: utf-8 -*-
"""
cron: 35 7 * * *
new Env('天气预报');
"""

import json
import requests
from os.path import dirname, join
from bs4 import BeautifulSoup
from utils import get_data
from notify_mtr import send

class Weather:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def city_map():
        cur_dir = dirname(__file__)
        with open(join(cur_dir, "city.json"), "r", encoding="utf-8") as city_file:
            city_map = json.load(city_file)
            if not city_map:
                raise FileNotFoundError
        return city_map

    def main(self):
        msg = ""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/92.0.4515.131 Safari/537.36",
        }
        url = "https://wannianli.tianqi.com/laohuangli/"
        p = requests.get(url, headers=headers)
        if p.status_code == 200:
            hlsoup = BeautifulSoup(p.content, 'html.parser')
            kalendar_date = hlsoup.find('div', class_='kalendar_top').find('h3').text.strip()
            kalendar_date1 = hlsoup.find('div', class_='kalendar_top').find('h5').text.strip()

            for city in self.check_items:
                code = self.city_map().get(city)
                url = f"http://i.tianqi.com/?c=code&id=27&py={code}"
                r = requests.get(url, headers=headers)
                soup = BeautifulSoup(r.content, 'html.parser')
                boxes = soup.find_all('div', class_='box')

                for box in boxes:
                    summary = ""
                    icon_url = f"<img src='{box.img['src']}' />"
                    name = box.find('a').text.strip()
                    temp = box.find('strong').text
                    humidity = box.find_all('span')[1].text
                    details = "\n".join([li.text for li in box.select('div.today_data_r01 li')][:6])
                    description = box.find('li', class_='wtwt').text.strip()
                    path = box.find('li', class_='wtpath').text.strip()
                    wind = box.find('li', class_='wtwind').text.strip()
                    future_weather_info = box.find_all('ul', class_='wltq')
                    living_index = box.find_all('ul', class_='wltq3')

                    for future_weather in future_weather_info:
                        day = future_weather.find('a').text.strip()
                        temperature = future_weather.find('li', class_='t2').text.strip()
                        description_tag = future_weather.find('li', class_='t4')
                        weather_description = description_tag.find_all('p')[0].text.strip()
                        future_wind = description_tag.find_all('p')[1].text.strip()
                        future_icon_url = f"<img src='{future_weather.img['src']}' />"
                        summary += f"{day} {temperature} {future_wind} {weather_description} {future_icon_url}\n"

                    msg += (f"<b><span style='color: red'>{name} </span></b>今天\n"
                            f"{kalendar_date}\n{kalendar_date1}\n{path}{icon_url} {description} {wind}")
                    msg += f"\n当前温度：{temp}\n{humidity}\n{details}\n\n{summary}"
                msg += "\n"
        else:
            msg += f"请求失败\n"

        return msg

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("CITY", [])
    result = Weather(check_items=_check_items).main()
    send("天气预报", result)
    # print(result)
