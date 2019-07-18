"""brondon URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from summer import views

urlpatterns = [
    re_path(r'report/$', views.asset_report, name='asset_report'),
    re_path(r'report/asset_with_no_asset_id/$', views.asset_with_no_asset_id),
    re_path(r'new_assets/approval/$', views.new_assets_approval, name='new_assets_approval'),
]
