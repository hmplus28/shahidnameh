#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  شهیدنامه (shahidnameh) — اسکریپت استقرار روی هاست اشتراکی cPanel (میزبانفا و مشابه)
#
#  کارهایی که انجام می‌دهد:
#    ۱. یافتن و «الزام» استفاده از محیط مجازی «Setup Python App» خود سی‌پنل
#       (مسیر ‎~/virtualenv/<پوشه-پروژه>/<نسخه>‎) — این اسکریپت هیچ venv دستی
#       نمی‌سازد؛ اگر برنامهٔ پایتون در سی‌پنل ساخته نشده باشد، راهنمای گام‌به‌گام
#       نمایش داده می‌شود و متوقف می‌شود.
#    ۲. ساخت خودکار فایل ‎.env‎ با کلید امنیتی تصادفی (DJANGO_SECRET_KEY،
#       DJANGO_DEBUG، DJANGO_ALLOWED_HOSTS و …) — مقادیر موجود بازنویسی نمی‌شوند.
#    ۳. کنترل کامل بودن مشخصات MySQL (فقط اگر DB_ENGINE=mysql باشد؛
#       پیش‌فرض پروژه SQLite است و بدون دیتابیس MySQL هم کار می‌کند).
#    ۴. نصب وابستگی‌ها در همان venv سی‌پنل (Django، Pillow، whitenoise، …)
#    ۵. اجرای مایگریشن‌ها، جمع‌آوری فایل‌های استاتیک، همگام‌سازی نقش‌ها
#       (configure_roles) و ساخت اختیاری مدیر اولیه
#    ۶. ساخت/به‌روزرسانی ‎passenger_wsgi.py‎ (نقطه ورود Passenger سی‌پنل) —
#       برای venv سی‌پنل بدون re-exec (سازگار با لودر lswsgi) ساخته می‌شود.
#    ۷. افزودن قواعد امنیتی به ‎.htaccess‎ (جلوی دانلود ‎.env‎، دیتابیس، سورس
#       پایتون و پوشه‌های حساس از وب — مخصوصاً وقتی پروژه داخل public_html است)
#    ۸. ری‌استارت برنامه (tmp/restart.txt)
#
#  نحوه اجرا (از داخل پوشه پروژه، در ترمینال cPanel یا SSH):
#      bash deploy/deploy_cpanel.sh
#
#  گزینه‌ها:
#      --venv <مسیر>    استفاده از محیط مجازی مشخص (خارج از حالت پیش‌فرض)
#                       (مثلاً ‎--venv ~/virtualenv/shahidnameh/3.11‎)
#      --python <مسیر>  پایتون جایگزین — فقط همراه ‎--venv‎ استفاده می‌شود
#      -h | --help      نمایش راهنما
#
#  متغیرهای محیطی جایگزین: SHAHIDNAMEH_VENV و SHAHIDNAMEH_PYTHON
#
#  برای به‌روزرسانی‌های بعدی:  git pull && bash deploy/deploy_cpanel.sh
#  (اسکریپت idempotent است و قابل اجرای مکرر.)
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# ------------------------------------------------------------- تنظیمات ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# هم از داخل deploy/ اجرا می‌شود هم از ریشه پروژه
if [ -f "$SCRIPT_DIR/manage.py" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
else
    PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
fi
VENV_DIR="${SHAHIDNAMEH_VENV:-}"
PYTHON_BIN="${SHAHIDNAMEH_PYTHON:-}"
SETTINGS_MODULE="config.settings"

# رنگ‌ها (در ترمینال‌های بدون رنگ مشکلی ایجاد نمی‌کنند)
if [ -t 1 ]; then
    C_GREEN='\033[0;32m'; C_YELLOW='\033[1;33m'; C_RED='\033[0;31m'; C_BLUE='\033[0;34m'; C_OFF='\033[0m'
else
    C_GREEN=''; C_YELLOW=''; C_RED=''; C_BLUE=''; C_OFF=''
fi
say()  { echo -e "${C_GREEN}✔${C_OFF} $*"; }
info() { echo -e "${C_BLUE}ℹ${C_OFF} $*"; }
warn() { echo -e "${C_YELLOW}⚠${C_OFF} $*" >&2; }
die()  { echo -e "${C_RED}✘ خطا:${C_OFF} $*" >&2; exit 1; }

echo ""
echo -e "${C_BLUE}═══════════════════════════════════════════════════════════════${C_OFF}"
echo -e "${C_BLUE}  شهیدنامه — استقرار روی cPanel${C_OFF}"
echo -e "${C_BLUE}═══════════════════════════════════════════════════════════════${C_OFF}"
info "پوشه پروژه: $PROJECT_DIR"

[ -f "$PROJECT_DIR/manage.py" ] || die "فایل manage.py در «$PROJECT_DIR» پیدا نشد.
اسکریپت را از داخل پوشه پروژه اجرا کنید:  bash deploy/deploy_cpanel.sh"

# ----------------------------------------------- آرگومان‌های خط فرمان ----
show_help() {
    awk 'NR>1 { if ($0 ~ /^#/) { sub(/^# ? ?/, ""); print } else exit }' "$0"
}
while [ $# -gt 0 ]; do
    case "$1" in
        --venv)   [ $# -ge 2 ] || die "گزینه --venv نیاز به مسیر دارد"; VENV_DIR="$2"; shift 2 ;;
        --venv=*) VENV_DIR="${1#*=}"; shift ;;
        --python) [ $# -ge 2 ] || die "گزینه --python نیاز به مسیر دارد"; PYTHON_BIN="$2"; shift 2 ;;
        --python=*) PYTHON_BIN="${1#*=}"; shift ;;
        -h|--help) show_help; exit 0 ;;
        *) warn "آرگومان ناشناخته: $1 (نادیده گرفته شد)" ; shift ;;
    esac
