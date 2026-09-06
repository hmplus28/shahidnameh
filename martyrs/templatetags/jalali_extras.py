import jdatetime
from django import template
from django.utils import timezone


register = template.Library()

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


@register.filter
def fa(value):
    """تبدیل اعداد لاتین به فارسی"""
    if value is None:
        return ""
    return str(value).translate(_PERSIAN_DIGITS)


@register.filter
def jalali_date(value, fmt="%Y/%m/%d"):
    if not value:
        return ""
    result = jdatetime.date.fromgregorian(date=value).strftime(fmt)
    return result.translate(_PERSIAN_DIGITS)


@register.filter
def jalali_datetime(value, fmt="%Y/%m/%d - %H:%M"):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    result = jdatetime.datetime.fromgregorian(datetime=value).strftime(fmt)
    return result.translate(_PERSIAN_DIGITS)


@register.simple_tag
def jalali_year():
    """سال جاری را برای بخش‌های سراسری سایت با تقویم شمسی نمایش می‌دهد."""
    return jdatetime.date.today().strftime("%Y").translate(_PERSIAN_DIGITS)
