# forms.py
from django import forms
from .models import SpeedTestResult, UserFeedback, NetworkIssue, InternetProvider


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


class SpeedTestCompareForm(forms.Form):
    result1 = forms.ModelChoiceField(
        queryset=SpeedTestResult.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Birinchi test'
    )

    result2 = forms.ModelChoiceField(
        queryset=SpeedTestResult.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Ikkinchi test'
    )

    def clean(self):
        cleaned_data = super().clean()
        result1 = cleaned_data.get('result1')
        result2 = cleaned_data.get('result2')

        if result1 and result2 and result1 == result2:
            raise forms.ValidationError('Iltimos, turli testlarni tanlang!')

        return cleaned_data