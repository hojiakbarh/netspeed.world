# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Max, Min, Count
from django.utils import timezone
from datetime import timedelta
from .models import SpeedTestResult, InternetProvider, UserFeedback, NetworkIssue
from .forms import SpeedTestForm, FeedbackForm, NetworkIssueReportForm, ProviderFilterForm
import random
import requests


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
        # ipapi.co API dan foydalanish (bepul, registration kerak emas)
        response = requests.get(f'https://ipapi.co/{ip_address}/json/', timeout=5)
        data = response.json()

        return {
            'ip': ip_address,
            'city': data.get('city', 'Noma\'lum'),
            'region': data.get('region', 'Noma\'lum'),
            'country': data.get('country_name', 'Noma\'lum'),
            'isp': data.get('org', 'Noma\'lum'),  # Internet provayder
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

    # Provayderning qisqa nomini olish (masalan: "AS12345 UZTELECOM" -> "UZTELECOM")
    if ' ' in isp_name:
        isp_name = isp_name.split(' ')[-1]

    # Provayderni qidirish
    provider = InternetProvider.objects.filter(
        name__icontains=isp_name
    ).first()

    # Agar topilmasa, yangi yaratish
    if not provider:
        provider = InternetProvider.objects.create(
            name=isp_name,
            location=f"{location_data['city']}, {location_data['region']}",
            ip_address=location_data['ip'],
            is_active=True
        )

    return provider


def home(request):
    """Bosh sahifa - Avtomatik IP va joylashuv aniqlash bilan"""
    form = SpeedTestForm()

    # Foydalanuvchi IP va joylashuvini aniqlash
    client_ip = get_client_ip(request)
    location_data = get_location_and_isp(client_ip)

    # Provayderni topish yoki yaratish
    provider = get_or_create_provider(location_data)

    # Oxirgi testlar
    recent_tests = SpeedTestResult.objects.select_related('provider').order_by('-test_date')[:5]

    # Barcha provayderlar
    providers = InternetProvider.objects.filter(is_active=True)

    context = {
        'form': form,
        'recent_tests': recent_tests,
        'providers': providers,
        'location_data': location_data,
        'current_provider': provider,
        'page_title': 'Internet Tezligi Testi'
    }
    return render(request, 'speedtest/home.html', context)


def run_test(request):
    """Speed testni bajarish - Avtomatik ma'lumotlar bilan"""
    if request.method == 'POST':
        form = SpeedTestForm(request.POST)
        if form.is_valid():
            # Foydalanuvchi ma'lumotlarini avtomatik aniqlash
            client_ip = get_client_ip(request)
            location_data = get_location_and_isp(client_ip)
            provider = get_or_create_provider(location_data)

            # Test natijalarini yaratish
            test_result = form.save(commit=False)
            test_result.provider = provider
            test_result.ip_address = client_ip

            # Tasodifiy test natijalari (real testda ularni o'zgartiring)
            # Bu yerda siz real speed test API dan foydalanishingiz mumkin
            test_result.download_speed = round(random.uniform(50, 150), 2)
            test_result.upload_speed = round(random.uniform(40, 120), 2)
            test_result.ping = random.randint(3, 100)
            test_result.jitter = random.randint(1, 20)
            test_result.packet_loss = round(random.uniform(0, 5), 2)

            if request.user.is_authenticated:
                test_result.user = request.user

            test_result.save()

            messages.success(request, 'Test muvaffaqiyatli yakunlandi!')
            return redirect('test_result', pk=test_result.pk)

    return redirect('home')


def test_result(request, pk):
    """Test natijasini ko'rsatish"""
    result = get_object_or_404(SpeedTestResult, pk=pk)
    feedback_form = FeedbackForm()

    # O'rtacha ko'rsatkichlar
    avg_stats = SpeedTestResult.objects.filter(provider=result.provider).aggregate(
        avg_download=Avg('download_speed'),
        avg_upload=Avg('upload_speed'),
        avg_ping=Avg('ping')
    )

    # Joylashuv ma'lumotlarini olish
    location_data = get_location_and_isp(result.ip_address)

    context = {
        'result': result,
        'feedback_form': feedback_form,
        'avg_stats': avg_stats,
        'location_data': location_data,
        'page_title': 'Test Natijalari'
    }
    return render(request, 'speedtest/result.html', context)


def submit_feedback(request, pk):
    """Feedback yuborish"""
    result = get_object_or_404(SpeedTestResult, pk=pk)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.result = result
            feedback.save()
            messages.success(request, 'Fikr-mulohazangiz uchun rahmat!')
            return redirect('test_result', pk=pk)

    return redirect('test_result', pk=pk)


def results_history(request):
    """Barcha testlar tarixi"""
    filter_form = ProviderFilterForm(request.GET)
    results = SpeedTestResult.objects.select_related('provider').order_by('-test_date')

    # Filtrlash
    if filter_form.is_valid():
        provider = filter_form.cleaned_data.get('provider')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        connection_type = filter_form.cleaned_data.get('connection_type')

        if provider:
            results = results.filter(provider=provider)
        if date_from:
            results = results.filter(test_date__gte=date_from)
        if date_to:
            results = results.filter(test_date__lte=date_to)
        if connection_type:
            results = results.filter(connection_type=connection_type)

    # Paginatsiya
    from django.core.paginator import Paginator
    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'page_title': 'Testlar Tarixi'
    }
    return render(request, 'speedtest/history.html', context)


def statistics(request):
    """Statistika sahifasi"""
    # Umumiy statistika
    total_tests = SpeedTestResult.objects.count()

    # Oxirgi 30 kunlik o'rtacha
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_stats = SpeedTestResult.objects.filter(test_date__gte=thirty_days_ago).aggregate(
        avg_download=Avg('download_speed'),
        avg_upload=Avg('upload_speed'),
        avg_ping=Avg('ping'),
        max_download=Max('download_speed'),
        max_upload=Max('upload_speed'),
        min_ping=Min('ping')
    )

    # Provayderlar bo'yicha statistika
    provider_stats = InternetProvider.objects.annotate(
        test_count=Count('speedtestresult'),
        avg_download=Avg('speedtestresult__download_speed'),
        avg_upload=Avg('speedtestresult__upload_speed'),
        avg_ping=Avg('speedtestresult__ping')
    ).filter(test_count__gt=0)

    # Kunlik testlar soni (oxirgi 7 kun)
    from django.db.models.functions import TruncDate
    daily_tests = SpeedTestResult.objects.filter(
        test_date__gte=timezone.now() - timedelta(days=7)
    ).annotate(
        date=TruncDate('test_date')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')

    context = {
        'total_tests': total_tests,
        'recent_stats': recent_stats,
        'provider_stats': provider_stats,
        'daily_tests': daily_tests,
        'page_title': 'Statistika'
    }
    return render(request, 'speedtest/statistics.html', context)


def network_issues(request):
    """Tarmoq muammolari sahifasi"""
    issues = NetworkIssue.objects.filter(is_resolved=False).order_by('-reported_at')

    if request.method == 'POST':
        form = NetworkIssueReportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Muammo haqida xabar yuborildi!')
            return redirect('network_issues')
    else:
        form = NetworkIssueReportForm()

    context = {
        'issues': issues,
        'form': form,
        'page_title': 'Tarmoq Muammolari'
    }
    return render(request, 'speedtest/network_issues.html', context)


def about(request):
    """Loyiha haqida sahifa"""
    context = {
        'page_title': 'Loyiha Haqida'
    }
    return render(request, 'speedtest/about.html', context)