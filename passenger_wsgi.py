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
