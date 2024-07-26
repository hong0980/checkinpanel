# -*- coding: utf-8 -*-
"""
cron: 15 0,11,20 * * *
new Env('HDSky 签到');
"""

import re
import time
import requests
import pytesseract
from io import BytesIO
from utils import get_data
from notify_mtr import send
from requests_html import HTMLSession
from PIL import Image, ImageFilter, ImageEnhance

class Get:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        res, msg, cg_msg, attempts, max_attempts = '', '', '', 0, 5
        headers = {
            "Cookie": cookie,
            'accept': '*/*',
            'authority': 'hdsky.me',
            'origin': 'https://hdsky.me',
            'referer': 'https://hdsky.me/torrents.php',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/102.0.0.0 Safari/537.36",
        }
        try:
            with HTMLSession() as s:
                r = s.get('https://hdsky.me/torrents.php', headers=headers, timeout=5)
                if not "欢迎回来" in r.text:
                    return f'账号({i})无法登录！可能Cookie失效，请重新修改'

                if '[已签到]' in r.text:
                    cg_msg = '今天已经签到了'
                else:
                    def fetch_image_hash():
                        return s.post(
                            'https://hdsky.me/image_code_ajax.php', headers=headers, data={'action': 'new'}
                        ).json()['code']

                    def fetch_captcha_image(imagehash):
                        params = {'action': 'regimage', 'imagehash': imagehash}
                        headers['accept'] = 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
                        return s.get('https://hdsky.me/image.php', headers=headers, params=params)

                    def binarize_image(img_response, threshold):
                        def crop_center(img, width, height):
                            img_width, img_height = img.size
                            left = (img_width - width) // 2
                            top = (img_height - height) // 2
                            right = left + width
                            bottom = top + height
                            return img.crop((left, top, right, bottom))

                        img = Image.open(BytesIO(img_response.content)).convert('L')
                        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS) # 使用LANCZOS插值算法进行放大
                        img = img.crop((45, 25, 252, 55)) # 截取图片
                        # img = crop_center(img, 210, 30) # 截取图片
                        img = ImageEnhance.Contrast(img).enhance(0.9) # 对比度设置
                        img = img.filter(ImageFilter.MedianFilter(size=3)) # 减少图像中的噪声
                        t = []
                        for i in range(256):
                            if i < threshold:
                                t.append(0)
                            else:
                                t.append(1)
                        img = img.point(t, '1')
                        return img

                    def recognize_captcha_text(img_response):
                        img = binarize_image(img_response, 100)
                        custom_config = r'--oem 3 --psm 6' # oem 0-4 psm 0-13
                        imagestring = pytesseract.image_to_string(img, lang='eng', config=custom_config)
                        imagestring = re.sub(r'[^a-zA-Z0-9]', '', imagestring)
                        if imagestring:
                            img.save(f'/tmp/captcha.jpg')
                            return imagestring
                        return None

                    while attempts < max_attempts:
                        imagehash = fetch_image_hash()
                        img_response = fetch_captcha_image(imagehash)
                        imagestring = recognize_captcha_text(img_response)
                        short_imagehash = f"{imagehash[:4]}...{imagehash[-4:]}"

                        if imagestring and len(imagestring) == 6:
                            print(f"识别到 {short_imagehash} 验证码: {imagestring}，执行第 {attempts + 1} 次签到。")
                            data = {
                                'action': 'showup', 'imagehash': imagehash, 'imagestring': imagestring,
                            }
                            p = s.post('https://hdsky.me/showup.php', headers=headers, data=data)
                            message = p.json()['message']

                            if p.json()['success'] == True:
                                days = int((message - 10) / 2 + 1)
                                msg = "<b><span style='color: green'>签到成功</span></b>\n"
                                cg_msg = (f"已连续签到 {days} 天，"
                                       f"奖励 {message} 魔力值，明日继续签到可获取 {message + 2} 魔力值"
                                )
                                r = s.get('https://hdsky.me/torrents.php', headers=headers)
                                break
                            elif message == 'date_unmatch':
                                cg_msg = f"你今天已经签到了，请勿重复签到"
                                break
                            elif message == 'invalid_imagehash':
                                if attempts < max_attempts:
                                    attempts += 1
                                    print(f"验证码错误。重新获取验证，尝试重新签到。")
                                    time.sleep(2)
                                else:
                                    msg = "<b><span style='color: red'>签到失败/span></b>\n"
                                    cg_msg = f"尝试次数已达上限 ({max_attempts} 次)，无法完成签到"
                                    print(cg_msg)
                            else:
                                cg_msg = f"失败，信息：{message if message else ''}"
                                print(cg_msg)
                        else:
                            print(f"识别到 {short_imagehash} 的验证码 {imagestring} 不符合要求。重新获取验证。")
                            time.sleep(2)

                name = re.findall(r"class='InsaneUser_Name'><b>(.*?)</b><", r.text, re.DOTALL)[0]
                res = f"\n--- {name} HDSky 签到结果 ---\n{msg}"
                res += f"<b><span style='color: {'purple' if '今天已经签到了' in cg_msg else 'orange'}'>{cg_msg}</span></b>\n\n"
                pattern = r'使用</a>]: (.*?)\s*<font.*?分享率：</font>\s*(.*?)\s*<font.*?上传量：</font>\s*(.*?)\s*<font.*?下载量：</font>\s*(.*?)\s*<font.*?当前做种.*?>\s*(\d+)\s*<img'
                result = re.findall(pattern, r.text, re.DOTALL)[0]
                res += (f'<b>账户信息</b>\n'
                       f'魔力值：{result[0]}\n'
                       f'分享率：{result[1]}\n'
                       f'上传量：{result[2]}\n'
                       f'下载量：{result[3]}\n'
                       f'当前做种：{result[4]}'
                )

        except requests.RequestException as e:
            res = f"请求异常: {e}"
        except Exception as e:
            res = f"出现错误: {e}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg = self.sign(cookie, i)
            msg_all += msg + "\n\n"
        return msg_all

if __name__ == "__main__":
    _data = get_data()
    _check_items = _data.get("HDSKY", [])
    result = Get(check_items=_check_items).main()
    if '今天已经签到了' in result:
        print(result)
    else:
        send("HDSky 签到", result)
