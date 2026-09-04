from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from martyrs.models import ComradeMartyr, Martyr, MartyrInjury, Memory


class FeatureFieldsTests(TestCase):
    """تست یک‌به‌یک قابلیت‌های درخواستی پرونده شهید."""

    def setUp(self):
        self.martyr = Martyr.objects.create(
            first_name="علی",
            last_name="حسینی",
            last_name_old="حسینی قدیم",
            birth_date=date(1965, 3, 21),
            birth_date_hijri="۱۵ شعبان ۱۳۸۴ قمری",
            birth_province="فارس",
            birth_county="شیراز",
            birth_city="شیراز",
            birth_village="دوزخان",
            martyrdom_date=date(1985, 2, 8),
            burial_county="تهران",
            burial_village="تهران",
            burial_cemetery="بهشت زهرا",
            burial_plot="۲۶",
            division="لشکر ۱۹ فجر",
            brigade="تیپ ۱ انصار",
            battalion="گردان امام رضا",
            company="گروهان علی‌اکبر",
            platoon="دسته اول",
            unit_role="معاون فرمانده گروهان",
            is_published=True,
        )
        MartyrInjury.objects.create(
            martyr=self.martyr,
            injury_date=date(1982, 7, 10),
            description="شکستگی پا در عملیات رمضان",
        )
        ComradeMartyr.objects.create(
            martyr=self.martyr,
            full_name="محمد کریمی",
            service_place="لشکر ۱۹ فجر - گردان امام رضا",
            memories="خاطره‌ای از شب عملیات.",
        )

    # 1) نام خانوادگی قدیم و جدید
    def test_old_and_new_last_names_are_stored_and_displayed(self):
        response = self.client.get(self.martyr.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "نام خانوادگی قدیم")
        self.assertContains(response, "حسینی قدیم")
        self.assertContains(response, "شهید علی حسینی")

    # 2) تاریخ تولد شمسی و قمری
    def test_shamsi_and_hijri_birth_dates_displayed(self):
        response = self.client.get(self.martyr.get_absolute_url())
        self.assertContains(response, "تاریخ تولد (شمسی)")
        self.assertContains(response, "تاریخ تولد (قمری)")
        self.assertContains(response, "۱۵ شعبان ۱۳۸۴ قمری")

    # 3) محل تولد به ترتیب استان، شهرستان، شهر، روستا
    def test_birth_place_chain_order(self):
        self.assertEqual(
            self.martyr.birth_place_full,
            "فارس، شیراز، شیراز، دوزخان",
        )
        response = self.client.get(self.martyr.get_absolute_url())
        for label in ("استان تولد", "شهرستان تولد", "شهر تولد", "روستای تولد"):
            self.assertContains(response, label)

    # 4) مجروحیت به دفعات با تاریخ و توضیحات
    def test_multiple_injuries_with_date_and_description(self):
        second = MartyrInjury.objects.create(
            martyr=self.martyr,
            injury_date=date(1984, 3, 1),
            description="ترکش در ناحیه دست",
        )
        self.assertEqual(self.martyr.injuries.count(), 2)

        response = self.client.get(self.martyr.get_absolute_url())
        self.assertContains(response, "مجروحیت‌ها")
        self.assertContains(response, "شکستگی پا در عملیات رمضان")
        self.assertContains(response, "ترکش در ناحیه دست")

    # 5) محل دفن: شهرستان، روستا، نام محل دفن، قطعه
    def test_burial_details_displayed(self):
        self.assertIn("بهشت زهرا", self.martyr.burial_place_full)
        self.assertIn("قطعه ۲۶", self.martyr.burial_place_full)

        response = self.client.get(self.martyr.get_absolute_url())
        self.assertContains(response, "نام محل دفن")
        self.assertContains(response, "بهشت زهرا")
        self.assertContains(response, "قطعه")

    # 6) یگان: لشکر، تیپ، گردان، گروهان، دسته + مسئولیت
    def test_unit_hierarchy_chain_and_role(self):
        chain = dict(self.martyr.unit_chain)
        self.assertEqual(set(chain.values()), {"لشکر ۱۹ فجر", "تیپ ۱ انصار", "گردان امام رضا", "گروهان علی‌اکبر", "دسته اول"})

        response = self.client.get(self.martyr.get_absolute_url())
        self.assertContains(response, "مسئولیت در یگان")
        self.assertContains(response, "معاون فرمانده گروهان")

    # 7) همرزمان: نام، محل خدمت با شهید، خاطرات
    def test_comrades_with_service_place_and_memories(self):
        response = self.client.get(self.martyr.get_absolute_url())
        self.assertContains(response, "همرزمان شهید")
        self.assertContains(response, "محمد کریمی")
        self.assertContains(response, "هم‌خدمت در لشکر ۱۹ فجر")
        self.assertContains(response, "خاطره‌ای از شب عملیات.")

    # 9) شهدای شاخص در نمای کلی و قابل مشاهده
    def test_featured_martyrs_visible_on_home(self):
        self.martyr.is_featured = True
        self.martyr.save(update_fields=["is_featured"])

        response = self.client.get(reverse("martyrs:home"))
        self.assertContains(response, "شهدای شاخص")
        self.assertContains(response, "علی حسینی")


