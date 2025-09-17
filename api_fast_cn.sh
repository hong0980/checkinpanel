#!/usr/bin/env bash

<<'COMMENT'
cron: 45 12 */7 * *
new Env('国内加速');
COMMENT

echo "🚀 开始配置青龙面板国内加速源..."
echo "=========================================="

# 1. Alpine 换源
echo "📦 配置Alpine国内镜像源..."
if [ -f /etc/apk/repositories ]; then
    cp /etc/apk/repositories /etc/apk/repositories.bak 2>/dev/null
    sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories
    sed -i 's/http:\/\/dl-cdn.alpinelinux.org/https:\/\/mirrors.aliyun.com/g' /etc/apk/repositories
    echo "✅ Alpine镜像源已配置为阿里云"
else
    echo "⚠️  Alpine未找到，跳过配置"
fi

# 2. Python pip 换源
echo "🐍 配置Python pip国内镜像源..."
mkdir -p /root/.config/pip
cat > /root/.config/pip/pip.conf << 'EOF'
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple/
extra-index-url =
    https://mirrors.aliyun.com/pypi/simple/
    https://pypi.mirrors.ustc.edu.cn/simple/
    https://pypi.doubanio.com/simple/

[install]
trusted-host =
    pypi.tuna.tsinghua.edu.cn
    mirrors.aliyun.com
    pypi.mirrors.ustc.edu.cn
    pypi.doubanio.com
EOF
echo "✅ Python pip源已配置(清华+阿里云+中科大+豆瓣)"

# 3. NPM 换源
echo "📦 配置NPM国内镜像源..."
if command -v npm > /dev/null 2>&1; then
    npm config set registry https://registry.npmmirror.com /dev/null 2>&1
    echo "✅ NPM registry已配置为淘宝镜像"
else
    echo "⚠️  NPM未安装，跳过配置"
fi

# 4. Node.js 和 NPM 二进制镜像环境变量配置
echo "🟢 配置Node.js和NPM国内镜像环境变量..."
NODE_MIRROR_CONFIG='
# Node.js and NPM mirrors
export NODEJS_ORG_MIRROR=https://npmmirror.com/mirrors/node
export NODIST_NODE_MIRROR=https://npmmirror.com/mirrors/node
export PHANTOMJS_CDNURL=https://npmmirror.com/mirrors/phantomjs
export CHROMEDRIVER_CDNURL=https://npmmirror.com/mirrors/chromedriver
export OPERADRIVER_CDNURL=https://npmmirror.com/mirrors/operadriver
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/
export SASS_BINARY_SITE=https://npmmirror.com/mirrors/node-sass
export PUPPETEER_DOWNLOAD_HOST=https://npmmirror.com/mirrors
export DISTURL=https://npmmirror.com/dist
'

# 写入bashrc
echo "$NODE_MIRROR_CONFIG" >> ~/.bashrc
# 设置当前会话的环境变量
eval "$NODE_MIRROR_CONFIG"

echo "✅ Node.js和NPM镜像环境变量已配置"

# 5. CPAN 换源 (Perl模块)
echo "🐪 配置CPAN国内镜像源..."
if command -v cpan > /dev/null 2>&1; then
    mkdir -p /root/.cpan/CPAN/
    cat > /root/.cpan/CPAN/MyConfig.pm << 'EOF'
$CPAN::Config = {
  'allow_installing_module_downgrades' => q[ask/no],
  'allow_installing_outdated_dists' => q[ask/no],
  'applypatch' => q[],
  'auto_commit' => q[0],
  'build_cache' => q[100],
  'build_dir' => q[/root/.cpan/build],
  'build_dir_reuse' => q[0],
  'build_requires_install_policy' => q[yes],
  'bzip2' => q[/usr/bin/bzip2],
  'cache_metadata' => q[1],
  'check_sigs' => q[0],
  'cleanup_after_install' => q[0],
  'colorize_output' => q[0],
  'commandnumber_in_prompt' => q[1],
  'connect_to_internet_ok' => q[1],
  'cpan_home' => q[/root/.cpan],
  'ftp_passive' => q[1],
  'ftp_proxy' => q[],
  'getcwd' => q[cwd],
  'gpg' => q[],
  'gzip' => q[/bin/gzip],
  'halt_on_failure' => q[0],
  'histfile' => q[/root/.cpan/histfile],
  'histsize' => q[100],
  'http_proxy' => q[],
  'inactivity_timeout' => q[0],
  'index_expire' => q[1],
  'inhibit_startup_message' => q[0],
  'keep_source_where' => q[/root/.cpan/sources],
  'load_module_verbosity' => q[none],
  'make' => q[/usr/bin/make],
  'make_arg' => q[],
  'make_install_arg' => q[],
  'make_install_make_command' => q[/usr/bin/make],
  'makepl_arg' => q[],
  'mbuild_arg' => q[],
  'mbuild_install_arg' => q[],
  'mbuild_install_build_command' => q[./Build],
  'mbuildpl_arg' => q[],
  'no_proxy' => q[],
  'pager' => q[/usr/bin/less],
  'patch' => q[],
  'perl5lib_verbosity' => q[none],
  'prefer_external_tar' => q[1],
  'prefer_installer' => q[MB],
  'prefs_dir' => q[/root/.cpan/prefs],
  'prerequisites_policy' => q[follow],
  'recommends_policy' => q[1],
  'scan_cache' => q[atstart],
  'shell' => q[/bin/bash],
  'show_unparsable_versions' => q[0],
  'show_upload_date' => q[0],
  'show_zero_versions' => q[0],
  'suggests_policy' => q[0],
  'tar' => q[/bin/tar],
  'tar_verbosity' => q[none],
  'term_is_latin' => q[1],
  'term_ornaments' => q[1],
  'test_report' => q[0],
  'trust_test_report_history' => q[0],
  'unzip' => q[/usr/bin/unzip],
  'urllist' => [q[http://mirrors.ustc.edu.cn/CPAN/], q[http://mirrors.tuna.tsinghua.edu.cn/CPAN/]],
  'use_prompt_default' => q[0],
  'use_sqlite' => q[0],
  'version_timeout' => q[15],
  'wget' => q[/usr/bin/wget],
  'yaml_load_code' => q[0],
  'yaml_module' => q[YAML],
};
1;
EOF
    echo "✅ CPAN源已配置为清华和中科大镜像"
else
    echo "⚠️  CPAN未安装，跳过配置"
fi


echo "=========================================="
echo "🎉 青龙面板国内加速配置完成！"
echo "📋 已配置:"
echo "   - Alpine软件源 → 阿里云"
echo "   - Python pip → 清华+阿里云+中科大+豆瓣"
echo "   - NPM registry → 淘宝镜像"
# echo "   - Node.js环境变量 → 包含所有二进制包镜像"
echo "   - CPAN → 清华+中科大镜像"
echo ""
echo "💡 建议重启青龙容器使配置生效"
echo "   docker restart qinglong"


echo ""
echo "✨ 所有配置已完成！"
