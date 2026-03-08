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

@admin.register(MeetingDatabase)
class MeetingDatabaseAdmin(admin.ModelAdmin):
    list_display = (
        'meeting_url', 'topic', 'host_name', 'host_age', 'host_gender', 'get_host_location',
        'guest_name', 'guest_age', 'guest_gender', 'get_guest_location'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('meeting_url', 'host_name', 'guest_name', 'host_mail_id', 'guest_mail_id')

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

@admin.register(UserMeetingHistory)
class UserMeetingHistoryAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'script_count')
    search_fields = ('user1__email', 'user2__email')
