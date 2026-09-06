from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.urls import reverse
from django.utils.html import format_html
from jalali_date import date2jalali
from jalali_date.admin import ModelAdminJalaliMixin, TabularInlineJalaliMixin

from .models import ComradeMartyr, Martyr, MartyrImage, MartyrInjury, MartyrSection, MartyrVideo, Memory, SiteSettings

ACTION_FLAGS = {1: "افزودن", 2: "ویرایش", 3: "حذف"}


class ChangeLog(LogEntry):
    """نمای فارسی روی گزارش داخلی تغییرات مدیریت."""

    class Meta:
        proxy = True
        verbose_name = "رکورد تاریخچه"
        verbose_name_plural = "تاریخچه تغییرات"
        ordering = ["-action_time"]


@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    """تاریخچه کامل تغییرات محتوای پنل مدیریت."""

    list_display = ("jalali_time", "user", "content_type", "object_link", "action_label", "change_message")
    list_filter = ("action_flag", "content_type", "user")
    search_fields = ("object_repr", "change_message", "user__username")
    date_hierarchy = "action_time"
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="زمان", ordering="action_time")
    def jalali_time(self, obj):
        return date2jalali(obj.action_time).strftime("%Y/%m/%d - %H:%M")

    @admin.display(description="عملیات", ordering="action_flag")
    def action_label(self, obj):
        return ACTION_FLAGS.get(obj.action_flag, str(obj.action_flag))

    @admin.display(description="موضوع")
    def object_link(self, obj):
        if obj.content_type and obj.object_id:
            url = reverse(f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change", args=[obj.object_id])
            return format_html('<a href="{}">{}</a>', url, obj.object_repr)
        return obj.object_repr


class MemoryInline(TabularInlineJalaliMixin, admin.TabularInline):
    model = Memory
    extra = 0
    fields = ("category", "narrator", "text", "recorded_at", "is_featured")
    show_change_link = True


class MartyrImageInline(TabularInlineJalaliMixin, admin.TabularInline):
    model = MartyrImage
    extra = 0
    fields = ("image", "inline_preview", "title", "description", "sort_order")
    readonly_fields = ("inline_preview",)

    @admin.display(description="پیش‌نمایش")
    def inline_preview(self, obj):
        if obj and obj.image:
            return format_html('<img class="js-image-preview admin-image-preview" src="{}" alt="پیش‌نمایش تصویر" />', obj.image.url)
        return format_html('<div class="js-image-preview admin-image-preview admin-image-preview-empty">پس از انتخاب فایل، پیش‌نمایش اینجا ظاهر می‌شود.</div>')

    class Media:
        css = {"all": ("css/admin-image-preview.css",)}
        js = ("js/admin-image-preview.js",)


class MartyrVideoInline(TabularInlineJalaliMixin, admin.TabularInline):
    model = MartyrVideo
    extra = 0
    fields = ("video_file", "external_url", "title", "description", "sort_order")


class MartyrSectionInline(TabularInlineJalaliMixin, admin.TabularInline):
    model = MartyrSection
    extra = 0
    fields = ("title", "content", "sort_order")


class MartyrInjuryInline(TabularInlineJalaliMixin, admin.TabularInline):
    model = MartyrInjury
    extra = 0
    fields = ("injury_date", "description", "sort_order")
    verbose_name = "مجروحیت"
    verbose_name_plural = "سوابق مجروحیت (به دفعات)"


class ComradeMartyrInline(TabularInlineJalaliMixin, admin.TabularInline):
    model = ComradeMartyr
    extra = 0
    fields = ("full_name", "service_place", "memories", "sort_order")
    verbose_name = "همرزم"
    verbose_name_plural = "همرزمان شهید"


@admin.register(Martyr)
class MartyrAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ("full_name", "is_published", "birth_province", "jalali_martyrdom_date", "division", "is_featured")
    list_filter = ("is_published", "is_featured", "birth_province", "martyrdom_date", "division")
    search_fields = ("first_name", "last_name", "last_name_old", "father_name", "birth_city", "birth_province", "division", "brigade", "testament_text")
    readonly_fields = ("jalali_created_at", "jalali_updated_at")
    inlines = (MemoryInline, MartyrImageInline, MartyrVideoInline, MartyrSectionInline, MartyrInjuryInline, ComradeMartyrInline)

    @admin.display(description="تاریخ شهادت", ordering="martyrdom_date")
    def jalali_martyrdom_date(self, obj):
        return date2jalali(obj.martyrdom_date).strftime("%Y/%m/%d") if obj.martyrdom_date else "—"
    fieldsets = (
        ("هویت و زندگی‌نامه", {"fields": (("first_name", "last_name", "last_name_old"), "profile_image", "slug", ("father_name", "mother_name"), ("birth_province", "birth_county"), ("birth_city", "birth_village"), ("birth_date", "birth_date_hijri"), "child_order", ("father_occupation", "mother_occupation"), "scientific_background", "political_positions", "biography_summary")}),
        ("شهادت و جبهه", {"fields": (("martyrdom_date", "martyrdom_place"), "martyrdom_manner", ("burial_county", "burial_village"), ("burial_cemetery", "burial_plot"), ("division", "brigade"), ("battalion", "company"), "platoon", "unit_role", "front_documents")}),
        ("سبک زندگی و اخلاق", {"classes": ("collapse",), "fields": ("family_life", "scientific_life", "velayat", "frontline_life", "social_life", "ethical_traits", "neighborhood_mosque_quran")}),
        ("فعالیت‌ها و سوابق", {"classes": ("collapse",), "fields": ("basij_responsibility", "mosque_activity", "school_activity", "university_activity", "frontline_activity", "teaching_activity", "religious_practice", "ramadan_muharram", "favorite_sports")}),
        ("وصیت‌نامه و سفارش‌ها", {"classes": ("collapse",), "fields": ("testament_text", "testament_prayer", "testament_hijab", "testament_velayat", "testament_islam", "testament_rights_debts", "handwritten_notes")}),
        ("انتشار", {"fields": ("is_published", "is_featured", ("jalali_created_at", "jalali_updated_at"))}),
    )

    @admin.display(description="تاریخ ثبت")
    def jalali_created_at(self, obj):
        return date2jalali(obj.created_at).strftime("%Y/%m/%d - %H:%M")

    @admin.display(description="آخرین ویرایش")
    def jalali_updated_at(self, obj):
        return date2jalali(obj.updated_at).strftime("%Y/%m/%d - %H:%M")


@admin.register(Memory)
class MemoryAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ("martyr", "category", "narrator", "jalali_recorded_at", "is_featured")
    list_filter = ("category", "is_featured", "recorded_at")
    search_fields = ("martyr__first_name", "martyr__last_name", "narrator", "text")
    autocomplete_fields = ("martyr",)

    @admin.display(description="تاریخ ثبت", ordering="recorded_at")
    def jalali_recorded_at(self, obj):
        return date2jalali(obj.recorded_at).strftime("%Y/%m/%d") if obj.recorded_at else "—"


@admin.register(MartyrImage)
class MartyrImageAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ("thumbnail", "martyr", "title", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("martyr__first_name", "martyr__last_name", "title")
    autocomplete_fields = ("martyr",)
    fields = ("martyr", "image", "live_preview", "title", "description", "sort_order")
    readonly_fields = ("live_preview",)

    @admin.display(description="پیش‌نمایش")
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:8px" />', obj.image.url)
        return "—"

    @admin.display(description="پیش‌نمایش زنده")
    def live_preview(self, obj):
        if obj and obj.image:
            return format_html('<img id="image-live-preview" class="js-image-preview admin-image-preview" src="{}" alt="پیش‌نمایش تصویر" />', obj.image.url)
        return format_html('<div id="image-live-preview" class="js-image-preview admin-image-preview admin-image-preview-empty">پس از انتخاب فایل، پیش‌نمایش اینجا ظاهر می‌شود.</div>')

    class Media:
        css = {"all": ("css/admin-image-preview.css",)}
        js = ("js/admin-image-preview.js",)


@admin.register(MartyrSection)
class MartyrSectionAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ("title", "martyr", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("title", "content", "martyr__first_name", "martyr__last_name")
    autocomplete_fields = ("martyr",)


@admin.register(MartyrVideo)
class MartyrVideoAdmin(ModelAdminJalaliMixin, admin.ModelAdmin):
    list_display = ("title", "martyr", "has_source", "sort_order")
    list_editable = ("sort_order",)
    search_fields = ("martyr__first_name", "martyr__last_name", "title", "description")
    autocomplete_fields = ("martyr",)

    @admin.display(boolean=True, description="فایل یا پیوند")
    def has_source(self, obj):
        return bool(obj.video_file or obj.external_url)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("music_enabled", "music_url")
    fieldsets = (
        ("موزیک پس‌زمینه", {"fields": ("music_enabled", "music_url")}),
    )
