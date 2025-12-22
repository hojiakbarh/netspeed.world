# speedtest/views.py
from django.shortcuts import  get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Max, Min, Count, Q
from django.utils import timezone
from django.views.generic import (
    ListView, DetailView, CreateView,
    DeleteView, TemplateView, FormView, View
)
from django.urls import reverse_lazy
from datetime import timedelta
from .models import SpeedTestResult, InternetProvider, UserFeedback, NetworkIssue
from .forms import (
    SpeedTestForm, FeedbackForm, NetworkIssueReportForm,
    ProviderFilterForm, UserRegistrationForm, UserLoginForm
)
import random
import requests
from django.shortcuts import render
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


def get_client_ip(request):
    """Foydalanuvchining IP manzilini olish"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_location_and_isp(ip_address):
    """IP manzildan joylashuv va ISP ma'lumotlarini olish"""
    try:
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        data = response.json()

        return {
            'ip': ip_address,
            'city': data.get('city', 'Noma\'lum'),
            'region': data.get('region', 'Noma\'lum'),
            'country': data.get('country_name', 'Noma\'lum'),
            'isp': data.get('org', 'Noma\'lum'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
        }
    except Exception as e:
        print(f"IP ma'lumotlarini olishda xatolik: {e}")
        return {
            'ip': ip_address,
            'city': 'Toshkent',
            'region': 'Toshkent',
            'country': 'O\'zbekiston',
            'isp': 'UZTELECOM',
            'latitude': None,
            'longitude': None,
        }


def get_or_create_provider(location_data):
    """Provayderni topish yoki yangi yaratish"""
    isp_name = location_data['isp']

    if ' ' in isp_name:
        isp_name = isp_name.split(' ')[-1]

    provider = InternetProvider.objects.filter(
        name__icontains=isp_name
    ).first()

    if not provider:
        provider = InternetProvider.objects.create(
            name=isp_name,
            location=f"{location_data['city']}, {location_data['region']}",
            ip_address=location_data['ip'],
            is_active=True
        )

    return provider


# ============================================
# REGISTRATION & LOGIN
# ============================================
class RegisterView(CreateView):
    """Ro'yxatdan o'tish"""
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Xush kelibsiz, {user.username}!')
        return redirect('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Ro\'yxatdan O\'tish'
        return context


class LoginView(FormView):
    """Kirish"""
    form_class = UserLoginForm
    template_name = 'registration/login.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(self.request, user)
            messages.success(self.request, f'Xush kelibsiz, {user.username}!')

            # Agar redirect kerak bo'lsa
            next_url = self.request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(self.request, 'Login yoki parol noto\'g\'ri!')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Kirish'
        return context


@never_cache
@require_http_methods(["GET", "POST"])
def logout_view(request):
    """Chiqish - cache qilinmaydi"""
    logout(request)
    messages.info(request, 'Siz tizimdan chiqdingiz.')

    response = redirect('home')
    # Cache larni o'chirish
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'

    return response


# ============================================
# BOSH SAHIFA
# ============================================
class HomeView(TemplateView):
    """Bosh sahifa - Hamma ko'ra oladi"""
    template_name = 'speedtest/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        client_ip = get_client_ip(self.request)
        location_data = get_location_and_isp(client_ip)
        provider = get_or_create_provider(location_data)

        # Login qilgan foydalanuvchi o'z testlarini ko'radi
        if self.request.user.is_authenticated:
            recent_tests = SpeedTestResult.objects.filter(
                user=self.request.user
            ).select_related('provider').order_by('-test_date')[:5]
        else:
            recent_tests = []

        context.update({
            'form': SpeedTestForm(),
            'recent_tests': recent_tests,
            'providers': InternetProvider.objects.filter(is_active=True),
            'location_data': location_data,
            'current_provider': provider,
            'page_title': 'Internet Tezligi Testi'
        })
        return context


# ============================================
# TEST YARATISH
# ============================================
class RunTestView(FormView):
    """Test qilish - Hamma test qila oladi"""
    form_class = SpeedTestForm
    template_name = 'speedtest/home.html'
    success_url = None

    def form_valid(self, form):
        client_ip = get_client_ip(self.request)
        location_data = get_location_and_isp(client_ip)
        provider = get_or_create_provider(location_data)

        test_result = form.save(commit=False)
        test_result.provider = provider
        test_result.ip_address = client_ip

        # Login qilgan - user ga biriktiramiz
        if self.request.user.is_authenticated:
            test_result.user = self.request.user
        else:
            # Anonim - session ID
            if not self.request.session.session_key:
                self.request.session.create()
            test_result.session_id = self.request.session.session_key

        # Test natijalari
        test_result.download_speed = round(random.uniform(50, 150), 2)
        test_result.upload_speed = round(random.uniform(40, 120), 2)
        test_result.ping = random.randint(3, 100)
        test_result.jitter = random.randint(1, 20)
        test_result.packet_loss = round(random.uniform(0, 5), 2)

        test_result.save()

        messages.success(self.request, 'Test muvaffaqiyatli yakunlandi!')
        return redirect('test_result', pk=test_result.pk)


# ============================================
# TEST NATIJASI
# ============================================
class TestResultView(DetailView):
    """Test natijasi - hamma ko'ra oladi"""
    model = SpeedTestResult
    template_name = 'speedtest/result.html'
    context_object_name = 'result'

    def get_queryset(self):
        # Login qilgan - faqat o'z testlarini
        if self.request.user.is_authenticated:
            return SpeedTestResult.objects.filter(user=self.request.user)

        # Anonim - session bo'yicha
        session_id = self.request.session.session_key
        if session_id:
            return SpeedTestResult.objects.filter(session_id=session_id)

        # Hech narsa topilmasa
        return SpeedTestResult.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = self.get_object()

        # O'rtacha statistika
        if self.request.user.is_authenticated:
            avg_stats = SpeedTestResult.objects.filter(
                provider=result.provider,
                user=self.request.user
            ).aggregate(
                avg_download=Avg('download_speed'),
                avg_upload=Avg('upload_speed'),
                avg_ping=Avg('ping')
            )
        else:
            avg_stats = {}

        location_data = get_location_and_isp(result.ip_address)

        # O'chirish mumkinmi?
        can_delete = False
        if self.request.user.is_authenticated and result.user == self.request.user:
            can_delete = True
        elif not self.request.user.is_authenticated and result.session_id == self.request.session.session_key:
            can_delete = True

        context.update({
            'feedback_form': FeedbackForm(),
            'avg_stats': avg_stats,
            'location_data': location_data,
            'can_delete': can_delete,
            'page_title': 'Test Natijalari'
        })
        return context


# ============================================
# TEST O'CHIRISH
# ============================================
class DeleteTestView(DeleteView):
    """Test o'chirish - faqat o'ziniki"""
    model = SpeedTestResult
    template_name = 'speedtest/confirm_delete.html'
    success_url = reverse_lazy('results_history')
    context_object_name = 'result'

    def get_queryset(self):
        # Login qilgan
        if self.request.user.is_authenticated:
            return SpeedTestResult.objects.filter(user=self.request.user)

        # Anonim
        session_id = self.request.session.session_key
        if session_id:
            return SpeedTestResult.objects.filter(session_id=session_id)

        return SpeedTestResult.objects.none()

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Test muvaffaqiyatli o\'chirildi!')

        # Agar anonim bo'lsa, home ga qaytarish
        if not request.user.is_authenticated:
            self.success_url = reverse_lazy('home')

        return super().delete(request, *args, **kwargs)


# ============================================
# TESTLAR TARIXI - Login KERAK
# ============================================
# History View
@method_decorator(never_cache, name='dispatch')
class ResultsHistoryView(LoginRequiredMixin, ListView):
    """Tarix - cache qilinmaydi"""
    model = SpeedTestResult
    template_name = 'speedtest/history.html'
    context_object_name = 'page_obj'
    paginate_by = 20
    login_url = 'login'

    def get_queryset(self):
        queryset = SpeedTestResult.objects.filter(
            user=self.request.user
        ).select_related('provider').order_by('-test_date')

        # Filtrlash
        provider = self.request.GET.get('provider')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        connection_type = self.request.GET.get('connection_type')

        if provider:
            queryset = queryset.filter(provider_id=provider)
        if date_from:
            queryset = queryset.filter(test_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(test_date__lte=date_to)
        if connection_type:
            queryset = queryset.filter(connection_type=connection_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ProviderFilterForm(self.request.GET)
        context['page_title'] = 'Mening Testlarim'
        return context


# ============================================
# STATISTIKA - Login KERAK
# ============================================
@method_decorator(never_cache, name='dispatch')
class StatisticsView(LoginRequiredMixin, TemplateView):
    """Statistika - cache qilinmaydi"""
    template_name = 'speedtest/statistics.html'
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        total_tests = SpeedTestResult.objects.filter(user=user).count()

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_stats = SpeedTestResult.objects.filter(
            user=user,
            test_date__gte=thirty_days_ago
        ).aggregate(
            avg_download=Avg('download_speed'),
            avg_upload=Avg('upload_speed'),
            avg_ping=Avg('ping'),
            max_download=Max('download_speed'),
            max_upload=Max('upload_speed'),
            min_ping=Min('ping')
        )

        provider_stats = InternetProvider.objects.annotate(
            test_count=Count('speedtestresult', filter=Q(speedtestresult__user=user)),
            avg_download=Avg('speedtestresult__download_speed', filter=Q(speedtestresult__user=user)),
            avg_upload=Avg('speedtestresult__upload_speed', filter=Q(speedtestresult__user=user)),
            avg_ping=Avg('speedtestresult__ping', filter=Q(speedtestresult__user=user))
        ).filter(test_count__gt=0)

        from django.db.models.functions import TruncDate
        daily_tests = SpeedTestResult.objects.filter(
            user=user,
            test_date__gte=timezone.now() - timedelta(days=7)
        ).annotate(
            date=TruncDate('test_date')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')

        context.update({
            'total_tests': total_tests,
            'recent_stats': recent_stats,
            'provider_stats': provider_stats,
            'daily_tests': daily_tests,
            'page_title': 'Mening Statistikam'
        })
        return context


# ============================================
# FEEDBACK
# ============================================
class SubmitFeedbackView(CreateView):
    """Feedback - hamma yuborishi mumkin"""
    model = UserFeedback
    form_class = FeedbackForm

    def form_valid(self, form):
        result = get_object_or_404(SpeedTestResult, pk=self.kwargs['pk'])
        feedback = form.save(commit=False)
        feedback.result = result
        feedback.save()

        messages.success(self.request, 'Fikr-mulohazangiz uchun rahmat!')
        return redirect('test_result', pk=result.pk)


# ============================================
# NETWORK ISSUES
# ============================================
class NetworkIssuesView(CreateView):
    """Tarmoq muammolari"""
    model = NetworkIssue
    form_class = NetworkIssueReportForm
    template_name = 'speedtest/network_issues.html'
    success_url = reverse_lazy('network_issues')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['issues'] = NetworkIssue.objects.filter(
            is_resolved=False
        ).order_by('-reported_at')
        context['page_title'] = 'Tarmoq Muammolari'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Muammo haqida xabar yuborildi!')
        return super().form_valid(form)


# ============================================
# ABOUT
# ============================================
class AboutView(TemplateView):
    """Loyiha haqida"""
    template_name = 'speedtest/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Loyiha Haqida'
        return context




def custom_404(request, exception):
    """Custom 404 page"""
    return render(request, '404.html', status=404)

def custom_500(request):
    """Custom 500 page"""
    return render(request, '500.html', status=500)