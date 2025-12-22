# speedtest/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import SpeedTestResult, UserFeedback, NetworkIssue, InternetProvider


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email manzilingiz'
        })
    )
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Foydalanuvchi nomi'
        })
    )
    password1 = forms.CharField(
        label="Parol",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parol'
        })
    )
    password2 = forms.CharField(
        label="Parolni tasdiqlang",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parolni qayta kiriting'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Bu email allaqachon ro\'yxatdan o\'tgan!')
        return email


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Foydalanuvchi nomi yoki Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parol'
        })
    )


class SpeedTestForm(forms.ModelForm):
    class Meta:
        model = SpeedTestResult
        fields = ['connection_type']
        widgets = {
            'connection_type': forms.RadioSelect(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'connection_type': 'Ulanish turi'
        }


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = UserFeedback
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(
                choices=[(i, str(i)) for i in range(11)],
                attrs={'class': 'rating-input'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Fikr-mulohazangizni qoldiring...'
            })
        }
        labels = {
            'rating': 'Xizmat sifatini baholang (0-10)',
            'comment': 'Izoh (ixtiyoriy)'
        }


class NetworkIssueReportForm(forms.ModelForm):
    class Meta:
        model = NetworkIssue
        fields = ['service_name', 'issue_type', 'severity']
        widgets = {
            'service_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masalan: PlayStation Network'
            }),
            'issue_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'severity': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'service_name': 'Xizmat nomi',
            'issue_type': 'Muammo turi',
            'severity': 'Jiddiylik darajasi'
        }


class ProviderFilterForm(forms.Form):
    provider = forms.ModelChoiceField(
        queryset=InternetProvider.objects.filter(is_active=True),
        required=False,
        empty_label="Barcha provayderlar",
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Provayder'
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Boshlanish sanasi'
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Tugash sanasi'
    )

    connection_type = forms.ChoiceField(
        choices=[('', 'Barchasi'), ('multi', 'Multi'), ('single', 'Single')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Ulanish turi'
    )