done

# گسترش ~ در مسیرهای داده‌شده (برای وقتی که کوتیشن‌شده پاس داده شده باشد)
expand_tilde() {
    case "$1" in
        "~")  echo "$HOME" ;;
        "~/"*) echo "$HOME${1#\~}" ;;
        *)    echo "$1" ;;
    esac
}
[ -n "$VENV_DIR" ]   && VENV_DIR="$(expand_tilde "$VENV_DIR")"
[ -n "$PYTHON_BIN" ] && PYTHON_BIN="$(expand_tilde "$PYTHON_BIN")"

# ----------------------------------------------------- فایل .env و دیتابیس ----
# این بخش عمداً قبل از کارهای سنگین اجرا می‌شود تا اگر مشخصات دیتابیس ناقص
# باشد، راهنمای گام‌به‌گام فوراً نمایش داده شود.
ENV_FILE="$PROJECT_DIR/.env"
CPANEL_USER="$(id -un)"

# خواندن مقدار یک کلید از .env (آخرین occurrence؛ خطوط کامنت نادیده می‌شوند)
env_value() {
    sed -n "s/^$1=//p" "$ENV_FILE" 2>/dev/null | tail -n 1 | tr -d '\r' || true
}

# کنترل کامل بودن مشخصات MySQL — اگر ناقص باشد با راهنمای گام‌به‌گام متوقف می‌شود
mysql_env_check() {
    local engine name_ user_ pass_ host_ port_
    engine="$(env_value DB_ENGINE | tr '[:upper:]' '[:lower:]')"
    case "$engine" in
        mysql|mariadb) ;;
        *) info "دیتابیس: SQLite (فایل db.sqlite3) — نیازی به تنظیمات اضافه نیست."; return 0 ;;
    esac
    name_="$(env_value DB_NAME)"
    user_="$(env_value DB_USER)"
    pass_="$(env_value DB_PASSWORD)"
    if [ -z "$name_" ] || [ -z "$user_" ] || [ -z "$pass_" ] || [ "$pass_" = "CHANGE_ME" ]; then
        die "DB_ENGINE=mysql است اما مشخصات دیتابیس در ‎.env‎ کامل نیست
(مقدار DB_PASSWORD هنوز CHANGE_ME/خالی است یا DB_NAME/DB_USER خالی‌اند).

