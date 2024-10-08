# -*- coding: utf-8 -*-
"""
cron: 30 15,19 * * *
new Env('chdbits 最新电影信息');
"""

import re, time
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
            url, s, circled_numbers = 'https://ptchdbits.co/torrents.php', HTMLSession(), \
            ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩', '⑪', '⑫', '⑬', '⑭', '⑮', '⑯', '⑰', '⑱', '⑲', '⑳']
            headers = {'referer': url, 'authority': 'ptchdbits.co',
                       'Cookie': cookie, 'origin': 'https://ptchdbits.co'}

            driver.get(url)
            for single_cookie in cookie.split('; '):
                name, value = single_cookie.split('=', 1)
                driver.add_cookie({'name': name, 'value': value})
            driver.get(url)

            movie_info = f'<b> ⑵ 当前最新的 {Movies_quantity} 部信息：</b>\n'
            r = s.get(url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")

            if "欢迎回来" in r.text:
                Movieslist = soup.select('tr.thirtypercentdown_bg')
                for i, tag in enumerate(Movieslist):
                    if i % 2 == 1:
                        tag['class'] = 'Modify_style'

                Movieslist = soup.select('tr.thirtypercentdown_bg')
                for sequence, Moviesinfo in enumerate(Movieslist[:int(Movies_quantity)], start=1):
                    category = Moviesinfo.img.get('title')
                    Limited_time = Moviesinfo.select_one('span').text
                    upload_time = Moviesinfo.select_one('span')['title']
                    td_tags = Moviesinfo.select('td.rowfollow')
                    data = [td.get_text(strip=True) for td in td_tags]
                    time, size, seeders, leechers, snatched = data[3:8]
                    movie_name = Moviesinfo.select_one('a[title]')['title']
                    imdb_img = Moviesinfo.select_one('img[src="pic/imdb.gif"]')
                    imdb_rating = imdb_img.find_next_sibling(string=True).strip() if imdb_img else ''
                    chinese_name = ' '.join(Moviesinfo.find('font', class_='subtitle').stripped_strings)

                    movie_link = Moviesinfo.select('td.embedded a')[2]['href']
                    d = s.get('https://ptchdbits.co/' + movie_link, headers=headers)
                    movie = BeautifulSoup(d.text, "html.parser")
                    content = movie.select_one('div#kdescr')
                    for tag in content.select('fieldset, div.codetop, div.codemain, span'):
                        tag.decompose()
                    lines = content.get_text(separator='\n', strip=False).splitlines()
                    processed_lines = []
                    url_pattern = re.compile(r'https://((?:movie\.)?douban\.com|www\.imdb\.com)')
                    for i in range(len(lines)):
                        line = lines[i].strip()
                        if '链接' in line and i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if url_pattern.match(next_line):
                                processed_lines.append(f'<a href="{next_line}">{line}</a>')
                                continue
                        if line and not line.startswith('https://'):
                            processed_lines.append(lines[i].strip())
                    cleaned_content = "\n".join(processed_lines)

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
                                   f"【 完成数 】: {snatched}\n"
                                   f"详细信息\n{cleaned_content}\n\n")

                pattern = (r'UltimateUser_Name.*?><b>(.*?)</b>.*?'
                           r'使用</a>]: (.*?)\s*'
                           r'<.*?分享率：</font>\s*(.*?)\s*'
                           r'<.*?上传量：</font>\s*(.*?)\s*'
                           r'<.*?下载量：</font>\s*(.*?)\s*'
                           r'<.*?当前做种.*?(\d+).*?'
                           r'<.*?做种积分: </font>\s*(.*?)</')
                result = re.findall(pattern, r.text, re.DOTALL)[0]
                return (f'<b> ⑴ {result[0]} 账户信息：</b>\n'
                        f'魔力值：{result[1]}\n分享率：{result[2]}\n'
                        f'上传量：{result[3]}\n下载量：{result[4]}\n'
                        f'当前做种：{result[5]}\n做种积分：{result[6]}\n\n'
                        f'{movie_info}')
            else:
                return f'账号({i})无法登录！可能Cookie失效，请重新修改'
        finally:
            driver.quit()

    def main(self):
        msg_all = ''
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            Movies_quantity = check_item.get("Movies_quantity")
            msg_all += f'{self.sign(cookie, Movies_quantity, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = Get(check_items=get_data().get("CHDBITS", [])).main()
    if not 'Cookie失效' in result:
        chunk_size = 4
        paragraphs = result.split("\n\n")
        first_chunk = "\n\n".join(paragraphs[0:chunk_size + 1])
        send(f"(1) chdbits 最新电影信息", first_chunk)
        time.sleep(3)

        for i in range(chunk_size + 1, len(paragraphs), chunk_size):
            chunk = "\n\n".join(paragraphs[i:i + chunk_size])
            block_number = (i // chunk_size) + 1

            if chunk.strip():
                send(f"({block_number}) chdbits 最新电影信息", chunk)
                time.sleep(3)
    # print(result)
