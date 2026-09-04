import jdatetime
from django import template
from django.utils import timezone


register = template.Library()


@register.filter
def jalali_date(value, fmt="%Y/%m/%d"):
    if not value:
        return ""
    return jdatetime.date.fromgregorian(date=value).strftime(fmt)


@register.filter
def jalali_datetime(value, fmt="%Y/%m/%d - %H:%M"):
    if not value:
        return ""
    if timezone.is_aware(value):
        value = timezone.localtime(value)
    return jdatetime.datetime.fromgregorian(datetime=value).strftime(fmt)


@register.simple_tag
def jalali_year():
    """سال جاری را برای بخش‌های سراسری سایت با تقویم شمسی نمایش می‌دهد."""
    return jdatetime.date.today().strftime("%Y")
