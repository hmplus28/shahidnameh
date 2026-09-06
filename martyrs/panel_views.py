from functools import wraps

from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model, views as auth_views
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme

from .models import ComradeMartyr, Martyr, MartyrImage, MartyrInjury, MartyrSection, MartyrVideo, Memory
from .panel_forms import (
    ROLE_ADMIN,
    ROLE_AUTHOR,
    ComradeMartyrForm,
    MartyrForm,
    MartyrImageForm,
    MartyrInjuryForm,
    MartyrSectionForm,
    MartyrVideoForm,
    MemoryForm,
    PanelUserForm,
    ensure_role_groups,
)

User = get_user_model()


def panel_access(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_active or not request.user.is_staff:
            return redirect("martyrs:panel_login")
        return view(request, *args, **kwargs)

    return wrapped


def can_edit(request):
    return request.user.is_superuser or request.user.has_perm("martyrs.change_martyr")


class PanelLoginView(auth_views.LoginView):
    template_name = "panel/login.html"
    redirect_authenticated_user = True

    def _has_panel_access(self, user):
        return user.is_active and user.is_staff

    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated and not self._has_panel_access(user):
            return str(reverse_lazy("martyrs:home"))
        next_url = self.get_redirect_url()
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}):
            return next_url
        return str(reverse_lazy("martyrs:panel_home"))

    def form_valid(self, form):
        user = form.get_user()
        if not self._has_panel_access(user):
            messages.error(self.request, "شما دسترسی ورود به پنل مدیریت را ندارید.")
            return redirect("martyrs:home")
        return super().form_valid(form)


def _log(user, obj, flag, message):
    LogEntry.objects.log_action(
        user_id=user.pk,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=flag,
        change_message=message,
    )


@panel_access
def panel_home(request):
    martyrs = Martyr.objects.all()
    context = {
        "active_section": "dashboard",
        "stats": {
            "martyrs_total": martyrs.count(),
            "martyrs_published": martyrs.filter(is_published=True).count(),
            "martyrs_featured": martyrs.filter(is_featured=True).count(),
            "memories": Memory.objects.count(),
            "images": MartyrImage.objects.count(),
            "videos": MartyrVideo.objects.count(),
        },
        "recent_martyrs": martyrs.order_by("-updated_at")[:6],
        "recent_logs": LogEntry.objects.select_related("user", "content_type").order_by("-action_time")[:8],
    }
    return render(request, "panel/dashboard.html", context)


@panel_access
def martyr_list(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    martyrs = Martyr.objects.all()
    if query:
        martyrs = martyrs.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query)
            | Q(last_name_old__icontains=query) | Q(father_name__icontains=query)
            | Q(division__icontains=query) | Q(brigade__icontains=query)
        )
    if status == "published":
        martyrs = martyrs.filter(is_published=True)
    elif status == "draft":
        martyrs = martyrs.filter(is_published=False)
    elif status == "featured":
        martyrs = martyrs.filter(is_featured=True)

    page = Paginator(martyrs.order_by("-updated_at"), 12).get_page(request.GET.get("page"))
    context = {
        "active_section": "martyrs",
        "page_obj": page,
        "query": query,
        "status": status,
        "can_edit": can_edit(request),
    }
    return render(request, "panel/martyr_list.html", context)


@panel_access
def martyr_create(request):
    if not can_edit(request):
        messages.error(request, "شما اجازه ثبت و ویرایش محتوا را ندارید.")
        return redirect("martyrs:panel_martyr_list")
    form = MartyrForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        martyr = form.save()
        _log(request.user, martyr, ADDITION, "ثبت از پنل اختصاصی")
        messages.success(request, f"پرونده «{martyr.full_name}» ثبت شد.")
        return redirect("martyrs:panel_martyr_edit", pk=martyr.pk)
    return render(
        request,
        "panel/martyr_form.html",
        {"form": form, "field_groups": form.grouped_fields(), "can_edit": True, "active_section": "martyrs", "is_new": True},
    )


@panel_access
def martyr_edit(request, pk):
    martyr = get_object_or_404(Martyr, pk=pk)
    readonly = not can_edit(request)
    form = MartyrForm(request.POST or None, instance=martyr)
    if request.method == "POST":
        if readonly:
            messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
            return redirect("martyrs:panel_martyr_edit", pk=pk)
        if form.is_valid():
            martyr = form.save()
            _log(request.user, martyr, CHANGE, "ویرایش از پنل اختصاصی")
            messages.success(request, "تغییرات ذخیره شد.")
            return redirect("martyrs:panel_martyr_edit", pk=pk)

    context = {
        "form": form,
        "field_groups": form.grouped_fields(),
        "martyr": martyr,
        "readonly": readonly,
        "can_edit": not readonly,
        "active_section": "martyrs",
        "memories": martyr.memories.all(),
        "memory_form": MemoryForm(),
        "images": martyr.images.all(),
        "image_form": MartyrImageForm(),
        "videos": martyr.videos.all(),
        "video_form": MartyrVideoForm(),
        "sections": martyr.sections.all(),
        "section_form": MartyrSectionForm(),
        "injuries": martyr.injuries.all(),
        "injury_form": MartyrInjuryForm(),
        "comrades": martyr.comrades.all(),
        "comrade_form": ComradeMartyrForm(),
    }
    return render(request, "panel/martyr_form.html", context)


@panel_access
def martyr_toggle_flag(request, pk, flag):
    martyr = get_object_or_404(Martyr, pk=pk)
    if not can_edit(request):
        messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
        return redirect("martyrs:panel_martyr_edit", pk=pk)
    if request.method == "POST":
        if flag == "publish":
            martyr.is_published = not martyr.is_published
            label = "انتشار" if martyr.is_published else "پیش‌نویس شدن"
        else:
            martyr.is_featured = not martyr.is_featured
            label = "شاخص شدن" if martyr.is_featured else "خروج از شاخص‌ها"
        martyr.save(update_fields=["is_published", "is_featured"] if flag == "publish" else ["is_featured"])
        _log(request.user, martyr, CHANGE, f"{label} از پنل اختصاصی")
        messages.success(request, f"«{martyr.full_name}» {label}.")
    return redirect("martyrs:panel_martyr_list")


@panel_access
def martyr_delete(request, pk):
    martyr = get_object_or_404(Martyr, pk=pk)
    if not can_edit(request):
        messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
        return redirect("martyrs:panel_martyr_list")
    if request.method == "POST":
        repr_name = str(martyr)
        _log(request.user, martyr, DELETION, "حذف از پنل اختصاصی")
        martyr.delete()
        messages.success(request, f"پرونده «{repr_name}» حذف شد.")
        return redirect("martyrs:panel_martyr_list")
    return render(request, "panel/martyr_delete.html", {"martyr": martyr, "active_section": "martyrs"})


@panel_access
def section_add(request, martyr_pk):
    martyr = get_object_or_404(Martyr, pk=martyr_pk)
    if not can_edit(request):
        messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
        return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)
    if request.method == "POST":
        form = MartyrSectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.martyr = martyr
            section.save()
            _log(request.user, section, ADDITION, f"افزودن بخش «{section.title}» برای {martyr.full_name}")
            messages.success(request, "بخش جدید افزوده شد.")
        else:
            messages.error(request, "افزودن بخش ناموفق بود؛ عنوان و متن را بررسی کنید.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def section_delete(request, pk):
    section = get_object_or_404(MartyrSection.objects.select_related("martyr"), pk=pk)
    martyr_pk = section.martyr_id
    if can_edit(request) and request.method == "POST":
        _log(request.user, section, DELETION, "حذف بخش سفارشی از پنل اختصاصی")
        section.delete()
        messages.success(request, "بخش حذف شد.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def memory_add(request, martyr_pk):
    martyr = get_object_or_404(Martyr, pk=martyr_pk)
    if not can_edit(request):
        messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
        return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)
    if request.method == "POST":
        form = MemoryForm(request.POST)
        if form.is_valid():
            memory = form.save(commit=False)
            memory.martyr = martyr
            memory.save()
            _log(request.user, memory, ADDITION, f"افزودن خاطره برای {martyr.full_name}")
            messages.success(request, "خاطره ثبت شد.")
        else:
            messages.error(request, "ثبت خاطره ناموفق بود؛ فیلدها را بررسی کنید.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def memory_delete(request, pk):
    memory = get_object_or_404(Memory.objects.select_related("martyr"), pk=pk)
    martyr_pk = memory.martyr_id
    if can_edit(request) and request.method == "POST":
        _log(request.user, memory, DELETION, "حذف خاطره از پنل اختصاصی")
        memory.delete()
        messages.success(request, "خاطره حذف شد.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def image_upload(request, martyr_pk):
    martyr = get_object_or_404(Martyr, pk=martyr_pk)
    if not can_edit(request):
        messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
        return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)
    if request.method == "POST":
        form = MartyrImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.martyr = martyr
            image.save()
            _log(request.user, image, ADDITION, f"افزودن تصویر برای {martyr.full_name}")
            messages.success(request, "تصویر بارگذاری شد.")
        else:
            messages.error(request, "بارگذاری تصویر ناموفق بود؛ فرمت و حجم فایل را بررسی کنید.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def image_delete(request, pk):
    image = get_object_or_404(MartyrImage.objects.select_related("martyr"), pk=pk)
    martyr_pk = image.martyr_id
    if can_edit(request) and request.method == "POST":
        _log(request.user, image, DELETION, "حذف تصویر از پنل اختصاصی")
        image.image.delete(save=False)
        image.delete()
        messages.success(request, "تصویر حذف شد.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def video_add(request, martyr_pk):
    martyr = get_object_or_404(Martyr, pk=martyr_pk)
    if not can_edit(request):
        messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
        return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)
    if request.method == "POST":
        form = MartyrVideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.martyr = martyr
            video.save()
            _log(request.user, video, ADDITION, f"افزودن ویدئو برای {martyr.full_name}")
            messages.success(request, "ویدئو ثبت شد.")
        else:
            messages.error(request, "ثبت ویدئو ناموفق بود؛ یکی از فایل یا پیوند را تکمیل کنید.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def video_delete(request, pk):
    video = get_object_or_404(MartyrVideo.objects.select_related("martyr"), pk=pk)
    martyr_pk = video.martyr_id
    if can_edit(request) and request.method == "POST":
        _log(request.user, video, DELETION, "حذف ویدئو از پنل اختصاصی")
        video.video_file.delete(save=False)
        video.delete()
        messages.success(request, "ویدئو حذف شد.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def injury_add(request, martyr_pk):
    martyr = get_object_or_404(Martyr, pk=martyr_pk)
    if not can_edit(request):
        messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
        return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)
    if request.method == "POST":
        form = MartyrInjuryForm(request.POST)
        if form.is_valid():
            injury = form.save(commit=False)
            injury.martyr = martyr
            injury.save()
            _log(request.user, injury, ADDITION, f"افزودن مجروحیت برای {martyr.full_name}")
            messages.success(request, "مجروحیت ثبت شد.")
        else:
            messages.error(request, "ثبت مجروحیت ناموفق بود؛ فیلدها را بررسی کنید.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def injury_delete(request, pk):
    injury = get_object_or_404(MartyrInjury.objects.select_related("martyr"), pk=pk)
    martyr_pk = injury.martyr_id
    if can_edit(request) and request.method == "POST":
        _log(request.user, injury, DELETION, "حذف مجروحیت از پنل اختصاصی")
        injury.delete()
        messages.success(request, "مجروحیت حذف شد.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def comrade_add(request, martyr_pk):
    martyr = get_object_or_404(Martyr, pk=martyr_pk)
    if not can_edit(request):
        messages.error(request, "نقش شما فقط امکان مشاهده دارد.")
        return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)
    if request.method == "POST":
        form = ComradeMartyrForm(request.POST)
        if form.is_valid():
            comrade = form.save(commit=False)
            comrade.martyr = martyr
            comrade.save()
            _log(request.user, comrade, ADDITION, f"افزودن همرزم برای {martyr.full_name}")
            messages.success(request, "همرزم ثبت شد.")
        else:
            messages.error(request, "ثبت همرزم ناموفق بود؛ فیلدها را بررسی کنید.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def comrade_delete(request, pk):
    comrade = get_object_or_404(ComradeMartyr.objects.select_related("martyr"), pk=pk)
    martyr_pk = comrade.martyr_id
    if can_edit(request) and request.method == "POST":
        _log(request.user, comrade, DELETION, "حذف همرزم از پنل اختصاصی")
        comrade.delete()
        messages.success(request, "همرزم حذف شد.")
    return redirect("martyrs:panel_martyr_edit", pk=martyr_pk)


@panel_access
def change_logs(request):
    logs = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")
    page = Paginator(logs, 25).get_page(request.GET.get("page"))
    return render(request, "panel/logs.html", {"page_obj": page, "active_section": "logs"})


def superuser_only(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "این بخش فقط برای مدیر کل (سوپریوزر) قابل دسترسی است.")
            return redirect("martyrs:panel_home")
        return view(request, *args, **kwargs)

    return wrapped


@panel_access
@superuser_only
def user_list(request):
    from django.contrib.auth.models import User

    def _role(user):
        if user.is_superuser:
            return "سوپریوزر", "is-gold"
        if not user.is_active:
            return "غیرفعال", "is-danger-tag"
        if user.has_perm("martyrs.delete_martyr"):
            return "مدیر محتوا", "is-ok"
        if user.is_staff:
            return "نویسنده", "is-view"
        return "بدون نقش", ""

    users = [
        {"obj": user, "role": _role(user)}
        for user in User.objects.order_by("-is_superuser", "-is_active", "username")
    ]
    return render(request, "panel/user_list.html", {"users": users, "active_section": "users"})


@panel_access
@superuser_only
def user_create(request):
    form = PanelUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        from django.contrib.auth.models import User

        data = form.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            password=data["password"],
            is_staff=True,
        )
        groups = ensure_role_groups()
        user.groups.add(groups[data["role"]])
        if data["role"] == ROLE_ADMIN:
            user.user_permissions.set(groups[ROLE_ADMIN].permissions.all())
        _log(request.user, user, ADDITION, f"ایجاد کاربر با نقش {data['role']} از پنل")
        messages.success(request, f"کاربر «{user.username}» ساخته شد.")
        return redirect("martyrs:panel_user_list")
    return render(request, "panel/user_form.html", {"form": form, "is_new": True, "active_section": "users"})


@panel_access
@superuser_only
def user_edit(request, pk):
    from django.contrib.auth.models import User

    user = get_object_or_404(User, pk=pk)
    current_role = ROLE_ADMIN if user.has_perm("martyrs.delete_martyr") else ROLE_AUTHOR
    form = PanelUserForm(
        request.POST or None,
        initial={"username": user.username, "first_name": user.first_name, "last_name": user.last_name, "role": current_role, "pk": user.pk},
        is_edit=True,
    )
    if request.method == "POST":
        if not user.is_superuser or user.pk == request.user.pk:
            if form.is_valid():
                data = form.cleaned_data
                user.username = data["username"]
                user.first_name = data["first_name"]
                user.last_name = data["last_name"]
                if data["password"]:
                    user.set_password(data["password"])
                groups = ensure_role_groups()
                user.groups.clear()
                user.user_permissions.clear()
                user.groups.add(groups[data["role"]])
                if data["role"] == ROLE_ADMIN:
                    user.user_permissions.set(groups[ROLE_ADMIN].permissions.all())
                user.save()
                _log(request.user, user, CHANGE, "ویرایش کاربر از پنل")
                messages.success(request, "تغییرات کاربر ذخیره شد.")
                return redirect("martyrs:panel_user_list")
        else:
            messages.error(request, "امکان ویرایش سایر سوپریوزرها وجود ندارد.")
    return render(request, "panel/user_form.html", {"form": form, "target_user": user, "is_new": False, "active_section": "users"})


@panel_access
@superuser_only
def user_toggle_active(request, pk):
    from django.contrib.auth.models import User

    target = get_object_or_404(User, pk=pk)
    if request.method == "POST" and target.pk != request.user.pk and not target.is_superuser:
        target.is_active = not target.is_active
        target.save(update_fields=["is_active"])
        state = "فعال" if target.is_active else "غیرفعال"
        messages.success(request, f"حساب «{target.username}» {state} شد.")
    return redirect("martyrs:panel_user_list")


@panel_access
@superuser_only
def user_delete(request, pk):
    from django.contrib.auth.models import User

    target = get_object_or_404(User, pk=pk)
    if request.method == "POST" and target.pk != request.user.pk and not target.is_superuser:
        name = target.username
        target.delete()
        messages.success(request, f"کاربر «{name}» حذف شد.")
    return redirect("martyrs:panel_user_list")


@panel_access
@superuser_only
def site_settings(request):
    from .models import SiteSettings
    from .panel_forms import SiteSettingsForm

    obj = SiteSettings.load()
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "تنظیمات سایت ذخیره شد.")
            return redirect("martyrs:panel_site_settings")
    else:
        form = SiteSettingsForm(instance=obj)
    return render(request, "panel/site_settings.html", {"form": form})


@panel_access
@superuser_only
def clear_service_worker(request):
    js = """
(function(){
  if('serviceWorker' in navigator){
    navigator.serviceWorker.getRegistrations().then(function(regs){
      regs.forEach(function(r){ r.unregister(); });
    });
  }
  if('caches' in window){
    caches.keys().then(function(names){
      names.forEach(function(n){ caches.delete(n); });
    });
  }
  document.open();
  document.write('<html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>پاک‌سازی</title></head><body style="display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif;background:#f3f6f1;color:#173f3d;text-align:center"><div><h1>✅ سرویس‌ورکر و کش پاک شد</h1><p>صفحه را ببندید و دوباره سایت را باز کنید.</p></div></body></html>');
  document.close();
})();
"""
    return HttpResponse(js, content_type="application/javascript; charset=utf-8")
