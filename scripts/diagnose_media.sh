#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════
#  شهیدنامه — تشخیص وضعیت رسانه‌ها (media)
#  «چرا عکس‌های آپلودی در سایت ۴۰۴ می‌شوند؟»
#
#  اجرا:
#      bash scripts/diagnose_media.sh
#  اگر پایتون venv سی‌پنل خودکار پیدا نشد:
#      SHAHIDNAMEH_PYTHON=~/virtualenv/.../bin/python bash scripts/diagnose_media.sh
#
#  این اسکریپت فقط «می‌خواند» و چیزی را تغییر نمی‌دهد.
# ════════════════════════════════════════════════════════════════
set -uo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

say()  { printf 'ℹ  %s\n' "$*"; }
ok()   { printf '✔ %s\n' "$*"; }
bad()  { printf '✖ %s\n' "$*"; }
line() { printf '═══════════════════════════════════════════════════════════════\n'; }

line
echo "  شهیدنامه — تشخیص رسانه‌ها (media)"
line

# ── یافتن پایتون venv سی‌پنل ─────────────────────────────────────────
VENV_PY="${SHAHIDNAMEH_PYTHON:-}"
if [ -z "$VENV_PY" ]; then
    for c in "$HOME/virtualenv/public_html/$(basename "$PROJECT_DIR")"/*/bin/python \
             "$HOME/virtualenv/$(basename "$PROJECT_DIR")"/*/bin/python ; do
        [ -x "$c" ] && VENV_PY="$c" && break
    done
fi
if [ -z "$VENV_PY" ]; then
    VENV_PY="$(command -v python3 2>/dev/null || true)"
    [ -n "$VENV_PY" ] && say "venv سی‌پنل پیدا نشد؛ از پایتون سیستم استفاده می‌شود: $VENV_PY"
fi
if [ -z "$VENV_PY" ]; then
    bad "هیچ پایتونی پیدا نشد!"
    exit 1
fi
ok "پایتون: $VENV_PY"

# ── ۱) فایل‌های روی دیسک ─────────────────────────────────────────────
echo
say "۱) همهٔ فایل‌های زیر media/ روی دیسک:"
if [ -d media ]; then
    ls -ld media | sed 's/^/   /'
    n="$(find media -type f | wc -l)"
    if [ "$n" -eq 0 ]; then
        bad "پوشه media وجود دارد اما هیچ فایلی داخلش نیست!"
    else
        find media -type f -printf '   %10s  %p\n' | sort -k3
        ok "جمعاً $n فایل روی دیسک."
    fi
    say "فضای دیسک:"
    df -h . | sed 's/^/   /'
else
    bad "پوشه media اصلاً وجود ندارد!"
fi

# ── ۲) تنظیمات جنگو و ردیف‌های رسانه در دیتابیس ──────────────────────
echo
PY_OUT="$(mktemp /tmp/shahidnameh_media_XXXXXX.txt)"
say "۲) تنظیمات جنگو و مقایسهٔ ردیف‌های دیتابیس با دیسک:"
"$VENV_PY" manage.py shell -v 0 <<'PYEOF' | tee "$PY_OUT" | grep -v '^MISSING_FILE='
from django.conf import settings
from django.apps import apps
from django.db import models as djm
from pathlib import Path
import os

root = Path(settings.MEDIA_ROOT)
print(f"   MEDIA_ROOT = {settings.MEDIA_ROOT}")
print(f"   MEDIA_URL  = {settings.MEDIA_URL}")
print(f"   DEBUG      = {settings.DEBUG}")
print(f"   MEDIA_ROOT وجود دارد: {root.exists()} | خواندنی: {os.access(root, os.R_OK)} | نوشتنی: {os.access(root, os.W_OK)}")
print()

total = missing = 0
for model in apps.get_models():
    for field in model._meta.fields:
        if isinstance(field, (djm.FileField, djm.ImageField)):
            qs = model.objects.exclude(**{field.name: ""}).exclude(**{f"{field.name}__isnull": True})
            for obj in qs:
                name = str(getattr(obj, field.name))
                total += 1
                p = root / name
                if p.exists():
                    print(f"   OK       {model.__name__}.{field.name} pk={obj.pk}: {name}")
                else:
                    missing += 1
                    print(f"   MISSING  {model.__name__}.{field.name} pk={obj.pk}: {name}")
                    print(f"MISSING_FILE={Path(name).name}")
                    cur = root
                    for part in Path(name).parts:
                        cur = cur / part
                        if not cur.exists():
                            print(f"             ← اولین مسیر ناموجود: {cur}")
                            break
print()
print(f"   جمع ردیف‌های رسانه در دیتابیس: {total} | غایب روی دیسک: {missing}")
if missing:
    print()
    print("   ▶ یعنی: عکس در دیتابیس ثبت شده اما فایلش روی دیسک نیست.")
    print("     راه‌حل: در پنل (ادمین یا پنل اختصاصی) همان عکس‌ها را دوباره آپلود کنید؛")
    print("     متن‌ها و بقیهٔ اطلاعات سالم می‌مانند.")
PYEOF

# ── ۳) جستجوی فایل‌های گم‌شده در کل هوم ──────────────────────────────
# اگر پروژه قبلاً در مسیر دیگری نصب بوده (BASE_DIR قدیمی)، فایل‌های آپلودی
# همان‌جا جا مانده‌اند و فقط باید برگردند.
MISSING_NAMES="$(sed -n 's/^MISSING_FILE=//p' "$PY_OUT" | sort -u)"
rm -f "$PY_OUT"
if [ -n "$MISSING_NAMES" ]; then
    echo
    say "۳) جستجوی فایل‌های گم‌شده در کل هوم (شاید در مسیر قدیمی پروژه جا مانده‌اند):"
    found_any=0
    while IFS= read -r name; do
        [ -z "$name" ] && continue
        hits="$(find "$HOME" -type f -name "$name" -not -path "$PROJECT_DIR/*" 2>/dev/null | head -5)"
        if [ -n "$hits" ]; then
            found_any=1
            ok "پیدا شد: $name"
            printf '%s\n' "$hits" | sed 's/^/      /'
        else
            bad "هیچ‌جا پیدا نشد: $name"
        fi
    done <<< "$MISSING_NAMES"
    if [ "$found_any" -eq 1 ]; then
        echo
        say "▶ فایل‌ها در مسیر دیگری از هاست پیدا شدند! کافیست به دستیار بگویید"
        say "  تا دستور کپی به media/ همین پروژه را برایتان بنویسد."
    fi
fi

echo
line
say "پایان گزارش — لطفاً کل خروجی بالا را کپی و برای دستیار بفرستید."
line
