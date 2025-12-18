import json
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django import forms
from django.urls import reverse # Importante para o botão do PDF
from .models import Funcionario, RegistroPonto, Cargo, Equipe, Ferias

# --- FORMULÁRIO PERSONALIZADO ---
class FuncionarioAdminForm(forms.ModelForm):
    username = forms.CharField(label="Usuário (Login/CPF)", required=True)
    email = forms.EmailField(label="E-mail", required=True)
    password = forms.CharField(label="Senha", widget=forms.PasswordInput, required=False, help_text="Deixe vazio para manter a senha atual.")
    is_active = forms.BooleanField(label="Acesso Ativo?", required=False, initial=True)

    class Meta:
        model = Funcionario
        fields = '__all__'
        exclude = ('usuario',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.usuario:
            self.fields['username'].initial = self.instance.usuario.username
            self.fields['email'].initial = self.instance.usuario.email
            self.fields['is_active'].initial = self.instance.usuario.is_active


# --- ADMIN FUNCIONÁRIO ---
class FuncionarioAdmin(admin.ModelAdmin):
    form = FuncionarioAdminForm
    
    list_display = ('nome_completo', 'cargo', 'equipe', 'get_local_trabalho')
    
    list_filter = ('local_trabalho_estado', 'equipe', 'cargo') 
    
    search_fields = ('nome_completo', 'cpf', 'usuario__username', 'email')
    filter_horizontal = ('outras_equipes',)
    
    class Media:
        js = ('js/cep_admin.js',)

    # ATUALIZADO: Adicionei o grupo 'Documentação' com os novos campos
    fieldsets = (
        ('🔐 Acesso', {'fields': ('username', 'password', 'email', 'is_active', 'primeiro_acesso')}),
        ('👤 Dados Pessoais', {'fields': ('nome_completo', 'cpf', 'data_admissao')}),
        ('📄 Documentação (Para Férias)', {'fields': (('matricula', 'registro_geral'), ('carteira_trabalho', 'serie_ctps'))}),
        ('📍 Endereço', {'fields': ('cep', 'endereco', 'bairro', 'cidade', 'estado', 'local_trabalho_estado')}),
        ('🏢 Corporativo', {'fields': ('cargo', 'equipe', 'outras_equipes', 'numero_contrato')}),
        ('⏰ Ponto', {'fields': ('jornada_entrada', 'jornada_saida', 'intervalo_padrao', 'saldo_horas')}),
    )

    def get_local_trabalho(self, obj):
        if obj.local_trabalho_estado:
            return obj.local_trabalho_estado
        if obj.equipe and obj.equipe.local_trabalho:
            return obj.equipe.local_trabalho
        return "-"
    get_local_trabalho.short_description = 'Local de Trabalho'
    get_local_trabalho.admin_order_field = 'equipe__local_trabalho'

    # --- INJEÇÃO DE DADOS PARA OS FILTROS DO TOPO ---
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        estados = Funcionario.objects.exclude(local_trabalho_estado__isnull=True)\
                                     .exclude(local_trabalho_estado='')\
                                     .values_list('local_trabalho_estado', flat=True)\
                                     .distinct().order_by('local_trabalho_estado')
        
        mapa_estado_equipe = {}
        for est in estados:
            ids = Funcionario.objects.filter(local_trabalho_estado=est)\
                                     .exclude(equipe__isnull=True)\
                                     .values_list('equipe_id', flat=True)\
                                     .distinct()
            mapa_estado_equipe[est] = list(ids)

        todas_equipes = list(Equipe.objects.values('id', 'nome').order_by('nome'))

        extra_context['filter_estados'] = list(estados)
        extra_context['filter_equipes'] = todas_equipes
        extra_context['json_mapa_equipes'] = json.dumps(mapa_estado_equipe)
        
        return super().changelist_view(request, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        is_active = form.cleaned_data['is_active']
        
        nomes = obj.nome_completo.strip().split()
        first_name = nomes[0].title()
        last_name = ' '.join(nomes[1:]).title() if len(nomes) > 1 else ''

        if change and obj.usuario:
            user = obj.usuario
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = is_active
            if password:
                user.set_password(password)
            user.save()
            obj.save()
        else:
            # Cria usuário se não existir
            try:
                user = User.objects.create_user(username=username, email=email, password=password or '123456', first_name=first_name, last_name=last_name)
                user.is_active = is_active
                user.save()
                obj.usuario = user
                if not password:
                    obj.primeiro_acesso = True
                obj.save()
            except Exception as e:
                # Caso o usuário já exista mas não esteja vinculado, tenta vincular
                if User.objects.filter(username=username).exists():
                     obj.usuario = User.objects.get(username=username)
                     obj.save()


# --- ADMIN EQUIPE ---
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'local_trabalho', 'listar_gestores')
    search_fields = ('nome', 'local_trabalho')
    list_filter = ('local_trabalho',) 
    filter_horizontal = ('gestores',)

    def listar_gestores(self, obj):
        return ", ".join([g.nome_completo.split()[0] for g in obj.gestores.all()])
    listar_gestores.short_description = "Gestores"


# --- ADMIN PONTO ---
class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'data', 'entrada_manha', 'saida_tarde', 'status_assinaturas')
    list_filter = ('data', 'funcionario__equipe', 'assinado_funcionario', 'assinado_gestor')
    search_fields = ('funcionario__nome_completo',)
    date_hierarchy = 'data'
    
    def status_assinaturas(self, obj):
        func = "✅" if obj.assinado_funcionario else "❌"
        gest = "✅" if obj.assinado_gestor else "❌"
        return format_html("Func: {} | Gest: {}", func, gest)
    status_assinaturas.short_description = "Assinaturas"


