from django.contrib import admin
from .models import User, TopicDatabase, MeetingDatabase, StudioLinkDatabase, PayoutMethod, Transaction, UserMeetingHistory

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'whatsapp_number', 'is_active', 'created_at')
    search_fields = ('email', 'name', 'whatsapp_number')

@admin.register(TopicDatabase)
class TopicDatabaseAdmin(admin.ModelAdmin):
    list_display = ('topic_id', 'topic_name', 'is_done')
    search_fields = ('topic_id', 'topic_name')

@admin.register(StudioLinkDatabase)
class StudioLinkDatabaseAdmin(admin.ModelAdmin):
    list_display = ('name_id', 'email1', 'email2', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('name_id', 'email1', 'email2')
    actions = ['mark_as_not_used']

    @admin.action(description='Mark selected links as Not Used')
    def mark_as_not_used(self, request, queryset):
        updated = queryset.update(is_used=False)
        self.message_user(request, f'{updated} studio links were successfully marked as Not Used.')

@admin.register(MeetingDatabase)
class MeetingDatabaseAdmin(admin.ModelAdmin):
    list_display = (
        'meeting_id', 'status', 'meeting_url', 'topic', 'host_name', 'host_age', 'host_gender', 'get_host_location',
        'guest_name', 'guest_age', 'guest_gender', 'get_guest_location'
    )
    list_display_links = ('meeting_id', 'meeting_url')
    list_filter = ('status', 'created_at')
    search_fields = ('meeting_id', 'meeting_url', 'host_name', 'guest_name', 'host_mail_id', 'guest_mail_id')

    def get_host_location(self, obj):
        return obj.host_dist
    get_host_location.short_description = 'Host location'

    def get_guest_location(self, obj):
        return obj.guest_dist
    get_guest_location.short_description = 'Guest location'

@admin.register(PayoutMethod)
class PayoutMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'created_at')
    list_filter = ('method_type',)
    search_fields = ('user__email', 'user__name', 'upi_id', 'account_number')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'status', 'date')
    list_filter = ('transaction_type', 'status', 'date')
    search_fields = ('user__email', 'user__name', 'comments')
    readonly_fields = ('user_payout_details',)

    def user_payout_details(self, obj):
        payouts = PayoutMethod.objects.filter(user=obj.user)
        if payouts.exists():
            details = []
            for p in payouts:
                if p.method_type == 'upi':
                    details.append(f"UPI: {p.upi_id} (Name: {p.upi_name})")
                else:
                    details.append(f"Bank: {p.bank_name}, A/c: {p.account_number}, IFSC: {p.ifsc_code}, Name: {p.account_holder_name}")
            return " | ".join(details)
        return "No payout details added by user yet."
    user_payout_details.short_description = "User Payout Method Details"

@admin.register(UserMeetingHistory)
class UserMeetingHistoryAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'script_count')
    search_fields = ('user1__email', 'user2__email')
