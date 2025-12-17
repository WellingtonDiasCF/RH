from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django import forms
from .models import Funcionario, RegistroPonto, Cargo, Equipe


# --- FORMULÁRIO PERSONALIZADO (Mantido Original) ---
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
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.usuario.username
            self.fields['email'].initial = self.instance.usuario.email
            self.fields['is_active'].initial = self.instance.usuario.is_active


# --- ADMIN FUNCIONÁRIO ---
class FuncionarioAdmin(admin.ModelAdmin):
    form = FuncionarioAdminForm
    
    # Colunas da Tabela
    list_display = ('nome_completo', 'cargo', 'equipe', 'get_local_trabalho')
    
    # --- AJUSTE CRÍTICO PARA OS FILTROS FUNCIONAREM ---
    # Removi nome e email daqui (usar na busca). Deixei só categorias.
    list_filter = ('equipe', 'cargo', 'local_trabalho_estado') 
    
    # Barra de Pesquisa
    search_fields = ('nome_completo', 'cpf', 'usuario__username', 'email')
    
    filter_horizontal = ('outras_equipes',)
    
    class Media:
        js = ('js/cep_admin.js',)

    fieldsets = (
        ('🔐 Acesso', {'fields': ('username', 'password', 'email', 'is_active', 'primeiro_acesso')}),
        ('👤 Dados Pessoais', {'fields': ('nome_completo', 'cpf', 'data_admissao', 'numero_contrato')}),
        ('📍 Endereço', {'fields': ('cep', 'endereco', 'bairro', 'cidade', 'estado', 'local_trabalho_estado')}),
        ('🏢 Corporativo', {'fields': ('cargo', 'equipe', 'outras_equipes')}),
        ('⏰ Ponto', {'fields': ('jornada_entrada', 'jornada_saida', 'intervalo_padrao')}),
    )

    def get_local_trabalho(self, obj):
        if obj.local_trabalho_estado:
            return obj.local_trabalho_estado
        if obj.equipe and obj.equipe.local_trabalho:
            return obj.equipe.local_trabalho
        return "-"
    get_local_trabalho.short_description = 'Local de Trabalho'
    get_local_trabalho.admin_order_field = 'equipe__local_trabalho'

    # Lógica original de salvar usuário (Mantida)
    def save_model(self, request, obj, form, change):
        username = form.cleaned_data['username']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        is_active = form.cleaned_data['is_active']
        
        nomes = obj.nome_completo.strip().split()
        first_name = nomes[0].title()
        last_name = ' '.join(nomes[1:]).title() if len(nomes) > 1 else ''

        if change:
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
            user = User.objects.create_user(username=username, email=email, password=password or '123', first_name=first_name, last_name=last_name)
            user.is_active = is_active
            user.save()
            obj.usuario = user
            if not password:
                obj.primeiro_acesso = True
            obj.save()


# --- ADMIN EQUIPE ---
class EquipeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'local_trabalho', 'listar_gestores')
    search_fields = ('nome', 'local_trabalho')
    # Adicionado para ter filtro na aba Equipes
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
    date_hierarchy = 'data' # Navegação por data no topo
    
    def status_assinaturas(self, obj):
        func = "✅" if obj.assinado_funcionario else "❌"
        gest = "✅" if obj.assinado_gestor else "❌"
        return format_html("Func: {} | Gest: {}", func, gest)
    status_assinaturas.short_description = "Assinaturas"


# --- REGISTROS ---
admin.site.register(Funcionario, FuncionarioAdmin)
admin.site.register(Equipe, EquipeAdmin)
admin.site.register(Cargo, admin.ModelAdmin)
admin.site.register(RegistroPonto, RegistroPontoAdmin)

try:
    admin.site.unregister(User)
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass