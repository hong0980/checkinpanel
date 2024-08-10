# -*- coding: utf-8 -*-
"""
cron: 33 15,19 * * *
new Env('hdsky 最新电影信息');
"""

import re
from utils import get_data
from notify_mtr import send
from bs4 import BeautifulSoup
from requests_html import HTMLSession

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    def sign(self, cookie, Movies_quantity):
        res = ""
        session = HTMLSession()
        try:
            url = 'https://hdsky.me/'
            r = session.get(url + 'torrents.php', headers={"Cookie": cookie}, timeout=10)
            if "欢迎回来" in r.text:
                movie_info = f'<b>（2）当前最新的{Movies_quantity}部信息：</b>\n'
                soup = BeautifulSoup(r.text, "html.parser")
                user_name = soup.find('a', class_='InsaneUser_Name').find('b').text
                Movieslist = soup.find_all('tr', class_='stickbg progresstr')
                for i, info in enumerate(Movieslist[:int(Movies_quantity)], start=1):
                    for element in info.find_all('td', class_='embedded'):
                        spans = element.find_all('span')
                        if spans:
                            chinese_name = spans[-1].text
                            if re.search(r'\d*时\d+分', chinese_name):
                                chinese_name = spans[-2].text
                                remaining = ' '.join([span.text for span in spans[1:-2]])
                            else:
                                remaining = ' '.join([span.text for span in spans[1:-1]])

                    imdb_element = info.find('img', src="/pic/icon-imdb.png")
                    douban_element = info.find('img', src="/pic/icon-douban.png")
                    imdb_rating = imdb_element.find_next_sibling(string=True).strip() if imdb_element else ''
                    douban_rating = douban_element.find_next_sibling(string=True).strip() if douban_element else ''

                    douban_msg = ''
                    if douban_rating:
                        movie_link = info.find('a', title=True)['href']
                        d = session.get(url + movie_link, headers={"Cookie": cookie}, timeout=10)
                        douban_soup = BeautifulSoup(d.text, 'html.parser')
                        if '<td class="rowhead">豆瓣' in d.text:
                            for element in douban_soup.find_all('dl', id='dbdl'):
                                for dt in element.find_all('dt'):
                                    key = dt.get_text(strip=True)
                                    dd = dt.find_next_sibling('dd')
                                    value = dd.get_text(strip=True) if dd else ''
                                    douban_msg = ('<b>豆瓣信息：</b>\n'
                                                 f"【<span style='color: #FE830F'>  {key}  </span>】：{value}\n")

                    category = info.img.get('title')
                    name = info.find('a', title=True)['title']
                    upload_time = info.find_all('td', class_='rowfollow nowrap')[1].find('span')['title']

                    td_tags = info.find_all('td', class_='rowfollow')
                    data = [td.get_text(strip=True) for td in td_tags]
                    if len(data) >= 8:
                        time, size, seeders, leechers, snatched = data[3:8]
                        movie_info += (f"<b>{i}):</b>\n"
                                       f"【<span style='color: magenta'>{category}</span>】："
                                       f"<b>(<span style='color: green'>{remaining}</span>) "
                                       f"<span style='color: red'>{chinese_name}</span> "
                                       f"<span style='color: blue'>{name}</span></b>\n"
                                       f"【<span style='color: magenta'>文件大小</span>】: {size}\n"
                                       f"【<span style='color: magenta'>发布时间</span>】: {upload_time}\n"
                                       f"【<span style='color: magenta'>豆瓣评分</span>】: {douban_rating}\n"
                                       f"【<span style='color: magenta'>IMDb评分</span>】: {imdb_rating}\n"
                                       f"【<span style='color: magenta'>存活时间</span>】: {time}\n"
                                       f"【 <span style='color: magenta'>种子数</span> 】: {seeders}\n"
                                       f"【 <span style='color: magenta'>下载数</span> 】: {leechers}\n"
                                       f"【 <span style='color: magenta'>完成数</span> 】: {snatched}\n"
                                       f"{douban_msg}")

                bonus = re.findall(r"使用.*?:(.*)\s*<font", r.text)[0].strip()
                ratio = re.findall(r"分享率.*?> (.*).*?<f", r.text)[0].strip()
                uploaded = re.findall(r"上传量.*?> (.*).*?<f", r.text)[0].strip()
                downloaded = re.findall(r"下载量.*?> (.*).*?<f", r.text)[0].strip()
                active = re.findall(r"trans.gif\"/>(\d+).*?arrowdown", r.text)[0].strip()
                res += (f"<b>（1）账户信息：</b>\n"
                        f"用户名：{user_name}\n"
                        f"魔力值：{bonus}\n"
                        f"分享率：{ratio}\n"
                        f"上传量：{uploaded}\n"
                        f"下载量：{downloaded}\n"
                        f"当前做种：{active}\n"
                        f"{movie_info}")
            else:
                res = "登录失败，请检查Cookie或网络连接。"

        except Exception as e:
            res = f"出现错误: {e}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            quantity = check_item.get("Movies_quantity")
            sign_msg = self.sign(cookie, quantity)
            msg = f"{sign_msg}"
            msg_all += msg + "\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("HDSKY", [])
    result = Get(check_items=_check_items).main()
    send("hdsky 最新电影信息", result)
    # print(result)
