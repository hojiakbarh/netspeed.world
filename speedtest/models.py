# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class InternetProvider(models.Model):
    name = models.CharField(max_length=200, verbose_name="Provayder nomi")
    location = models.CharField(max_length=200, verbose_name="Joylashuv")
    ip_address = models.GenericIPAddressField(verbose_name="IP Manzil")
    is_active = models.BooleanField(default=True, verbose_name="Faol")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Internet Provayder"
        verbose_name_plural = "Internet Provayderlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.location}"


class SpeedTestResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    provider = models.ForeignKey(InternetProvider, on_delete=models.SET_NULL, null=True)
    download_speed = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Yuklab olish tezligi (Mbps)")
    upload_speed = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Yuklash tezligi (Mbps)")
    ping = models.IntegerField(verbose_name="Ping (ms)")
    jitter = models.IntegerField(verbose_name="Jitter", null=True, blank=True)
    packet_loss = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Paket yo'qolishi (%)")
    connection_type = models.CharField(max_length=50, choices=[
        ('multi', 'Multi'),
        ('single', 'Single')
    ], default='multi')
    test_date = models.DateTimeField(default=timezone.now, verbose_name="Test sanasi")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Speed Test Natijasi"
        verbose_name_plural = "Speed Test Natijalari"
        ordering = ['-test_date']

    def __str__(self):
        return f"{self.provider} - {self.test_date.strftime('%Y-%m-%d %H:%M')}"

    @property
    def speed_rating(self):
        avg_speed = (float(self.download_speed) + float(self.upload_speed)) / 2
        if avg_speed >= 100:
            return "A'lo"
        elif avg_speed >= 50:
            return "Yaxshi"
        elif avg_speed >= 25:
            return "O'rtacha"
        else:
            return "Past"


class UserFeedback(models.Model):
    result = models.ForeignKey(SpeedTestResult, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=[(i, i) for i in range(11)], verbose_name="Baho (0-10)")
    comment = models.TextField(blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foydalanuvchi Fikri"
        verbose_name_plural = "Foydalanuvchi Fikrlari"

    def __str__(self):
        return f"Baho: {self.rating} - {self.result}"


class NetworkIssue(models.Model):
    service_name = models.CharField(max_length=200, verbose_name="Xizmat nomi")
    issue_type = models.CharField(max_length=100, choices=[
        ('outage', 'To\'liq ishlamayapti'),
        ('slow', 'Sekin ishlayapti'),
        ('intermittent', 'Vaqti-vaqti bilan')
    ], verbose_name="Muammo turi")
    severity = models.CharField(max_length=50, choices=[
        ('low', 'Past'),
        ('medium', 'O\'rtacha'),
        ('high', 'Yuqori')
    ], default='medium')
    reported_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Tarmoq Muammosi"
        verbose_name_plural = "Tarmoq Muammolari"
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.service_name} - {self.get_issue_type_display()}"