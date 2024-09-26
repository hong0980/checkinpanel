# -*- coding: utf-8 -*-
"""
cron: 30 15,19 * * *
new Env('chdbits 最新电影信息');
"""

import re
from utils import get_data
from notify_mtr import send
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium_stealth import stealth
from requests_html import HTMLSession

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, Movies_quantity, i):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        service = webdriver.ChromeService(executable_path='/usr/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=options)
        stealth(driver,
            platform="Win32",
            fix_hairline=True,
            vendor="Google Inc.",
            languages=["zh-CN", "zh"],
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
        )
        try:
            headers, url, s, circled_numbers = {"Cookie": cookie}, 'https://ptchdbits.co/torrents.php', HTMLSession(), \
            ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳']
            driver.get(url)
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})

            movie_info = f'<b> ⑵ 当前最新的 {Movies_quantity} 部信息：</b>\n'
            r = s.get(url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")

            if "欢迎回来" in r.text:
                Movieslist = soup.find_all('tr', class_='thirtypercentdown_bg')
                for i, tag in enumerate(Movieslist):
                    if i % 2 == 1:
                        tag['class'] = 'Modify_style'

                Movieslist = soup.find_all('tr', class_='thirtypercentdown_bg')
                for sequence, Moviesinfo in enumerate(Movieslist[:int(Movies_quantity)], start=1):
                    category = Moviesinfo.img.get('title')
                    Limited_time = Moviesinfo.find('span').text
                    upload_time = Moviesinfo.find('span')['title']
                    td_tags = Moviesinfo.find_all('td', class_='rowfollow')
                    data = [td.get_text(strip=True) for td in td_tags]
                    time, size, seeders, leechers, snatched = data[3:8]
                    imdb_img = Moviesinfo.find('img', src="pic/imdb.gif")
                    movie_name = Moviesinfo.find('a', title=True)['title']
                    imdb_rating = imdb_img.find_next_sibling(string=True).strip() if imdb_img else ''
                    chinese_name = ' '.join(Moviesinfo.find('font', class_='subtitle').stripped_strings)

                    movie_info += (f"<b>{circled_numbers[sequence - 1]}：</b>【{category}】"
                                   f"<b><span style='color:red'>{chinese_name}</span>"
                                   f"<span style='color:blue'> {movie_name}</span></b>\n"
                                   f"【文件大小】: {size}\n"
                                   f"【IMDb评分】: {imdb_rating}\n"
                                   f"【免流限时】: {Limited_time}\n"
                                   f"【发布时间】: {upload_time}\n"
                                   f"【存活时间】: {time}\n"
                                   f"【 种子数 】: {seeders}\n"
                                   f"【 下载数 】: {leechers}\n"
                                   f"【 完成数 】: {snatched}\n")

                pattern = (r'UltimateUser_Name.*?><b>(.*?)</b>.*?'
                           r'使用</a>]: (.*?)\s*'
                           r'<font.*?分享率：</font>\s*(.*?)\s*'
                           r'<font.*?上传量：</font>\s*(.*?)\s*'
                           r'<font.*?下载量：</font>\s*(.*?)\s*'
                           r'<font.*?当前做种.*?(\d+).*?<font.*?'
                           r'做种积分: </font>\s*(.*?)</')
                result = re.findall(pattern, r.text, re.DOTALL)[0]
                res = (f'<b> ⑴ {result[0]} 账户信息：</b>\n'
                       f'魔力值：{result[1]}\n分享率：{result[2]}\n'
                       f'上传量：{result[3]}\n下载量：{result[4]}\n'
                       f'当前做种：{result[5]}\n做种积分：{result[6]}\n'
                       f'\n{movie_info}')
            else:
                res = f'账号({i})无法登录！可能Cookie失效，请重新修改'
        finally:
            driver.quit()
        return res

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            Movies_quantity = check_item.get("Movies_quantity")
            msg_all += f'{self.sign(cookie, Movies_quantity, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = Get(check_items=get_data().get("CHDBITS", [])).main()
    send("chdbits 最新电影信息", result)
    # print(result)