راهنمای گام‌به‌گام ساخت دیتابیس در cPanel:
  ۱) بخش «MySQL® Databases» را باز کنید:
       • Create New Database → مثلاً shahidnameh (نام کامل می‌شود ${CPANEL_USER}_shahidnameh)
       • MySQL Users → Add New User (رمز قوی؛ یادداشتش کنید)
       • Add User To Database → همان یوزر/دیتابیس → تیک ALL PRIVILEGES → Changes
  ۲) در فایل ‎.env‎ این خط‌ها را کامل و از کامنت خارج کنید:
       DB_ENGINE=mysql
       DB_NAME=${CPANEL_USER}_shahidnameh
       DB_USER=${CPANEL_USER}_shahidnameh
       DB_PASSWORD=همان-رمزی-که-ساختید
       DB_HOST=localhost
       DB_PORT=3306
  ۳) این اسکریپت را دوباره اجرا کنید:
       bash deploy/deploy_cpanel.sh
  (اگر MySQL نمی‌خواهید این خط‌ها کامنت بمانند — دیتابیس فایل db.sqlite3 می‌شود)"
    fi
    host_="$(env_value DB_HOST)"; host_="${host_:-localhost}"
    port_="$(env_value DB_PORT)"; port_="${port_:-3306}"
    info "دیتابیس: MySQL — ‎${name_}‎ روی ‎${host_}:${port_}‎"
    return 0
}

if [ -f "$ENV_FILE" ]; then
    say "فایل ‎.env‎ موجود است (مقادیر موجود حفظ می‌شوند)."
else
    say "فایل ‎.env‎ وجود ندارد؛ در حال ساخت با کلید امنیتی تصادفی ..."
    SECRET_KEY="$(head -c 96 /dev/urandom | base64 | tr -d '\n=+/')"
    cat > "$ENV_FILE" << EOF
# شهیدنامه — تنظیمات محیط تولید (توسط deploy/deploy_cpanel.sh ساخته شده)
# مقادیر زیر را مطابق دامنه خود ویرایش کنید و سپس اسکریپت را دوباره اجرا کنید.

# کلید امنیتی (تصادفی تولید شده — آن را تغییر ندهید)
DJANGO_SECRET_KEY=$SECRET_KEY

# حالت دیباگ — در تولید باید False بماند
# (اگر هنوز SSL/گواهی HTTPS ندارید و ورود پنل کار نکرد، موقتاً true بگذارید
#  و بعد از فعال‌سازی SSL دوباره False کنید)
DJANGO_DEBUG=False

# دامنه‌های مجاز — دامنه/زیردامنه خود را جایگزین * کنید (با کاما جدا کنید)
DJANGO_ALLOWED_HOSTS=*

# اگر آدرس‌ها را با https://دامنه-شما باز می‌کنید و صفحه ورود خطای CSRF داد،
# خط زیر را از کامنت درآورید و دامنه واقعی بنویسید:
# DJANGO_CSRF_TRUSTED_ORIGINS=https://shahidnameh.example.ir

# ── دیتابیس ──
# پیش‌فرض: SQLite (هیچ کاری لازم نیست؛ فایل db.sqlite3 ساخته می‌شود).
# برای MySQL/MariaDB سی‌پنل، خط‌های زیر را از کامنت درآورید و کامل کنید
# (راهنمای ساخت دیتابیس در خروجی همین اسکریپت هم نمایش داده می‌شود):
# DB_ENGINE=mysql
# DB_NAME=${CPANEL_USER}_shahidnameh
# DB_USER=${CPANEL_USER}_shahidnameh
# DB_PASSWORD=CHANGE_ME
# DB_HOST=localhost
# DB_PORT=3306

# مدیر اولیه (اختیاری) — این سه خط را از کامنت درآورید تا superuser
# خودکار ساخته شود (سپس اسکریپت را دوباره اجرا کنید):
# DJANGO_SUPERUSER_USERNAME=admin
# DJANGO_SUPERUSER_PASSWORD=Strong-Pass-1234
# DJANGO_SUPERUSER_EMAIL=admin@example.com
EOF
    say "فایل ‎.env‎ ساخته شد: $ENV_FILE"
    warn "بعد از استقرار، DJANGO_ALLOWED_HOSTS را در ‎.env‎ به دامنه واقعی خود محدود کنید."
fi
mysql_env_check

