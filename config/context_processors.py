from martyrs.models import BackgroundImage, SiteElement, SiteSettings


def site_settings(request):
    return {"site_settings": SiteSettings.load()}


def background_assets(request):
    """نقشه کامل اسلات‌های تصویر پس‌زمینه برای استفاده در همه قالب‌ها."""
    return {"background_assets": BackgroundImage.load_map()}


def site_elements(request):
    """نقشه کامل المان‌های گرافیکی سایت (لوگو، آیکون‌ها و تصویر پیش‌فرض شهید)."""
    return {"site_elements": SiteElement.load_map()}
