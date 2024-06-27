# -*- coding: utf-8 -*-
"""
cron: 40 7 * * *
new Env('每日新闻');
"""

import re
import traceback
import requests
from notify_mtr import send
from utils import get_data

class News:
    @staticmethod
    def parse_data(data, topic):
        if not data.get(topic):
            return ""
        msg = ""
        for key, value in data.get(topic).items():
            if key == "content":
                msg += "\n".join(str(i) for i in value)
                msg += "\n"
            elif value and type(value) is not bool and not bool(re.search("[a-z]", str(value))):
                msg += str(value) + "\n"
        return msg

    def process_weather_data(self, weather_data):
        msg = ''
        if weather_data['city'] != "未知":
            weather_detail = weather_data['detail']
            msg += (
                f"\n🚩 {weather_detail['date']} {weather_data['city']}天气：🚩\n"
                f"白天天气：{weather_detail['text_day']}\n"
                f"晚间天气：{weather_detail['text_night']}\n"
                f"最高温度：{weather_detail['high']}°C\n"
                f"最低温度：{weather_detail['low']}°C\n"
                f"降雨量：{weather_detail['rainfall']}mm\n"
                f"降水概率：{weather_detail['precip']}%\n"
                f"风向：{weather_detail['wind_direction']}\n"
                f"风向角度：{weather_detail['wind_direction_degree']}°\n"
                f"风速：{weather_detail['wind_speed']}km/h\n"
                f"风力等级：{weather_detail['wind_scale']}级\n"
                f"湿度：{weather_detail['humidity']}%\n\n"
            )
        return msg

    def process_calendar_data(self, calendar_data):
        term_info = ""
        if calendar_data['isTerm']:
            term_info = f"节气：{calendar_data['term']}\n"
        msg = (
            f"公历日期：{calendar_data['cYear']}年{calendar_data['cMonth']}月{calendar_data['cDay']}日  {calendar_data['ncWeek']}\n"
            f"农历日期：{calendar_data['yearCn']}({calendar_data['animal']}年) {calendar_data['monthCn']}{calendar_data['dayCn']}\n"
            f"干支年：{calendar_data['gzYear']}年\n"
            f"干支月：{calendar_data['gzMonth']}月\n"
            f"干支日：{calendar_data['gzDay']}日\n"
            f"{term_info}\n"
        )
        return msg

    def main(self):
        msg = ""
        try:
            res = requests.get("https://news.topurl.cn/api").json()
            if res.get("code") == 200:
                data = res.get("data")
                if data.get("weather"):
                    weather_data = data['weather']
                    msg += self.process_weather_data(weather_data)
                if data.get("calendar"):
                    msg += "📅 日历 📅\n" + self.process_calendar_data(data["calendar"])
                if data.get("newsList"):
                    msg += "📮 每日新闻 📮\n"
                    for no, news_ in enumerate(data.get("newsList"), start=1):
                        msg += f'{str(no).zfill(2)}. <a href="{news_.get("url")}">{news_.get("title")}</a>\n'
                if data.get("historyList"):
                    msg += "\n🎬 历史上的今天 🎬\n"
                    for history in data.get("historyList"):
                        msg += f'{history.get("event", "")}\n'
                msg += "\n🧩 天天成语 🧩\n" + self.parse_data(data, "phrase")
                msg += "\n🎻 慧语香风 🎻\n" + self.parse_data(data, "sentence")
                msg += "\n🎑 诗歌天地 🎑\n" + self.parse_data(data, "poem")
        except Exception:
            msg += f"每日新闻: 异常 {traceback.format_exc()}"
        return msg


if __name__ == "__main__":
    _data = get_data()
    news = _data.get("NEWS")
    if news:
        result = News().main()
        send("每日新闻", result)
        # print(result)
