"""
cron: 0 1 1 */3 *
new Env('et8 登录');
"""

from requests_html import HTMLSession
from utils import get_data, setup_hooks

session = HTMLSession()
cookie = get_data().get("ET8", [{}])[0].get('cookie')
setup_hooks(session, truncate=1)

session.get('https://et8.org/torrents.php', headers={'cookie': cookie})
