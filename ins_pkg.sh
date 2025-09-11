#!/usr/bin/env bash

<<'COMMENT'
cron: 1 1 1 1 *
new Env('签到依赖');
COMMENT

pl_mods="File::Slurp JSON5 TOML::Dumper"
alpine_pkgs="py3-pip libffi-dev openssl-dev perl-app-cpanminus perl-dev make"
py_reqs="cryptography dateparser feedparser peewee requests_html schedule tomli lxml_html_clean"
js_pkgs="redis@4.7.0 global-agent https-proxy-agent@7.0.5 tunnel png-js date-fns axios@1.7.7 dotenv got@11.8.6 crypto-js sharp fs md5 ts-md5 request jsdom download js-base64 qrcode-terminal moment ws form-data tslib @types/node tough-cookie"

install() {
    local max_retries=3 retry_count=0 cmd="$1" pkg="$2"
    while [ $retry_count -lt $max_retries ]; do
        echo "....... 开始安装 $pkg ......."
        [[ $retry_count -gt 0 ]] && echo "$pkg (第 $((retry_count + 1)) 次) 尝试安装"
        if eval "$cmd"; then
            echo -e "✅ $pkg 安装成功\n"
            return
        fi
        retry_count=$((retry_count + 1))
        echo "⚠️ 安装失败，3 秒后重试..."
        sleep 3
    done
    echo "❌ $pkg 自动安装失败，请尝试进入容器后执行!!"
    return 1
}

install_alpine_pkgs() {
    apk update >/dev/null 2>&1
    for pkg in $alpine_pkgs; do
        if apk info -e "$pkg" >/dev/null 2>&1; then
            echo "ℹ️ $pkg 已安装"
            continue
        fi
        install "apk add --no-cache --quiet $pkg" "$pkg"
    done
}

install_py_reqs() {
    for pkg in $py_reqs; do
        if pip3 show "$pkg" >/dev/null 2>&1; then
            echo "ℹ️ $pkg 已安装"
            continue
        fi
        install "pip3 install --user -q --force-reinstall --disable-pip-version-check --root-user-action=ignore --use-pep517 $pkg" "$pkg"
    done
    pip3 install --user --root-user-action=ignore --upgrade pip -q >/dev/null 2>&1

    requests_html_info=$(pip3 show 'requests_html') || return
    requests_html_path=$(echo "$requests_html_info" | awk '/Location: / {print $2}')"/requests_html.py"
    if [ -f "$requests_html_path" ] && ! grep -q 'executablePath' "$requests_html_path"; then
        sed -i \
            -e "s|self, mock_browser|self, executablePath : str = None, mock_browser|" \
            -e "s|args=self.__browser_args)|args=self.__browser_args, executablePath=self.executablePath)|" \
            -e "/browser_args = browser_args/a\        self.executablePath = executablePath" \
            "$requests_html_path"
    fi
}

install_js_pkgs() {
    command -v pnpm &>/dev/null || install "npm install -g pnpm --silent" "pnpm"

    for pkg in $js_pkgs; do
        if [ -n "$(pnpm list -g $pkg --silent)" ]; then
            echo "ℹ️ $pkg 已安装"
            continue
        fi
        install "pnpm add -g --silent $pkg" "$pkg"
    done
    pnpm list -g --depth 0
}

install_pl_mods() {
    if command -v cpm >/dev/null 2>&1; then
        echo "ℹ️ App::cpm 已安装"
    else
        install "cpanm --quiet -fn --notest App::cpm >/dev/null 2>&1" "cpanm -fn App::cpm"
        if ! command -v cpm >/dev/null 2>&1; then
            curl -fsSL https://cdn.jsdelivr.net/gh/Oreomeow/checkinpanel/cpm >cpm && chmod +x cpm && ./cpm --version
        fi
    fi
    for i in $pl_mods; do
        if perldoc -l "$i" > /dev/null 2>&1; then
            echo "ℹ️ $i 已安装"
        else
            install "cpm install -g --static-install $i" "$i"
        fi
    done
}

install_js_pkgs
install_py_reqs
install_alpine_pkgs
install_pl_mods
