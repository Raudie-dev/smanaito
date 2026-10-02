from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

from app1 import views as app1_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest'),
    path('sw.js', TemplateView.as_view(template_name='sw.js', content_type='application/javascript'), name='sw'),
    path('', include('app1.urls')),
    path('app2/', include('app2.urls')),
    path('accounts/password_reset/', app1_views.password_reset_view, name='password_reset'),
    path('accounts/password_reset/done/', TemplateView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', app1_views.password_reset_confirm_view, name='password_reset_confirm'),
    path('accounts/reset/done/', TemplateView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]

# Servir archivos estáticos y multimedia localmente, incluso con DEBUG=False
from django.conf import settings
from django.urls import re_path
from django.views.static import serve

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]