# ------------------------------------------------- نسخه پایتون و venv ----
# پروژه Django 5.x است → حداقل پایتون ۳.۱۰ لازم است.
python_ok() {
    local v
    v="$("$1" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null)" || return 1
    case "$v" in
        3.1[0-9]|3.[2-9][0-9]) return 0 ;;
        *) return 1 ;;
    esac
}

# ── یافتن محیط مجازی «Setup Python App» سی‌پنل (الزامی) ──
# سی‌پنل برای هر برنامه پایتون، venv را در ‎~/virtualenv/<Application root>/<نسخه>‎
# می‌سازد. این اسکریپت طبق الزام پروژه، «فقط» از همین venv استفاده می‌کند و
# هیچ‌وقت venv دستی نمی‌سازد (به‌جز حالتی که خودتان با ‎--venv‎ مسیر بدهید).
find_cpanel_venv() {
    local ver_dir proj_base rel
    local -a roots=()

    proj_base="$(basename "$PROJECT_DIR")"
    roots+=( "$HOME/virtualenv/$proj_base" )
    case "$PROJECT_DIR" in
        "$HOME"/*)
            rel="${PROJECT_DIR#${HOME}/}"
            if [ -n "$rel" ] && [ "$rel" != "$PROJECT_DIR" ]; then
                roots+=( "$HOME/virtualenv/$rel" )
            fi
            ;;
    esac

    # الگوی استاندارد کلودلینوکس: ~/virtualenv/<اپ>/<نسخه>/bin/python
    local root
    for root in "${roots[@]}"; do
        [ -d "$root" ] || continue
        while IFS= read -r ver_dir; do
            if [ -x "${ver_dir%/}/bin/python" ] && python_ok "${ver_dir%/}/bin/python"; then
                echo "${ver_dir%/}"
                return 0
            fi
        done < <(ls -1d "$root"/*/ 2>/dev/null | sort -rV)
        # الگوی نادر: venv مستقیماً داخل پوشه اپ
        if [ -x "$root/bin/python" ] && python_ok "$root/bin/python"; then
            echo "$root"
            return 0
        fi
    done
    return 1
}

if [ -z "$VENV_DIR" ]; then
    info "در حال یافتن محیط مجازی «Setup Python App» سی‌پنل ..."
    VENV_DIR="$(find_cpanel_venv)" || VENV_DIR=""
fi

if [ -z "$VENV_DIR" ]; then
    die "محیط مجازی «Setup Python App» سی‌پنل برای این پروژه پیدا نشد.
این اسکریپت طبق الزام پروژه باید از venv خود سی‌پنل استفاده کند و venv دستی نمی‌سازد.

راه‌حل (پیشنهادی و ساده) — ساخت برنامه پایتون در سی‌پنل:
  ۱) وارد cPanel شوید و بخش «Setup Python App» (یا «Python Selector») را باز کنید.
  ۲) روی «Create Application» بزنید و این مقادیر را وارد کنید:
       • Python version : 3.11 (یا هر نسخه ≥ 3.10 که ارائه می‌دهد)
       • Application root : $(basename "$PROJECT_DIR")   ← پوشه همین پروژه
       • Application URL  : دامنه یا زیردامنه شما
       • Application startup file : passenger_wsgi.py
  ۳) روی «Create» بزنید. سی‌پنل خودش venv را می‌سازد (معمولاً در
     ‎~/virtualenv/$(basename "$PROJECT_DIR")/<نسخه>‎).
  ۴) دوباره این اسکریپت را اجرا کنید:
       bash deploy/deploy_cpanel.sh
     اسکریپت خودش venv سی‌پنل را پیدا و همه مراحل را با آن انجام می‌دهد.

راه‌حل جایگزین — اگر venv را در مسیر دیگری دارید، مسیرش را بدهید:
       bash deploy/deploy_cpanel.sh --venv ~/virtualenv/$(basename "$PROJECT_DIR")/3.11

راهنمای کامل مصور: deploy/GUIDE-CPANEL-FA.md"
fi

say "محیط مجازی سی‌پنل: $VENV_DIR"
VENV_PY="$VENV_DIR/bin/python"
[ -x "$VENV_PY" ] || die "پایتون محیط مجازی در $VENV_PY قابل اجرا نیست."
python_ok "$VENV_PY" || die "پایتون محیط مجازی «$VENV_DIR» قدیمی است (<3.10).
در cPanel → Setup Python App یک برنامه با پایتون 3.10 یا جدیدتر بسازید
یا با ‎--venv‎ مسیر venv مناسب را بدهید."
VENV_PY_VERSION="$("$VENV_PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
info "پایتون: $VENV_PY_VERSION"

