from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve


admin.site.site_header = "مدیریت شهیدنامه"
admin.site.site_title = "پنل شهیدنامه"
admin.site.index_title = "مدیریت شهدا، خاطرات و رسانه‌ها"


def serve_media(request, path):
    """سرو فایل‌های آپلودی (MEDIA) در همهٔ حالت‌ها — حتی DEBUG=False.

    روی هاست اشتراکی cPanel، آپاچی/Passenger درخواست ‎/media/…‎ را به خودِ
    جنگو می‌فرستد و بدون این مسیر همهٔ عکس‌های آپلودی ۴۰۴ می‌شوند. به‌جای
    قفل‌کردن document_root هنگام import، هر بار از تنظیمات خوانده می‌شود
    (برای تست‌ها و تغییر تنظیمات درست‌تر است).
    """
    return serve(request, path, document_root=settings.MEDIA_ROOT)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("martyrs.urls", namespace="martyrs")),
    # ثبت همیشگی: اگر آپاچی خودش فایل را از دیسک سرو کند که بهتر، وگرنه جنگو
    re_path(r"^media/(?P<path>.*)$", serve_media, name="media"),
]
