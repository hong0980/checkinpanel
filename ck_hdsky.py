# -*- coding: utf-8 -*-
"""
cron: 25 2 0,12 * * *
new Env('HDSky 签到');
"""

from io import BytesIO
from utils import get_data
from notify_mtr import send
import re, time, pytesseract, urllib3
from requests_html import HTMLSession
from PIL import Image, ImageFilter, ImageEnhance

# 禁用 InsecureRequestWarning 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
class HDSky:
    def __init__(self, check_items):
        self.check_items = check_items

    @staticmethod
    def sign(cookie, i):
        def fetch_image_hash():
            imagehash = s.post('https://hdsky.me/image_code_ajax.php', headers=headers, data={'action': 'new'}).json().get('code')
            img_response = s.get('https://hdsky.me/image.php', params={'action': 'regimage', 'imagehash': imagehash})
            return imagehash, img_response

        def binarize_image(img_response, threshold=100):
            img = Image.open(BytesIO(img_response.content)).convert('L')
            img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS) # 使用LANCZOS插值算法进行放大
            img = img.crop((45, 25, 252, 55)) # 截取图片
            img = ImageEnhance.Contrast(img).enhance(0.9) # 对比度设置
            img = img.filter(ImageFilter.MedianFilter(size=3)) # 减少图像中的噪声
            t = [0 if i < threshold else 1 for i in range(256)]
            return img.point(t, '1')

        def recognize_captcha_text(img_response):
            img = binarize_image(img_response, threshold=130)  # 阈值可调（100-150）
            custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            text = pytesseract.image_to_string(img, config=custom_config)
            text = re.sub(r'[^A-Z0-9]', '', text)[:6]
            return text if len(text) == 6 else None

        msg, count, max_count, s, cg_msg, url, headers = '', 0, 5, HTMLSession(), \
            '你今天已经签到了，请勿重复签到', 'https://hdsky.me/torrents.php', {
                'authority': 'hdsky.me', 'origin': 'https://hdsky.me',
                'referer': 'https://hdsky.me/torrents.php', "Cookie": cookie,
            }

        try:
            r = s.get(url, headers=headers, verify=False)
            if r.status_code == 200:
                if "未登录!" in r.text:
                    return (f"<b><span style='color: red'>签到失败</span></b>\n"
                            f"账号({i})无法登录！可能Cookie失效，请重新修改")

                if not '[已签到]' in r.text:
                    while count < max_count:
                        imagehash, img_response = fetch_image_hash()
                        imagestring = recognize_captcha_text(img_response)

                        short_imagehash = f"{imagehash[:3]}...{imagehash[-3:]}"
                        if imagestring:
                            print(f"识别到 {short_imagehash} 验证码: {imagestring}，执行第 {count + 1} 次签到。")
                            data = {'action': 'showup', 'imagehash': imagehash, 'imagestring': imagestring}
                            response = s.post('https://hdsky.me/showup.php', headers=headers, data=data)
                            if response.status_code == 200:
                                p = response.json()
                                success, message = p.get('success'), p.get('message')

                                if success == True:
                                    msg = "<b><span style='color: green'>签到成功</span></b>\n"
                                    cg_msg = (f"执行 {count + 1} 次\n已连续签到 {int((message - 10) / 2 + 1)} 天，"
                                              f"奖励 {message} 魔力值，明日继续签到可获得 {message + 2} 魔力值")
                                    r = s.get(url, headers=headers)
                                    break
                                elif message == 'date_unmatch':
                                    break
                                elif message == 'invalid_imagehash':
                                    count += 1
                                    if count != max_count:
                                        print(f"验证码错误。5 秒后重新获取验证，尝试重新签到。")
                                        time.sleep(5)
                                    else:
                                        msg = "<b><span style='color: red'>签到失败</span></b>\n"
                                        cg_msg = f"验证码错误。已经尝试 {max_count} 次签到，稍后再试。"
                                        print(cg_msg)
                                else:
                                    cg_msg = f"失败，信息：{message if message else '未知'}"
                                    print(cg_msg)
                            else:
                                msg = "<b><span style='color: red'>签到请求失败，无法签到</span></b>\n"
                        else:
                            print(f"识别到 {short_imagehash} 的验证码不符合要求。5 秒后重新获取验证。")
                            time.sleep(5)

                pattern = (r'InsaneUser_Name\'><b>(.*?)</b>.*?'
                           r'使用</a>]: (.*?)\s*'
                           r'<font.*?分享率：</font>\s*(.*?)\s*'
                           r'<font.*?上传量：</font>\s*(.*?)\s*'
                           r'<font.*?下载量：</font>\s*(.*?)\s*'
                           r'<font.*?当前做种.*?>\s*(\d+)\s*<img')
                result = re.findall(pattern, r.text, re.DOTALL)[0]
                res = (f"--- {result[0]} HDSky 签到结果 ---\n{msg}<b><span style='color: "
                       f"{'purple' if '今天已经签到了' in cg_msg else 'orange'}'>{cg_msg}</span></b>\n\n"
                       f'<b>账户信息</b>\n魔力值：{result[1]}\n'
                       f'分享率：{result[2]}\n上传量：{result[3]}\n'
                       f'下载量：{result[4]}\n当前做种：{result[5]}')
            else:
                res = f"请求失败，状态码：{r.status_code}"

        except Exception:
            import traceback
            return f"<b><span style='color: red'>未知异常：签到失败</span></b>\n{traceback.format_exc()}"
        return res

    def main(self):
        msg_all = ""
        for i, check_item in enumerate(self.check_items, start=1):
            cookie = check_item.get("cookie")
            msg_all += f'{self.sign(cookie, i)}\n\n'
        return msg_all

if __name__ == "__main__":
    result = HDSky(check_items=get_data().get("HDSKY", [])).main()
    if '奖励' in result or '签到失败' in result or '请求失败' in result:
        send("HDSky 签到", result)
    else:
        print(result)
