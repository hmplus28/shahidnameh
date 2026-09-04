from django import forms
from jalali_date.fields import JalaliDateField
from jalali_date.widgets import AdminJalaliDateWidget

from .models import Memory


class MartyrDirectoryFilterForm(forms.Form):
    """فیلترهای فهرست شهدا با دریافت بازه تاریخ جلالی و تبدیل امن به میلادی."""

    q = forms.CharField(required=False, label="نام شهید")
    province = forms.ChoiceField(required=False, label="استان")
    city = forms.CharField(required=False, label="شهر")
    unit = forms.ChoiceField(required=False, label="یگان، تیپ یا لشکر")
    martyrdom_from = JalaliDateField(required=False, label="از تاریخ شهادت", widget=AdminJalaliDateWidget)
    martyrdom_to = JalaliDateField(required=False, label="تا تاریخ شهادت", widget=AdminJalaliDateWidget)
    will = forms.CharField(required=False, label="کلیدواژه وصیت‌نامه")
    memory = forms.ChoiceField(required=False, label="نوع خاطره")

    def __init__(self, *args, provinces=(), units=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["province"].choices = [("", "همه استان‌ها")] + [(item, item) for item in provinces]
        self.fields["unit"].choices = [("", "همه یگان‌ها")] + [(item, item) for item in units]
        self.fields["memory"].choices = [("", "همه روایت‌ها")] + list(Memory.Category.choices)
        self.fields["q"].widget.attrs.update({"placeholder": "نام، نام خانوادگی یا نام پدر", "autocomplete": "off"})
        self.fields["city"].widget.attrs.update({"placeholder": "نام شهر", "autocomplete": "off"})
        self.fields["will"].widget.attrs.update({"placeholder": "مانند: نماز، ولایت، حجاب", "autocomplete": "off"})
        for field_name in ("martyrdom_from", "martyrdom_to"):
            self.fields[field_name].widget.attrs.update({
                "placeholder": "۱۴۰۰-۰۱-۰۱",
                "inputmode": "numeric",
                "autocomplete": "off",
                "class": "jalali-date-input",
            })

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("martyrdom_from")
        end = cleaned.get("martyrdom_to")
        if start and end and start > end:
            self.add_error("martyrdom_to", "پایان بازه نمی‌تواند پیش از آغاز آن باشد.")
        return cleaned
