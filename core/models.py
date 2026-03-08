import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ]

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    whatsapp_number = models.CharField(max_length=20)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    district = models.CharField(max_length=100)
    
    contact_number = models.CharField(max_length=20, null=True, blank=True)
    user_uuid = models.UUIDField(default=uuid.uuid4, editable=False, null=True)
    is_whatsapp_same = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    is_active = models.BooleanField(default=False) # Will become True after OTP verification
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

class OTPVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        now = timezone.now()
        diff = now - self.created_at
        return diff.total_seconds() <= 300 # 5 minutes expiry

class StudioLinkDatabase(models.Model):
    name_id = models.CharField(max_length=255)
    email1 = models.EmailField() # Host Studio Email
    email2 = models.EmailField() # Guest Studio Email
    meeting_url = models.URLField(max_length=500)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return self.name_id

class TopicDatabase(models.Model):
    TOPIC_CHOICES = [
        ('ব্যবসা (Business)', 'ব্যবসা (Business)'),
        ('ব্যক্তিগত অর্থায়ন (Personal Finance)', 'ব্যক্তিগত অর্থায়ন (Personal Finance)'),
        ('কাস্টমার সাপোর্ট (Customer Support)', 'কাস্টমার সাপোর্ট (Customer Support)'),
        ('রাজনীতি (Politics)', 'রাজনীতি (Politics)'),
        ('ব্যাংকিং প্রশ্নাবলী (Banking)', 'ব্যাংকিং প্রশ্নাবলী (Banking)'),
        ('কল সেন্টার (Call Center)', 'কল সেন্টার (Call Center)'),
        ('খেলাধুলা (Sports)', 'খেলাধুলা (Sports)'),
        ('সংবাদপত্রে আসার মতো গুরুত্বপূর্ণ বিষয় (Newspaper-worthy topics)', 'সংবাদপত্রে আসার মতো গুরুত্বপূর্ণ বিষয় (Newspaper-worthy topics)'),
    ]
    topic_id = models.CharField(max_length=100, primary_key=True)
    topic_name = models.CharField(max_length=255, choices=TOPIC_CHOICES)
    script = models.TextField()
    is_done = models.BooleanField(default=False)

    def __str__(self):
        return self.topic_name

class MeetingDatabase(models.Model):
    STATUS_CHOICES = [
        ('searching', 'searching'),
        ('joined_other', 'joined_other'),
        ('waiting', 'waiting'),
        ('paired', 'paired'),
        ('completed', 'completed'),
        ('expired', 'expired'),
        ('timeout', 'timeout')
    ]
    
    joined_meeting_id = models.CharField(max_length=255, null=True, blank=True)

    meeting_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    host_mail_id = models.EmailField()
    guest_mail_id = models.EmailField(null=True, blank=True)
    meeting_url = models.URLField(max_length=500, blank=True)
    topic = models.ForeignKey(TopicDatabase, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting')
    created_at = models.DateTimeField(auto_now_add=True)

    studio_host_email = models.EmailField(null=True, blank=True)
    studio_guest_email = models.EmailField(null=True, blank=True)
    host_name = models.CharField(max_length=255, null=True, blank=True)
    guest_name = models.CharField(max_length=255, null=True, blank=True)
    host_age = models.IntegerField(null=True, blank=True)
    guest_age = models.IntegerField(null=True, blank=True)
    host_dist = models.CharField(max_length=100, null=True, blank=True)
    guest_dist = models.CharField(max_length=100, null=True, blank=True)
    host_gender = models.CharField(max_length=10, null=True, blank=True)
    guest_gender = models.CharField(max_length=10, null=True, blank=True)
    data_taken = models.BooleanField(default=False)
    
    host_done_script = models.BooleanField(default=False)
    guest_done_script = models.BooleanField(default=False)
    
    played_topics = models.ManyToManyField(TopicDatabase, related_name='played_in_meetings', blank=True)

    last_script_change_time = models.DateTimeField(null=True, blank=True)
    valid_script_count = models.IntegerField(default=0)
    played_topic_ids_comma_separated = models.TextField(blank=True, default='')
    
    # Heartbeat tracking to clean up disconnected users
    host_last_heartbeat = models.DateTimeField(null=True, blank=True)
    guest_last_heartbeat = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.meeting_id)

class PayoutMethod(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    method_type = models.CharField(max_length=20, choices=[('upi', 'UPI'), ('bank', 'Bank Transfer')])
    upi_name = models.CharField(max_length=255, null=True, blank=True)
    upi_id = models.CharField(max_length=255, null=True, blank=True)
    bank_name = models.CharField(max_length=255, null=True, blank=True)
    account_holder_name = models.CharField(max_length=255, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    ifsc_code = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=[('Credit', 'Credit'), ('Debit', 'Debit')])
    comments = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Success', 'Success'), ('Failed', 'Failed')], default='Pending')

class UserMeetingHistory(models.Model):
    user1 = models.ForeignKey(User, related_name='history_user1', on_delete=models.CASCADE)
    user2 = models.ForeignKey(User, related_name='history_user2', on_delete=models.CASCADE)
    script_count = models.IntegerField(default=0)
    last_meeting_url = models.URLField(max_length=500, blank=True)
    last_host = models.ForeignKey(User, related_name='history_last_host', on_delete=models.CASCADE, null=True, blank=True)
    last_guest = models.ForeignKey(User, related_name='history_last_guest', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ('user1', 'user2')

    def __str__(self):
        return f"{self.user1.name} and {self.user2.name}"