class HomePageWarDesignTests(TestCase):
    """المان‌های محراب، جبهه/بسیج و تذهیب در نمای کلی."""

    def test_home_contains_mihrab_and_war_elements(self):
        response = self.client.get(reverse("martyrs:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hero-war-silhouette")  # المان خاکریز/جبهه
        self.assertContains(response, "heading-frame")   # قاب تذهیبی عناوین
        self.assertContains(response, "kafiyeh-bg")      # پترن چفیه
        self.assertContains(response, "section-divider") # جداکننده مذهبی


class PanelFeatureTests(TestCase):
    """پنل اختصاصی: ثبت مجروحیت و همرزم."""

    def setUp(self):
        user_model = get_user_model()
        self.manager = user_model.objects.create_superuser("boss", "boss@example.com", "safe-test-password")
        self.client.force_login(self.manager)
        self.martyr = Martyr.objects.create(first_name="رضا", last_name="مرادی")

    def test_panel_form_includes_new_fields(self):
        response = self.client.get(reverse("martyrs:panel_martyr_edit", args=[self.martyr.pk]))
        self.assertEqual(response.status_code, 200)
        for field_label in ("نام خانوادگی قدیم", "قمری", "شهرستان تولد", "روستای تولد", "قطعه", "گروهان", "مسئولیت در یگان"):
            self.assertContains(response, field_label)

    def test_injury_can_be_added_from_panel(self):
        response = self.client.post(
            reverse("martyrs:panel_injury_add", args=[self.martyr.pk]),
            {"injury_date": "1361-04-19", "description": "ترکش خوردن در منطقه"},
        )
        self.assertRedirects(response, reverse("martyrs:panel_martyr_edit", args=[self.martyr.pk]))
        injury = self.martyr.injuries.get()
        self.assertEqual(injury.description, "ترکش خوردن در منطقه")

    def test_comrade_can_be_added_from_panel(self):
        response = self.client.post(
            reverse("martyrs:panel_comrade_add", args=[self.martyr.pk]),
            {"full_name": "اکبر صادقی", "service_place": "گردان کمیل", "memories": "خاطره مشترک."},
        )
        self.assertRedirects(response, reverse("martyrs:panel_martyr_edit", args=[self.martyr.pk]))
        comrade = self.martyr.comrades.get()
        self.assertEqual(comrade.service_place, "گردان کمیل")

    def test_injury_delete_view(self):
        injury = MartyrInjury.objects.create(martyr=self.martyr, description="آزمون حذف")
        response = self.client.post(reverse("martyrs:panel_injury_delete", args=[injury.pk]))
        self.assertEqual(self.martyr.injuries.count(), 0)

    def test_comrade_delete_view(self):
        comrade = ComradeMartyr.objects.create(martyr=self.martyr, full_name="حذف آزمون")
        response = self.client.post(reverse("martyrs:panel_comrade_delete", args=[comrade.pk]))
        self.assertEqual(self.martyr.comrades.count(), 0)


class AdminFeatureTests(TestCase):
    """پنل مدیریت: اینلاین مجروحیت و همرزم."""

    def setUp(self):
        user_model = get_user_model()
        self.manager = user_model.objects.create_superuser("adminx", "adminx@example.com", "safe-test-password")
        self.client.force_login(self.manager)

    def test_admin_change_page_renders_new_fields_and_inlines(self):
        martyr = Martyr.objects.create(first_name="مهدی", last_name="نوری")
        url = reverse("admin:martyrs_martyr_change", args=[martyr.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        for needle in ("last_name_old", "birth_date_hijri", "burial_plot", "unit_role", "injuries-TOTAL_FORMS", "comrades-TOTAL_FORMS"):
            self.assertContains(response, needle)
