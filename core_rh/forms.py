from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


User = get_user_model()

class CpfPasswordResetForm(forms.Form):
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(attrs={
            'placeholder': '000.000.000-00',
            'class': 'form-control',
            'autofocus': True
        })
    )

    def clean_cpf(self):
        cpf_raw = self.cleaned_data.get('cpf', '')
        
        
        cpf_limpo = ''.join(filter(str.isdigit, cpf_raw))

        if not cpf_limpo:
            raise ValidationError("Por favor, digite um CPF.")

        
        
        if not User.objects.filter(username=cpf_limpo).exists():
            raise ValidationError("CPF não encontrado no sistema.")

        return cpf_limpo