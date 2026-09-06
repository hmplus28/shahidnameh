from pathlib import Path
import re

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.templatetags.static import static

from .forms import MartyrDirectoryFilterForm
from .models import Martyr, Memory, SiteSettings


def home(request):
    quick_query = request.GET.get("q", "").strip()
    if quick_query:
        from django.urls import reverse
        return redirect(f"{reverse('martyrs:directory')}?q={quick_query}")

    published = Martyr.objects.filter(is_published=True)
    context = {
        "featured_martyrs": published.filter(is_featured=True)[:10],
        "latest_memories": Memory.objects.select_related("martyr").filter(martyr__is_published=True).order_by("-created_at")[:10],
        "stats": {
            "martyrs": published.count(),
            "memories": Memory.objects.filter(martyr__is_published=True).count(),
            "provinces": published.exclude(birth_province="").values("birth_province").distinct().count(),
        },
    }
    return render(request, "martyrs/home.html", context)


def _filter_options():
    provinces = Martyr.objects.exclude(birth_province="").values_list("birth_province", flat=True).distinct().order_by("birth_province")
    divisions = list(Martyr.objects.exclude(division="").values_list("division", flat=True).distinct())
    brigades = list(Martyr.objects.exclude(brigade="").values_list("brigade", flat=True).distinct())
    units = list(dict.fromkeys(divisions + brigades))
    return provinces, units


def _filtered_martyrs(request, provinces, units):
    filter_form = MartyrDirectoryFilterForm(request.GET or None, provinces=provinces, units=units)
    martyrs = Martyr.objects.filter(is_published=True)
    if not filter_form.is_bound:
        return martyrs.distinct(), filter_form
    if not filter_form.is_valid():
        return martyrs.none(), filter_form

    params = filter_form.cleaned_data
    if params["q"]:
        martyrs = martyrs.filter(Q(first_name__icontains=params["q"]) | Q(last_name__icontains=params["q"]) | Q(father_name__icontains=params["q"]))
    if params["province"]:
        martyrs = martyrs.filter(birth_province=params["province"])
    if params["city"]:
        martyrs = martyrs.filter(birth_city__icontains=params["city"])
    if params["unit"]:
        martyrs = martyrs.filter(Q(division=params["unit"]) | Q(brigade=params["unit"]))
    if params["martyrdom_from"]:
        martyrs = martyrs.filter(martyrdom_date__gte=params["martyrdom_from"])
    if params["martyrdom_to"]:
        martyrs = martyrs.filter(martyrdom_date__lte=params["martyrdom_to"])
    if params["will"]:
        martyrs = martyrs.filter(testament_text__icontains=params["will"])
    if params["memory"]:
        martyrs = martyrs.filter(memories__category=params["memory"])
    return martyrs.distinct(), filter_form


def martyr_directory(request):
    provinces, units = _filter_options()
    martyrs, filter_form = _filtered_martyrs(request, provinces, units)
    published = Martyr.objects.filter(is_published=True)
    context = {
        "martyrs": martyrs.filter(is_published=True),
        "filter_form": filter_form,
        "featured_martyrs": published.filter(is_featured=True),
        "latest_martyrs": published.order_by("-created_at"),
        "recent_martyrs": published.exclude(martyrdom_date=None).order_by("-martyrdom_date"),
    }
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(request, "martyrs/partials/martyr_results.html", context)
    return render(request, "martyrs/martyr_directory.html", context)


def martyr_detail(request, slug):
    queryset = Martyr.objects.prefetch_related("memories", "images", "videos", "sections", "injuries", "comrades")
    is_staff = request.user.is_staff
    if not is_staff:
        queryset = queryset.filter(is_published=True)
    martyr = get_object_or_404(queryset, slug=slug)
    memories = martyr.memories.all()
    hero_image = next((img for img in martyr.images.all() if img.image), None)
    context = {
        "martyr": martyr,
        "is_preview": not martyr.is_published and is_staff,
        "hero_image": hero_image,
        "memories": memories,
        "memory_groups": {category: memories.filter(category=category) for category, _ in Memory.Category.choices},
        "memory_categories": Memory.Category.choices,
        "images": martyr.images.all(),
        "videos": martyr.videos.all(),
        "sections": martyr.sections.all(),
        "injuries": martyr.injuries.all(),
        "comrades": martyr.comrades.all(),
    }
    return render(request, "martyrs/martyr_detail.html", context)


def offline(request):
    return render(request, "offline.html", status=200)


def service_worker(request):
    """ارسال سرویس‌ورکر از ریشه دامنه برای پوشش تمام صفحه‌های Django."""
    worker_path = Path(settings.BASE_DIR) / "static" / "js" / "service-worker.js"
    source = worker_path.read_text(encoding="utf-8")

    def to_hashed(match):
        try:
            return '"{}"'.format(static(match.group(1)))
        except Exception:
            return match.group(0)

    source = re.sub(r'"/static/([^"]+)"', to_hashed, source)
    response = HttpResponse(source, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


def robots_txt(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    lines = ["User-agent: *", "Disallow: /admin/", "Disallow: /media/", f"Sitemap: {sitemap_url}"]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def ziyaratnama(request):
    return render(request, "martyrs/ziyaratnama.html")