# تشخیص نوع venv: اگر زیر ‎~/virtualenv‎ باشد یا لودر lswsgi داشته باشد،
# یعنی venv «Setup Python App» سی‌پنل است و Passenger خودش با همین پایتون
# اجرا می‌کند (بدون نیاز به re-exec).
IS_SELECTOR_VENV=0
case "$VENV_DIR" in
    "$HOME"/virtualenv/*) IS_SELECTOR_VENV=1 ;;
esac
if [ -x "$VENV_DIR/bin/lswsgi" ]; then IS_SELECTOR_VENV=1; fi

# ------------------------------------------------------ نصب وابستگی‌ها ----
say "به‌روزرسانی pip در venv سی‌پنل ..."
"$VENV_PY" -m pip install --quiet --upgrade pip wheel setuptools

say "نصب وابستگی‌ها (چند دقیقه صبر کنید) ..."
"$VENV_PY" -m pip install --quiet -r "$PROJECT_DIR/requirements.txt"

# اگر MySQL انتخاب شده باشد، درایور mysqlclient هم لازم است
if [ "$(env_value DB_ENGINE | tr '[:upper:]' '[:lower:]')" = "mysql" ] \
   || [ "$(env_value DB_ENGINE | tr '[:upper:]' '[:lower:]')" = "mariadb" ]; then
    if ! "$VENV_PY" -c 'import MySQLdb' >/dev/null 2>&1; then
        say "نصب درایور MySQL (mysqlclient) ..."
        if ! "$VENV_PY" -m pip install --quiet mysqlclient; then
            die "نصب mysqlclient ناموفق بود. در برخی هاست‌ها باید از بخش
«Setup Python App → Run Pip Install» مقدار mysqlclient را نصب کنید
یا از پشتیبانی هاست بخواهید کتابخانه libmysqlclient را فعال کند.
راه‌حل سریع‌تر: در ‎.env‎ خط DB_ENGINE را کامنت کنید تا SQLite استفاده شود."
        fi
    fi
fi

# ------------------------------------------------------------- دستورات جنگو ----
export DJANGO_SETTINGS_MODULE="$SETTINGS_MODULE"

say "اجرای مایگریشن‌ها ..."
"$VENV_PY" "$PROJECT_DIR/manage.py" migrate --noinput

say "جمع‌آوری فایل‌های استاتیک ..."
"$VENV_PY" "$PROJECT_DIR/manage.py" collectstatic --noinput

say "همگام‌سازی گروه‌ها و مجوزها (نویسنده/ناظر) ..."
"$VENV_PY" "$PROJECT_DIR/manage.py" configure_roles || warn "همگام‌سازی نقش‌ها رد شد (احتمالاً از قبل انجام شده)."

# سوپریوزر خودکار اگر متغیرها در .env از کامنت درآمده باشند
SU_USERNAME="$(env_value DJANGO_SUPERUSER_USERNAME)"
SU_PASSWORD="$(env_value DJANGO_SUPERUSER_PASSWORD)"
if [ -n "$SU_USERNAME" ] && [ -n "$SU_PASSWORD" ]; then
    say "ساخت مدیر اولیه ($SU_USERNAME) ..."
    "$VENV_PY" "$PROJECT_DIR/manage.py" createsuperuser --noinput 2>/dev/null \
        || info "مدیر از قبل وجود دارد یا ساخته نشد."
fi

# ------------------------------------------------------------ passenger_wsgi ----
# فایل هر بار بازسازی می‌شود. برای venv «Setup Python App» سی‌پنل، wsgi باید
# ساده باشد و re-exec (os.execl) نداشته باشد؛ چون re-exec با لودر CloudLinux
# (lswsgi) سازگار نیست و خطای 503 می‌دهد. Passenger خودش با پایتون همین venv
# اسپاون می‌کند.
WSGI_FILE="$PROJECT_DIR/passenger_wsgi.py"
WSGI_MARKER="# SHAHIDNAMEH-PASSENGER-WSGI"
if [ -f "$WSGI_FILE" ] && ! grep -q "$WSGI_MARKER" "$WSGI_FILE" 2>/dev/null; then
    if [ ! -f "$WSGI_FILE.cpanel-backup" ]; then
        cp "$WSGI_FILE" "$WSGI_FILE.cpanel-backup"
        info "نسخه قبلی passenger_wsgi.py در ‎passenger_wsgi.py.cpanel-backup‎ نگه داشته شد."
    fi
fi
say "ساخت/به‌روزرسانی ‎passenger_wsgi.py‎ (نقطه ورود Passenger سی‌پنل) ..."

if [ "$IS_SELECTOR_VENV" -eq 1 ]; then
    cat > "$WSGI_FILE" << 'SHWWSGI'
# SHAHIDNAMEH-PASSENGER-WSGI — نقطه ورود WSGI برای cPanel/Passenger
# این فایل توسط deploy/deploy_cpanel.sh ساخته می‌شود؛ آن را دستی ویرایش نکنید
# (اجرای دوباره اسکریپت، آن را با تنظیمات به‌روز بازسازی می‌کند).
#
# venv از نوع «Setup Python App» سی‌پنل است؛ Passenger خودش با پایتون همین
# venv اجرا می‌کند، پس عمداً هیچ re-exec ای این‌جا نیست (re-exec با لودر
# lswsgi سی‌پنل سازگار نیست و 503 می‌دهد).

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings",
)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
SHWWSGI
    say "passenger_wsgi.py آماده شد (Setup Python App سی‌پنل — بدون re-exec؛ پایتون: $VENV_DIR/bin/python)."
else
    cat > "$WSGI_FILE" << SHWWSGI
# SHAHIDNAMEH-PASSENGER-WSGI — نقطه ورود WSGI برای cPanel/Passenger
# این فایل توسط deploy/deploy_cpanel.sh ساخته می‌شود؛ آن را دستی ویرایش نکنید
# (اجرای دوباره اسکریپت، آن را با تنظیمات به‌روز بازسازی می‌کند).

import os
import sys

# Passenger ممکن است این فایل را با پایتون سیستمی (قدیمی) اجرا کند؛ در آن
# صورت با پایتونِ محیط مجازی دوباره اجرا می‌شویم.
INTERP = r"$VENV_DIR/bin/python"
if os.path.realpath(os.path.dirname(sys.executable)) != os.path.realpath(os.path.dirname(INTERP)):
    os.execl(INTERP, INTERP, *sys.argv)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "$SETTINGS_MODULE")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
SHWWSGI
    say "passenger_wsgi.py آماده شد (اجرای برنامه با: $VENV_DIR/bin/python)."
fi

# ------------------------------------------------- قواعد امنیتی .htaccess ----
# اگر پروژه داخل public_html باشد، بدون این قواعد فایل‌های حساس (.env،
# db.sqlite3، سورس پایتون و…) از وب قابل دانلود هستند.
# توجه: فایل‌های قابل سرو (css/js/تصاویر/فونت‌ها/manifest.webmanifest/رسانه‌های
# پنل) مسدود نمی‌شوند.
HTACCESS_FILE="$PROJECT_DIR/.htaccess"
HT_MARKER="# BEGIN SHAHIDNAMEH-PROTECT"
write_htaccess_block() {
    cat << 'HTACCESS'
# BEGIN SHAHIDNAMEH-PROTECT
# ── محافظت از فایل‌های حساس شهیدنامه (تولیدشده توسط deploy/deploy_cpanel.sh) ──
Options -Indexes

# فایل‌های محیط، دیتابیس و پشتیبان — هرگز از وب قابل دانلود نباشند
<FilesMatch "\.env(\.[a-zA-Z0-9]+)?$|\.(sqlite3|sqlite3-journal|sqlite3-wal|sqlite3-shm|db|log|bak|backup|old|orig|swp)$">
    Require all denied
</FilesMatch>

# سورس پایتون، تنظیمات و مستندات پروژه
# (manifest.webmanifest و css/js/فونت/تصاویر شامل نمی‌شود)
<FilesMatch "\.(py|pyc|pyo|md|txt|sh|toml|cfg|ini|json|ya?ml|lock|example|gitignore|gitattributes|cpanel-backup)$">
    Require all denied
</FilesMatch>

# پوشه‌های حساس (نسبت به همین پوشه) — رسانه‌ها و static مسدود نمی‌شوند
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteRule (^|/)(\.git|\.venv|\.venv-host|venv|deploy|backups|logs|tmp)(/|$) - [F]
</IfModule>
# END SHAHIDNAMEH-PROTECT
HTACCESS
}
if [ ! -f "$HTACCESS_FILE" ]; then
    write_htaccess_block > "$HTACCESS_FILE"
    say ".htaccess ساخته شد (محافظت از فایل‌های حساس، مخصوصاً زیر public_html)."
elif grep -q "$HT_MARKER" "$HTACCESS_FILE" 2>/dev/null; then
    say "قواعد امنیتی .htaccess از قبل فعال است."
else
    if [ ! -f "$HTACCESS_FILE.shahidnameh-backup" ]; then
        cp "$HTACCESS_FILE" "$HTACCESS_FILE.shahidnameh-backup"
        info "نسخه قبلی .htaccess در ‎.htaccess.shahidnameh-backup‎ نگه داشته شد."
    fi
    printf '\n' >> "$HTACCESS_FILE"
    write_htaccess_block >> "$HTACCESS_FILE"
    say "قواعد امنیتی به .htaccess موجود افزوده شد."
fi
case "$PROJECT_DIR" in
    */public_html/*) warn "پروژه داخل public_html است؛ قواعد امنیتی نصب شد اما توصیه می‌شود در بلندمدت برنامه را خارج از public_html نگه دارید." ;;
esac

# ------------------------------------------------- پوشه‌های لازم و ری‌استارت ----
mkdir -p "$PROJECT_DIR/media" "$PROJECT_DIR/tmp" "$PROJECT_DIR/logs"

say "ری‌استارت برنامه (Passenger) ..."
touch "$PROJECT_DIR/tmp/restart.txt"

# ------------------------------------------------------------------ خلاصه ----
echo ""
echo -e "${C_GREEN}═══════════════════════════════════════════════════════════════${C_OFF}"
say "استقرار کامل شد."
echo -e "${C_GREEN}═══════════════════════════════════════════════════════════════${C_OFF}"
echo ""
echo "قدم‌های بعدی (اگر برای اولین بار استقرار می‌کنید):"
echo ""
echo -e "  ۱. در cPanel → ${C_YELLOW}Setup Python App${C_OFF} بررسی کنید:"
echo "     • Python version: 3.10+  |  Application root: $(basename "$PROJECT_DIR")"
echo "     • Application startup file: passenger_wsgi.py"
echo -e "     • اگر صفحه برنامه را باز کردید و تغییری ندیدید، دکمه ${C_YELLOW}Restart${C_OFF} را بزنید."
echo ""
echo "  ۲. فایل ‎.env‎ را ویرایش کنید و اسکریپت را دوباره اجرا کنید:"
echo "     • DJANGO_ALLOWED_HOSTS=دامنه-شما.ir"
echo "     • در صورت خطای CSRF: DJANGO_CSRF_TRUSTED_ORIGINS=https://دامنه-شما.ir"
echo "     • DJANGO_SUPERUSER_* برای ساخت مدیر اولیه (از کامنت دربیاید)"
echo ""
echo "  ۳. مسیرهای مهم:"
echo "     • سایت:               https://دامنه-شما/"
echo "     • پنل مدیریت جنگو:    https://دامنه-شما/admin/"
echo "     • ورود پنل اختصاصی:   https://دامنه-شما/panel/"
echo ""
echo "  ۴. گزینه‌های گرافیکی (پس‌زمینه‌ها، لوگو، المان‌ها و شفافیت همه) از"
echo "     همین پنل مدیریت قابل تغییر است؛ نیازی به ویرایش کد نیست."
echo ""
echo "  ۵. راهنمای کامل گام‌به‌گام و عیب‌یابی: deploy/GUIDE-CPANEL-FA.md"
echo ""
echo -e "  برای به‌روزرسانی‌های بعدی: ${C_YELLOW}git pull && bash deploy/deploy_cpanel.sh${C_OFF}"
echo ""
