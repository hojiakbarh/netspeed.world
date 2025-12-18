# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import InternetProvider, SpeedTestResult, UserFeedback, NetworkIssue


@admin.register(InternetProvider)
class InternetProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'ip_address', 'status_badge', 'created_at']
    list_filter = ['is_active', 'location', 'created_at']
    search_fields = ['name', 'location', 'ip_address']
    list_per_page = 20

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Faol</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Nofaol</span>'
        )

    status_badge.short_description = 'Holat'


@admin.register(SpeedTestResult)
class SpeedTestResultAdmin(admin.ModelAdmin):
    list_display = ['provider', 'download_speed_colored', 'upload_speed_colored',
                    'ping_colored', 'connection_type', 'speed_rating', 'test_date']
    list_filter = ['connection_type', 'test_date', 'provider']
    search_fields = ['provider__name', 'ip_address']
    readonly_fields = ['test_date', 'speed_rating']
    date_hierarchy = 'test_date'
    list_per_page = 25

    fieldsets = (
        ('Umumiy Ma\'lumot', {
            'fields': ('user', 'provider', 'connection_type', 'test_date')
        }),
        ('Tezlik Ko\'rsatkichlari', {
            'fields': ('download_speed', 'upload_speed', 'ping', 'jitter', 'packet_loss'),
            'classes': ('wide',)
        }),
        ('Qo\'shimcha', {
            'fields': ('ip_address', 'speed_rating'),
            'classes': ('collapse',)
        }),
    )

    def download_speed_colored(self, obj):
        speed = float(obj.download_speed)
        if speed >= 100:
            color = '#28a745'
        elif speed >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<strong style="color: {};">{:.2f} Mbps</strong>',
            color, speed
        )

    download_speed_colored.short_description = 'Download'
    download_speed_colored.admin_order_field = 'download_speed'

    def upload_speed_colored(self, obj):
        speed = float(obj.upload_speed)
        if speed >= 100:
            color = '#28a745'
        elif speed >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<strong style="color: {};">{:.2f} Mbps</strong>',
            color, speed
        )

    upload_speed_colored.short_description = 'Upload'
    upload_speed_colored.admin_order_field = 'upload_speed'

    def ping_colored(self, obj):
        if obj.ping <= 20:
            color = '#28a745'
        elif obj.ping <= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'
        return format_html(
            '<span style="color: {};">{} ms</span>',
            color, obj.ping
        )

    ping_colored.short_description = 'Ping'
    ping_colored.admin_order_field = 'ping'


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['result', 'rating_stars', 'comment_preview', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'result__provider__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        return format_html('<span style="font-size: 16px;">{}</span>', stars)

    rating_stars.short_description = 'Baho'

    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return '-'

    comment_preview.short_description = 'Izoh'


@admin.register(NetworkIssue)
class NetworkIssueAdmin(admin.ModelAdmin):
    list_display = ['service_name', 'issue_type_badge', 'severity_badge',
                    'status_badge', 'reported_at']
    list_filter = ['issue_type', 'severity', 'is_resolved', 'reported_at']
    search_fields = ['service_name']
    readonly_fields = ['reported_at']
    date_hierarchy = 'reported_at'

    actions = ['mark_as_resolved']

    def issue_type_badge(self, obj):
        colors = {
            'outage': '#dc3545',
            'slow': '#ffc107',
            'intermittent': '#17a2b8'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.issue_type, '#6c757d'),
            obj.get_issue_type_display()
        )

    issue_type_badge.short_description = 'Muammo turi'

    def severity_badge(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.severity, '#6c757d'),
            obj.get_severity_display()
        )

    severity_badge.short_description = 'Jiddiylik'

    def status_badge(self, obj):
        if obj.is_resolved:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">Hal qilindi</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">Faol</span>'
        )

    status_badge.short_description = 'Holat'

    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{updated} ta muammo hal qilindi deb belgilandi.')

    mark_as_resolved.short_description = "Tanlangan muammolarni hal qilindi deb belgilash"