# --- ADMIN FÉRIAS (3 ETAPAS) ---
# --- ADMIN FÉRIAS (CONFIGURAÇÃO CORRETA) ---
class FeriasAdmin(admin.ModelAdmin):
    # O PULO DO GATO: Autocomplete fields ativa a busca bonita
    autocomplete_fields = ['funcionario'] 
    
    list_display = ('funcionario', 'periodo_aquisitivo', 'data_inicio', 'status_etapas', 'botao_pdf')
    list_filter = ('status', 'abono_pecuniario')
    search_fields = ('funcionario__nome_completo',)
    
    def botao_pdf(self, obj):
        if obj.id:
            url = reverse('gerar_aviso_ferias_pdf', args=[obj.id])
            return format_html('<a class="button" href="{}" target="_blank" style="background:#17a2b8; color:white;"><i class="fas fa-print"></i> PDF</a>', url)
        return "-"
    botao_pdf.short_description = "Aviso"

    def status_etapas(self, obj):
        agendado = "✅" if obj.data_inicio else "⬜"
        arquivo = "✅" if obj.arquivo_aviso else "⬜"
        assinado = "✅" if obj.aviso_assinado else "⬜"
        return f"1.Agenda {agendado} ➔ 2.Arq {arquivo} ➔ 3.Assinou {assinado}"
    status_etapas.short_description = "Fluxo"

    fieldsets = (
        ('PASSO 1: AGENDAR', {
            'fields': ('funcionario', ('data_inicio', 'data_fim'), ('periodo_aquisitivo', 'abono_pecuniario')),
            'classes': ('wide', 'extrapretty'), 
        }),
        ('PASSO 2: GERAR DOCUMENTO', {
            'description': 'Salve o agendamento, clique no botão para gerar o PDF e depois anexe abaixo.',
            'fields': ('link_gerar_pdf', 'arquivo_aviso'),
        }),
        ('PASSO 3: UPLOAD DO RECIBO', {
            'fields': ('arquivo_recibo',),
        }),
        ('Status (Automático)', {
            'fields': ('status', 'aviso_assinado', 'recibo_assinado'),
            'classes': ('collapse',), 
        }),
    )
    readonly_fields = ('link_gerar_pdf', 'aviso_assinado', 'recibo_assinado')

    def link_gerar_pdf(self, obj):
        if obj.id:
            url = reverse('gerar_aviso_ferias_pdf', args=[obj.id])
            return format_html(
                '<a href="{}" target="_blank" class="button" style="background-color: #007bff; color: white; padding: 10px 20px; width:100%; text-align:center;">'
                '<i class="fas fa-file-pdf"></i> GERAR PDF DE AVISO</a> <br><br> '
                '<span style="color: #666;">(Clique para baixar, depois faça o upload no campo abaixo)</span>', url)
        return "Salve primeiro para gerar."
    link_gerar_pdf.short_description = "Ação"

# --- REGISTROS ---
admin.site.register(Funcionario, FuncionarioAdmin)
admin.site.register(Equipe, EquipeAdmin)
admin.site.register(Cargo, admin.ModelAdmin)
admin.site.register(RegistroPonto, RegistroPontoAdmin)
admin.site.register(Ferias, FeriasAdmin)

try:
    admin.site.unregister(User)
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass