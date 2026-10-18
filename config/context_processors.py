from martyrs.models import BackgroundImage, SiteSettings


def site_settings(request):
    return {"site_settings": SiteSettings.load()}


def background_assets(request):
    """نقشه کامل اسلات‌های تصویر پس‌زمینه برای استفاده در همه قالب‌ها."""
    return {"background_assets": BackgroundImage.load_map()}
