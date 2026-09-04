from django import forms
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget

from .models import ComradeMartyr, Martyr, MartyrImage, MartyrInjury, MartyrSection, MartyrVideo, Memory


class MartyrSectionForm(forms.ModelForm):
    sort_order = forms.IntegerField(required=False, initial=0, label="ترتیب نمایش")

    class Meta:
        model = MartyrSection
        fields = ("title", "content", "sort_order")

    def clean_sort_order(self):
        return self.cleaned_data.get("sort_order") or 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} panel-input".strip()
        self.fields["content"].widget.attrs["rows"] = 4


class MartyrForm(forms.ModelForm):
    birth_date = JalaliDateField(required=False, label="تاریخ تولد", widget=AdminJalaliDateWidget)
    martyrdom_date = JalaliDateField(required=False, label="تاریخ شهادت", widget=AdminJalaliDateWidget)

    class Meta:
        model = Martyr
        exclude = ("slug", "created_at", "updated_at")
        widgets = {
            "biography_summary": forms.Textarea(attrs={"rows": 4}),
            "testament_text": forms.Textarea(attrs={"rows": 6}),
        }

    FIELDSETS = [
        ("هویت", ["first_name", "last_name", "last_name_old", "profile_image", "father_name", "mother_name"]),
        ("تولد", ["birth_date", "birth_date_hijri", "birth_province", "birth_county", "birth_city", "birth_village", "child_order"]),
        ("خانواده و تحصیل", ["father_occupation", "mother_occupation", "scientific_background", "political_positions"]),
        ("زندگی‌نامه", ["biography_summary"]),
        ("شهادت و محل دفن", ["martyrdom_date", "martyrdom_place", "martyrdom_manner", "burial_county", "burial_village", "burial_cemetery", "burial_plot"]),
        ("یگان و جبهه (لشکر، تیپ، گردان، گروهان، دسته)", ["division", "brigade", "battalion", "company", "platoon", "unit_role", "front_documents"]),
        ("سبک زندگی و اخلاق", ["family_life", "scientific_life", "velayat", "frontline_life", "social_life", "ethical_traits", "neighborhood_mosque_quran"]),
        ("فعالیت‌ها", ["basij_responsibility", "mosque_activity", "school_activity", "university_activity", "frontline_activity", "teaching_activity", "religious_practice", "ramadan_muharram", "favorite_sports"]),
        ("وصیت‌نامه", ["testament_text", "testament_prayer", "testament_hijab", "testament_velayat", "testament_islam", "testament_rights_debts", "handwritten_notes"]),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} panel-input".strip()
        for name in ("is_published", "is_featured"):
            if name in self.fields:
                self.fields[name].widget.attrs["class"] = "panel-check"
                self.fields[name].widget.attrs.pop("placeholder", None)

    def grouped_fields(self):
        result = []
        for title, names in self.FIELDSETS:
            items = []
            for name in names:
                field = self[name]
                items.append({
                    "field": field,
                    "wide": isinstance(field.field.widget, forms.Textarea),
                })
            result.append((title, items))
        return result


class MartyrInjuryForm(forms.ModelForm):
    injury_date = JalaliDateField(required=False, label="تاریخ مجروحیت", widget=AdminJalaliDateWidget)

    class Meta:
        model = MartyrInjury
        fields = ("injury_date", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} panel-input".strip()
        self.fields["description"].widget = forms.Textarea(attrs={"rows": 3, "class": "panel-input"})


class ComradeMartyrForm(forms.ModelForm):
    class Meta:
        model = ComradeMartyr
        fields = ("full_name", "service_place", "memories")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} panel-input".strip()
        self.fields["memories"].widget = forms.Textarea(attrs={"rows": 3, "class": "panel-input"})


class MemoryForm(forms.ModelForm):
    recorded_at = JalaliDateField(required=False, label="تاریخ ثبت خاطره", widget=AdminJalaliDateWidget)

    class Meta:
        model = Memory
        fields = ("category", "narrator", "text", "recorded_at", "is_featured")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} panel-input".strip()
        self.fields["text"].widget.attrs["rows"] = 4


class MartyrImageForm(forms.ModelForm):
    class Meta:
        model = MartyrImage
        fields = ("image", "title", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} panel-input".strip()


class MartyrVideoForm(forms.ModelForm):
    class Meta:
        model = MartyrVideo
        fields = ("title", "video_file", "external_url", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} panel-input".strip()


ROLE_AUTHOR = "author"
ROLE_ADMIN = "admin"

ROLE_CHOICES = (
    (ROLE_AUTHOR, "نویسنده (ثبت و ویرایش محتوا)"),
    (ROLE_ADMIN, "مدیر (دسترسی کامل محتوا)"),
)


def ensure_role_groups():
    """ساخت گروه‌های نقش و تخصیص مجوزهای متناسب، در صورت نبود."""
    from django.contrib.auth.models import Group, Permission

    content_models = ["martyr", "memory", "martyrimage", "martyrsection", "martyrvideo"]
    author_group, _ = Group.objects.get_or_create(name="نویسنده")
    admin_group, _ = Group.objects.get_or_create(name="مدیر محتوا")
    author_perms = Permission.objects.filter(
        content_type__app_label="martyrs",
        codename__in=[f"{action}_{model}" for model in content_models for action in ("view", "add", "change")],
    )
    admin_perms = Permission.objects.filter(
        content_type__app_label="martyrs",
        codename__in=[f"{action}_{model}" for model in content_models for action in ("view", "add", "change", "delete")],
    )
    author_group.permissions.set(author_perms)
    admin_group.permissions.set(admin_perms)
    return {ROLE_AUTHOR: author_group, ROLE_ADMIN: admin_group}


class PanelUserForm(forms.Form):
    username = forms.CharField(label="نام کاربری", max_length=150)
    first_name = forms.CharField(label="نام", max_length=100, required=False)
    last_name = forms.CharField(label="نام خانوادگی", max_length=100, required=False)
    role = forms.ChoiceField(label="نقش", choices=ROLE_CHOICES)
    password = forms.CharField(
        label="گذرواژه",
        strip=False,
        widget=forms.PasswordInput,
        help_text="در حالت ویرایش، برای حفظ گذرواژه فعلی خالی بگذارید.",
    )

    def __init__(self, *args, is_edit=False, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css} panel-input".strip()
        self.fields["password"].required = not is_edit

    def clean_username(self):
        from django.contrib.auth.models import User
        username = self.cleaned_data["username"].strip()
        query = User.objects.filter(username__iexact=username)
        if self.initial.get("pk"):
            query = query.exclude(pk=self.initial["pk"])
        if query.exists():
            raise forms.ValidationError("این نام کاربری قبلاً ثبت شده است.")
        return username
