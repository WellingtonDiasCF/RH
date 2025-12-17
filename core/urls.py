from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 
from django.urls import path, include, re_path # Importe re_path e include
from django.views.generic import RedirectView # Importe RedirectView
urlpatterns = [
    # 1. REDIRECIONAMENTO (O Pulo do Gato)
    # Ao acessar /admin/, vai direto para a lista de equipes
    re_path(r'^admin/$', RedirectView.as_view(url='/admin/core_rh/equipe/', permanent=False)),

    # 2. ADMIN DO DJANGO (Necessário para as outras rotas do admin funcionarem)
    path('admin/', admin.site.urls),

    # 3. SEU APP RH
    path('', include('core_rh.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)