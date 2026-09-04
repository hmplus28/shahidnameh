from django.contrib.auth import views as auth_views
from django.urls import path
from django.contrib.sitemaps.views import sitemap

from . import panel_views, views
from .sitemaps import SITEMAPS


app_name = "martyrs"

urlpatterns = [
    path("", views.home, name="home"),
    path("service-worker.js", views.service_worker, name="service-worker"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("martyrs/", views.martyr_directory, name="directory"),
    path("martyrs/<str:slug>/", views.martyr_detail, name="detail"),
    path("offline/", views.offline, name="offline"),
    path("panel/login/", panel_views.PanelLoginView.as_view(), name="panel_login"),
    path("panel/logout/", auth_views.LogoutView.as_view(next_page="martyrs:panel_login"), name="panel_logout"),
    path("panel/", panel_views.panel_home, name="panel_home"),
    path("panel/martyrs/", panel_views.martyr_list, name="panel_martyr_list"),
    path("panel/martyrs/new/", panel_views.martyr_create, name="panel_martyr_new"),
    path("panel/martyrs/<int:pk>/", panel_views.martyr_edit, name="panel_martyr_edit"),
    path("panel/martyrs/<int:pk>/<str:flag>-toggle/", panel_views.martyr_toggle_flag, name="panel_martyr_toggle"),
    path("panel/martyrs/<int:pk>/delete/", panel_views.martyr_delete, name="panel_martyr_delete"),
    path("panel/martyrs/<int:martyr_pk>/sections/add/", panel_views.section_add, name="panel_section_add"),
    path("panel/sections/<int:pk>/delete/", panel_views.section_delete, name="panel_section_delete"),
    path("panel/martyrs/<int:martyr_pk>/memories/add/", panel_views.memory_add, name="panel_memory_add"),
    path("panel/memories/<int:pk>/delete/", panel_views.memory_delete, name="panel_memory_delete"),
    path("panel/martyrs/<int:martyr_pk>/images/add/", panel_views.image_upload, name="panel_image_add"),
    path("panel/images/<int:pk>/delete/", panel_views.image_delete, name="panel_image_delete"),
    path("panel/martyrs/<int:martyr_pk>/videos/add/", panel_views.video_add, name="panel_video_add"),
    path("panel/videos/<int:pk>/delete/", panel_views.video_delete, name="panel_video_delete"),
    path("panel/martyrs/<int:martyr_pk>/injuries/add/", panel_views.injury_add, name="panel_injury_add"),
    path("panel/injuries/<int:pk>/delete/", panel_views.injury_delete, name="panel_injury_delete"),
    path("panel/martyrs/<int:martyr_pk>/comrades/add/", panel_views.comrade_add, name="panel_comrade_add"),
    path("panel/comrades/<int:pk>/delete/", panel_views.comrade_delete, name="panel_comrade_delete"),
    path("panel/logs/", panel_views.change_logs, name="panel_logs"),
    path("panel/users/", panel_views.user_list, name="panel_user_list"),
    path("panel/users/new/", panel_views.user_create, name="panel_user_new"),
    path("panel/users/<int:pk>/", panel_views.user_edit, name="panel_user_edit"),
    path("panel/users/<int:pk>/active-toggle/", panel_views.user_toggle_active, name="panel_user_toggle"),
    path("panel/users/<int:pk>/delete/", panel_views.user_delete, name="panel_user_delete"),
]
