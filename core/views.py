import random
import re
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils import timezone
from django.db import transaction
from .models import User, OTPVerification, TopicDatabase, MeetingDatabase, StudioLinkDatabase, PayoutMethod, Transaction, UserMeetingHistory

def index(request):
    return render(request, 'core/index.html')

def terms(request):
    return render(request, 'core/terms.html')



def signup(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_number = request.POST.get('contact_number')
        same_whatsapp = request.POST.get('same_whatsapp') == 'on'
        whatsapp_number = request.POST.get('whatsapp_number')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        district = request.POST.get('district')
        email = request.POST.get('email')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            OTPVerification.objects.filter(user=user).delete()
            otp_code = str(random.randint(100000, 999999))
            OTPVerification.objects.create(user=user, otp_code=otp_code)
            
            send_mail(
                'Welcome Back to Biswas Tech – OTP Verification',
                f'Welcome back to Biswas Tech.\n\nThis is a simple Bengali recording project.\nYou will read a script with another participant.\n\nYour Secret OTP Code:\n\n        {otp_code}\n\nPlease enter this OTP to verify your account.',
                'noreply@biswastech.com',
                [email],
                fail_silently=False,
            )
            request.session['verification_email'] = email
            return redirect('verify_otp')

        user = User.objects.create(
            name=name,
            contact_number=contact_number,
            whatsapp_number=whatsapp_number,
            is_whatsapp_same=same_whatsapp,
            gender=gender,
            date_of_birth=date_of_birth,
            district=district,
            email=email
        )

        # Generate and send OTP
        otp_code = str(random.randint(100000, 999999))
        OTPVerification.objects.create(user=user, otp_code=otp_code)
        
        send_mail(
            'Welcome to Biswas Tech – OTP Verification',
            f'Welcome to Biswas Tech.\n\nThis is a simple Bengali recording project.\nYou will read a script with another participant.\n\nYour Secret OTP Code:\n\n        {otp_code}\n\nPlease enter this OTP to verify your account.',
            'noreply@biswastech.com',
            [email],
            fail_silently=False,
        )

        request.session['verification_email'] = email
        return redirect('verify_otp')
    return render(request, 'core/signup.html')

def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            # Generate and send OTP
            OTPVerification.objects.filter(user=user).delete()
            otp_code = str(random.randint(100000, 999999))
            OTPVerification.objects.create(user=user, otp_code=otp_code)
            
            send_mail(
                'Biswas Tech – Login OTP Verification',
                f'Your Secret OTP Code:\n\n        {otp_code}\n\nPlease enter this OTP to verify your account.',
                'noreply@biswastech.com',
                [email],
                fail_silently=False,
            )
            
            request.session['verification_email'] = email
            return redirect('verify_otp')
        except User.DoesNotExist:
            return render(request, 'core/login.html', {'error': 'Email not found.'})
    return render(request, 'core/login.html')

def verify_otp(request):
    email = request.session.get('verification_email')
    if not email:
        return redirect('login')

    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            user = User.objects.get(email=email)
            verification = OTPVerification.objects.filter(user=user).last()
            
            if verification and verification.otp_code == otp and verification.is_valid():
                user.is_active = True
                user.save()
                login(request, user)
                verification.delete()
                del request.session['verification_email']
                return redirect('dashboard')
            else:
                return render(request, 'core/verify_otp.html', {'error': 'Invalid or expired OTP.'})
        except User.DoesNotExist:
            return redirect('login')

    return render(request, 'core/verify_otp.html', {'email': email})

def resend_otp(request):
    if request.method == 'POST':
        email = request.session.get('verification_email')
        if not email:
            return redirect('login')
        try:
            user = User.objects.get(email=email)
            OTPVerification.objects.filter(user=user).delete()
            otp_code = str(random.randint(100000, 999999))
            OTPVerification.objects.create(user=user, otp_code=otp_code)
            
            send_mail(
                'Biswas Tech – Resend OTP Verification',
                f'Your Secret OTP Code is:\n\n        {otp_code}\n\nPlease enter this OTP to verify your account.',
                'noreply@biswastech.com',
                [email],
                fail_silently=False,
            )
            return render(request, 'core/verify_otp.html', {'email': email, 'message': 'OTP has been resent successfully.'})
        except User.DoesNotExist:
            return redirect('login')
    return redirect('login')

@login_required
def dashboard(request):
    from django.db.models import Q
    
    # If user comes to dashboard, cancel any of their active meetings (reconnect disabled)
    active = MeetingDatabase.objects.filter(
        Q(host_mail_id=request.user.email) | Q(guest_mail_id=request.user.email),
        status__in=['paired', 'searching']
    ).first()
    if active:
        active.status = 'expired'
        active.save()
        if active.valid_script_count == 0 and active.meeting_url:
            try:
                link = StudioLinkDatabase.objects.get(meeting_url=active.meeting_url)
                link.is_used = False
                link.save()
            except: pass
            if active.topic:
                active.topic.is_done = False
                active.topic.save()

    meetings = []
    if request.user.is_staff:
        # Show all meeting info with data_taken checkbox for admin
        meetings = MeetingDatabase.objects.all().order_by('-created_at')[:20]

    return render(request, 'core/dashboard.html', {'user': request.user, 'meetings': meetings})

@login_required
def payment_dashboard(request):
    user = request.user
    message = None
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_payout':
            method_type = request.POST.get('method_type')
            if method_type == 'upi':
                 PayoutMethod.objects.create(
                     user=user, method_type='upi',
                     upi_name=request.POST.get('upi_name'),
                     upi_id=request.POST.get('upi_id')
                 )
            elif method_type == 'bank':
                 PayoutMethod.objects.create(
                     user=user, method_type='bank',
                     bank_name=request.POST.get('bank_name'),
                     account_holder_name=request.POST.get('account_holder_name'),
                     account_number=request.POST.get('account_number'),
                     ifsc_code=request.POST.get('ifsc_code')
                 )
            message = "Payout method added successfully!"
        elif action == 'withdraw':
            if user.balance >= 150:
                amount = float(request.POST.get('withdraw_amount', 0))
                if 150 <= amount <= user.balance:
                    Transaction.objects.create(
                        user=user, amount=amount,
                        transaction_type='Debit',
                        comments='Withdrawal Request',
                        status='Pending'
                    )
                    user.balance -= amount
                    user.save()
                    message = "Withdrawal request submitted successfully!"
                else:
                    message = "Invalid amount."
            else:
                message = "You can only withdraw 150 or more."

    payout_methods = PayoutMethod.objects.filter(user=user)
    transactions = Transaction.objects.filter(user=user).order_by('-date')
    return render(request, 'core/payment_dashboard.html', {
        'user': user,
        'payout_methods': payout_methods,
        'transactions': transactions,
        'message': message
    })

@login_required
def start_recording(request):
    # Expire old searching meetings
    old_searching = MeetingDatabase.objects.filter(status='searching', created_at__lt=timezone.now() - timezone.timedelta(seconds=130))
    old_searching.update(status='timeout')

    # Auto-release old USED links if they haven't been touched in 1 hour
    one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
    StudioLinkDatabase.objects.filter(is_used=True, last_used_time__lt=one_hour_ago).update(is_used=False)

    # Remove any existing meeting tracking to start fresh
    if 'current_meeting' in request.session:
        del request.session['current_meeting']

    with transaction.atomic():
        new_meeting = MeetingDatabase.objects.create(
            host_mail_id=request.user.email,
            host_name=request.user.name,
            host_age=request.user.date_of_birth.year if request.user.date_of_birth else None,
            host_gender=request.user.gender,
            host_dist=request.user.district,
            status='searching'
        )
        
        candidates = MeetingDatabase.objects.filter(status='searching').exclude(meeting_id=new_meeting.meeting_id).order_by('created_at').select_for_update()
        valid_candidates = list(candidates)
        
        if not valid_candidates:
            available_link = StudioLinkDatabase.objects.filter(is_used=False).first()
            if available_link:
                available_link.is_used = True
                available_link.last_used_time = timezone.now()
                available_link.save()
                
                new_meeting.meeting_url = available_link.meeting_url
                new_meeting.studio_host_email = available_link.email1
                new_meeting.studio_guest_email = available_link.email2
                new_meeting.save()
        else:
            meeting = new_meeting
            matched_candidate = valid_candidates[0]
            
            matched_candidate.status = 'paired'
            matched_candidate.guest_mail_id = meeting.host_mail_id
            matched_candidate.guest_name = meeting.host_name
            matched_candidate.guest_age = meeting.host_age
            matched_candidate.guest_gender = meeting.host_gender
            matched_candidate.guest_dist = meeting.host_dist
            
            meeting.status = 'joined_other'
            meeting.joined_meeting_id = str(matched_candidate.meeting_id)
            
            assigned_url = matched_candidate.meeting_url
                    
            if assigned_url:
                link_db = StudioLinkDatabase.objects.filter(meeting_url=assigned_url).first()
                if link_db and link_db.topic_category:
                    topics = list(TopicDatabase.objects.filter(is_done=False, topic_name=link_db.topic_category))
                else:
                    topics = list(TopicDatabase.objects.filter(is_done=False))
                    
                if not topics and link_db and link_db.topic_category:
                    topics = list(TopicDatabase.objects.filter(is_done=False))

                if topics:
                    selected_topic = random.choice(topics)
                    selected_topic.is_done = True
                    selected_topic.save()
                    matched_candidate.topic = selected_topic
                    matched_candidate.last_script_change_time = timezone.now()
                    matched_candidate.valid_script_count = 0
                    matched_candidate.played_topic_ids_comma_separated = selected_topic.topic_id
                    matched_candidate.save()
                    matched_candidate.played_topics.add(matched_candidate.topic)
                    matched_candidate.save()
                    meeting.save()
                else:
                    if link_db:
                        link_db.is_used = False
                        link_db.save()
                    matched_candidate.status = 'expired'
                    matched_candidate.save()
                    meeting.status = 'expired'
                    meeting.save()
                    msg = "Something went wrong! No script available for this topic. Please go to the dashboard and search another partner"
                    
                    try:
                        cat_name = link_db.topic_category if (link_db and link_db.topic_category) else "Unknown"
                        from django.core.mail import send_mail
                        send_mail(f'Alert: No More Scripts for {cat_name}', msg, 'noreply@biswastech.com', ['koushik271999@gmail.com'], fail_silently=True)
                    except: pass
                    
                    return render(request, 'core/meeting_error.html', {'error': msg})

        request.session['current_meeting'] = str(new_meeting.meeting_id)

    return redirect('recording_room')

@login_required
def recording_room(request):
    meeting_id = request.session.get('current_meeting')
    if not meeting_id:
        return redirect('dashboard')

    try:
        meeting = MeetingDatabase.objects.get(meeting_id=meeting_id)
        if meeting.status in ['completed', 'expired']:
            del request.session['current_meeting']
            return render(request, 'core/meeting_error.html', {'error': 'Meeting expired or completed.'})
            
        if meeting.status == 'timeout':
            del request.session['current_meeting']
            return render(request, 'core/meeting_error.html', {'error': 'Currently no users are here, pls search after 15 minutes.'})
            
        if meeting.status == 'joined_other':
            meeting_id = meeting.joined_meeting_id
            request.session['current_meeting'] = meeting_id
            meeting = MeetingDatabase.objects.get(meeting_id=meeting_id)
            
        return render(request, 'core/recording_room.html', {'meeting': meeting})
    except MeetingDatabase.DoesNotExist:
        return redirect('dashboard')

@login_required
def meeting_status_api(request):
    meeting_id = request.GET.get('meeting_id')
    try:
        meeting = MeetingDatabase.objects.get(meeting_id=meeting_id)
        
        now_time = timezone.now()
        is_host = (request.user.email == meeting.host_mail_id)
        
        # Update heartbeat
        if is_host:
            meeting.host_last_heartbeat = now_time
        else:
            meeting.guest_last_heartbeat = now_time
        meeting.save()

        if meeting.status in ['expired', 'completed']:
            err_msg = "Your partner joined and left the room, or the meeting ended."
            if not meeting.topic and meeting.status == 'expired':
                err_msg = "Something went wrong! No script available for this topic. Please go to the dashboard and search another partner"
            return JsonResponse({'status': meeting.status, 'error': err_msg})

        # Check partner disconnect if paired
        partner_disconnected = False
        if meeting.status == 'paired':
            other_heartbeat = meeting.guest_last_heartbeat if is_host else meeting.host_last_heartbeat
            time_since_pairing = (now_time - meeting.last_script_change_time).total_seconds() if meeting.last_script_change_time else 0
            disconnected_time = (now_time - other_heartbeat).total_seconds() if other_heartbeat else time_since_pairing
            
            if time_since_pairing < 120:
                if disconnected_time > 45:
                    meeting.status = 'expired'
                    meeting.save()
                    if meeting.valid_script_count == 0 and meeting.meeting_url:
                        try:
                            link = StudioLinkDatabase.objects.get(meeting_url=meeting.meeting_url)
                            link.is_used = False
                            link.save()
                        except StudioLinkDatabase.DoesNotExist:
                            pass
                        if meeting.topic:
                            meeting.topic.is_done = False
                            meeting.topic.save()
                    return JsonResponse({'status': 'expired', 'error': 'Your partner joined and left the room.'})
            else:
                if disconnected_time > 45:
                    partner_disconnected = True
                
                if disconnected_time > 600:
                    meeting.status = 'expired'
                    meeting.save()
                    if meeting.valid_script_count == 0 and meeting.meeting_url:
                        try:
                            link = StudioLinkDatabase.objects.get(meeting_url=meeting.meeting_url)
                            link.is_used = False
                            link.save()
                        except StudioLinkDatabase.DoesNotExist:
                            pass
                        if meeting.topic:
                            meeting.topic.is_done = False
                            meeting.topic.save()
                    return JsonResponse({'status': 'expired', 'error': 'Partner disconnected for too long'})

        if meeting.status == 'searching':
            diff_seconds = (now_time - meeting.created_at).total_seconds()
            if diff_seconds >= 120:
                meeting.status = 'timeout'
                meeting.save()
                return JsonResponse({'status': 'timeout'})
            else:
                with transaction.atomic():
                    meeting = MeetingDatabase.objects.select_for_update().get(meeting_id=meeting.meeting_id)
                    if meeting.status != 'searching':
                        return JsonResponse({'status': meeting.status, 'joined_meeting_id': meeting.joined_meeting_id})
                        
                    candidates = MeetingDatabase.objects.filter(status='searching').exclude(meeting_id=meeting.meeting_id).order_by('created_at').select_for_update()
                    valid_candidates = list(candidates)
                    
                    if valid_candidates:
                        matched_candidate = None
                        best_history = None
                        
                        try:
                            u1 = User.objects.get(email=meeting.host_mail_id)
                            for cand in valid_candidates:
                                try:
                                    u2 = User.objects.get(email=cand.host_mail_id)
                                    h1 = UserMeetingHistory.objects.filter(user1=u1, user2=u2).first()
                                    h2 = UserMeetingHistory.objects.filter(user1=u2, user2=u1).first()
                                    history = h1 or h2
                                    if history and 1 <= history.script_count <= 25:
                                        if best_history is None or history.script_count < best_history.script_count:
                                            best_history = history
                                            matched_candidate = cand
                                except User.DoesNotExist:
                                    pass
                        except User.DoesNotExist:
                            pass
                        
                        if not matched_candidate:
                            matched_candidate = valid_candidates[0]
                            
                        assigned_url = None
                        if best_history:
                            is_u1_host = (meeting.host_mail_id == best_history.last_host.email)
                            link_db = StudioLinkDatabase.objects.filter(meeting_url=best_history.last_meeting_url).first()
                            
                            if is_u1_host:
                                meeting.status = 'paired'
                                meeting.guest_mail_id = matched_candidate.host_mail_id
                                meeting.guest_name = matched_candidate.host_name
                                meeting.guest_age = matched_candidate.host_age
                                meeting.guest_gender = matched_candidate.host_gender
                                meeting.guest_dist = matched_candidate.host_dist
                                meeting.meeting_url = best_history.last_meeting_url
                                if link_db:
                                    meeting.studio_host_email = link_db.email1
                                    meeting.studio_guest_email = link_db.email2
                                    link_db.last_used_time = timezone.now()
                                    link_db.save()
                                matched_candidate.status = 'joined_other'
                                matched_candidate.joined_meeting_id = str(meeting.meeting_id)
                            else:
                                matched_candidate.status = 'paired'
                                matched_candidate.guest_mail_id = meeting.host_mail_id
                                matched_candidate.guest_name = meeting.host_name
                                matched_candidate.guest_age = meeting.host_age
                                matched_candidate.guest_gender = meeting.host_gender
                                matched_candidate.guest_dist = meeting.host_dist
                                matched_candidate.meeting_url = best_history.last_meeting_url
                                if link_db:
                                    matched_candidate.studio_host_email = link_db.email1
                                    matched_candidate.studio_guest_email = link_db.email2
                                    link_db.last_used_time = timezone.now()
                                    link_db.save()
                                meeting.status = 'joined_other'
                                meeting.joined_meeting_id = str(matched_candidate.meeting_id)
                            assigned_url = best_history.last_meeting_url
                        else:
                            available_link = StudioLinkDatabase.objects.filter(is_used=False).first()
                            if available_link:
                                available_link.is_used = True
                                available_link.last_used_time = timezone.now()
                                available_link.save()
                                
                                matched_candidate.status = 'paired'
                                matched_candidate.guest_mail_id = meeting.host_mail_id
                                matched_candidate.guest_name = meeting.host_name
                                matched_candidate.guest_age = meeting.host_age
                                matched_candidate.guest_gender = meeting.host_gender
                                matched_candidate.guest_dist = meeting.host_dist
                                matched_candidate.studio_host_email = available_link.email1
                                matched_candidate.studio_guest_email = available_link.email2
                                matched_candidate.meeting_url = available_link.meeting_url
                                
                                meeting.status = 'joined_other'
                                meeting.joined_meeting_id = str(matched_candidate.meeting_id)
                                assigned_url = available_link.meeting_url
                            else:
                                return JsonResponse({'status': 'searching'})
                                
                        paired_meeting = meeting if meeting.status == 'paired' else matched_candidate
                        
                        # Find topic using the assigned link
                        link_db = StudioLinkDatabase.objects.filter(meeting_url=assigned_url).first()
                        if link_db and link_db.topic_category:
                            topics = list(TopicDatabase.objects.filter(is_done=False, topic_name=link_db.topic_category))
                        else:
                            topics = list(TopicDatabase.objects.filter(is_done=False))
                            
                        if not topics and link_db and link_db.topic_category:
                            # fallback to any topic
                            topics = list(TopicDatabase.objects.filter(is_done=False))

                        if topics:
                            selected_topic = random.choice(topics)
                            selected_topic.is_done = True
                            selected_topic.save()
                            paired_meeting.topic = selected_topic
                            paired_meeting.last_script_change_time = timezone.now()
                            paired_meeting.valid_script_count = 0
                            paired_meeting.played_topic_ids_comma_separated = selected_topic.topic_id
                            paired_meeting.save()
                            paired_meeting.played_topics.add(paired_meeting.topic)
                            paired_meeting.save()
                        else:
                            paired_meeting.status = 'expired'
                            if assigned_url:
                                try:
                                    link = StudioLinkDatabase.objects.get(meeting_url=assigned_url)
                                    link.is_used = False
                                    link.save()
                                except StudioLinkDatabase.DoesNotExist: pass
                            paired_meeting.save()
                            
                            try:
                                cat_name = link_db.topic_category if (link_db and link_db.topic_category) else "Unknown"
                                from django.core.mail import send_mail
                                send_mail(f'Alert: No More Scripts for {cat_name}', 'No script available.', 'noreply@biswastech.com', ['koushik271999@gmail.com'], fail_silently=True)
                            except: pass

                        if matched_candidate != paired_meeting:
                            matched_candidate.save()
                        if meeting != paired_meeting:
                            meeting.save()

            return JsonResponse({'status': meeting.status, 'joined_meeting_id': meeting.joined_meeting_id})

        script_html = ''
        topic_id = None
        if meeting.topic:
            topic_id = meeting.topic.topic_id
            
            # Skip generating the entire script HTML if the client already has it
            client_topic_id = request.GET.get('topic_id')
            if str(client_topic_id) != str(topic_id):
                raw_script = meeting.topic.script
                lines = raw_script.split('\n')
                formatted_lines = []
                current_speaker = None
                is_host = (request.user.email == meeting.host_mail_id)
                
                for line in lines:
                    if not line.strip():
                        formatted_lines.append('<br>')
                        continue
                    
                    if re.match(r'(?i)^Host\s*:', line):
                        current_speaker = 'host'
                        line = re.sub(r'(?i)^Host\s*:', f'<b>{meeting.host_name}</b>:', line)
                    elif re.match(r'(?i)^Guest\s*:', line):
                        current_speaker = 'guest'
                        h_name = meeting.guest_name if meeting.guest_name else "Guest"
                        line = re.sub(r'(?i)^Guest\s*:', f'<b>{h_name}</b>:', line)
                
                    if current_speaker == 'host':
                        if is_host:
                            formatted_lines.append(f'<div class="highlight-me">{line}</div>')
                        else:
                            formatted_lines.append(f'<div class="highlight-other">{line}</div>')
                    elif current_speaker == 'guest':
                        if is_host:
                            formatted_lines.append(f'<div class="highlight-other">{line}</div>')
                        else:
                            formatted_lines.append(f'<div class="highlight-me">{line}</div>')
                    else:
                        formatted_lines.append(f'<div>{line}</div>')
                        
                script_html = "".join(formatted_lines)

        script_count = meeting.played_topics.count()
        # Fallback to 1 if count is somehow 0 but topic exists
        if script_count == 0 and meeting.topic:
            script_count = 1

        is_host = (request.user.email == meeting.host_mail_id)
        # Identify partner name
        partner_name = ""
        if is_host:
            partner_name = meeting.guest_name if meeting.guest_name else "Waiting for partner..."
        else:
            partner_name = meeting.host_name if meeting.host_name else "Host"
            
        # Send correct email to correct side
        user_studio_email = meeting.studio_host_email if is_host else meeting.studio_guest_email

        return JsonResponse({
            'status': 'paired',
            'partner_name': meeting.guest_name if is_host else meeting.host_name,
            'meeting_url': meeting.meeting_url,
            'user_studio_email': user_studio_email, # Provide correct email
            'script_html': script_html,
            'script_number': meeting.valid_script_count + 1,
            'topic_id': topic_id,
            'partner_disconnected': partner_disconnected,
            'both_done': (meeting.host_done_script and meeting.guest_done_script)
        })
    except MeetingDatabase.DoesNotExist:
        return JsonResponse({'status': 'expired', 'error': 'Not found'}, status=404)

@login_required
def leave_meeting_api(request):
    if request.method == 'POST':
        meeting_id = request.POST.get('meeting_id')
        try:
            meeting = MeetingDatabase.objects.get(meeting_id=meeting_id)
            if meeting.status in ['waiting', 'paired', 'searching']:
                meeting.status = 'expired' # Expire it so partner knows
                meeting.save()
                
                # Make link reusable if no script was fully done
                if meeting.valid_script_count == 0 and meeting.meeting_url:
                    try:
                        link = StudioLinkDatabase.objects.get(meeting_url=meeting.meeting_url)
                        link.is_used = False
                        link.save()
                    except StudioLinkDatabase.DoesNotExist:
                        pass
                    if meeting.topic:
                        meeting.topic.is_done = False
                        meeting.topic.save()
                        
            return JsonResponse({'success': True})
        except MeetingDatabase.DoesNotExist:
            pass
    return JsonResponse({'success': False})

@login_required
def done_script_api(request):
    if request.method == 'POST':
        meeting_id = request.POST.get('meeting_id')
        try:
            with transaction.atomic():
                meeting = MeetingDatabase.objects.select_for_update().get(meeting_id=meeting_id)
                is_host = (request.user.email == meeting.host_mail_id)
                changed = False
                
                if is_host:
                    if not meeting.host_done_script:
                        meeting.host_done_script = True
                        changed = True
                else:
                    if not meeting.guest_done_script:
                        meeting.guest_done_script = True
                        changed = True
                
                if changed:
                    meeting.save()
                    
                # If BOTH are done, trigger script completion logic
                if meeting.host_done_script and meeting.guest_done_script:
                    
                    # Add pending balance
                    from decimal import Decimal
                    try:
                        host_user = User.objects.get(email=meeting.host_mail_id)
                        guest_user = User.objects.get(email=meeting.guest_mail_id)
                        host_user.pending_balance += Decimal('6.00')
                        guest_user.pending_balance += Decimal('6.00')
                        host_user.save()
                        guest_user.save()
                        
                        # Add tracking transactions (optional but user requested comment)
                        Transaction.objects.create(
                            user=host_user, amount=6.00,
                            transaction_type='Credit',
                            comments=f'1 Script done on {meeting.meeting_url}',
                            status='Success'
                        )
                        Transaction.objects.create(
                            user=guest_user, amount=6.00,
                            transaction_type='Credit',
                            comments=f'1 Script done on {meeting.meeting_url}',
                            status='Success'
                        )
                    except Exception as e:
                        pass
                        
                    # Mark link as used specifically when a script is successfully done
                    try:
                        link_ob = StudioLinkDatabase.objects.get(meeting_url=meeting.meeting_url)
                        if not link_ob.is_used:
                            link_ob.is_used = True
                            link_ob.save()
                    except: pass
                        
                    meeting.valid_script_count += 1
                    meeting.host_done_script = False
                    meeting.guest_done_script = False
                    
                    if meeting.valid_script_count >= 5:
                        meeting.status = 'completed'
                        meeting.save()
                        return JsonResponse({'success': True, 'completed': True, 'msg': 'Max 5 scripts done!'})
                        
                    now = timezone.now()
                    
                    topics = []
                    link_db = StudioLinkDatabase.objects.filter(meeting_url=meeting.meeting_url).first()
                    if link_db and link_db.topic_category:
                        topics = list(TopicDatabase.objects.filter(is_done=False, topic_name=link_db.topic_category))
                    else:
                        topics = list(TopicDatabase.objects.filter(is_done=False))
                        
                    if topics:
                        new_topic = random.choice(topics)
                        new_topic.is_done = True
                        new_topic.save()
                        
                        meeting.topic = new_topic
                        meeting.last_script_change_time = now
                        if meeting.played_topic_ids_comma_separated:
                            meeting.played_topic_ids_comma_separated += f",{new_topic.topic_id}"
                        else:
                            meeting.played_topic_ids_comma_separated = new_topic.topic_id
                        meeting.save()
                        meeting.played_topics.add(meeting.topic)
                        
                        try:
                            h_user = User.objects.get(email=meeting.host_mail_id)
                            g_user = User.objects.get(email=meeting.guest_mail_id)
                            h_hist = UserMeetingHistory.objects.filter(user1=h_user, user2=g_user).first()
                            g_hist = UserMeetingHistory.objects.filter(user1=g_user, user2=h_user).first()
                            hist = h_hist or g_hist
                            if hist:
                                hist.script_count += 1
                                hist.save()
                            else:
                                UserMeetingHistory.objects.create(
                                    user1=h_user, user2=g_user, script_count=1,
                                    last_meeting_url=meeting.meeting_url,
                                    last_host=h_user, last_guest=g_user
                                )
                        except Exception: pass
                        
                        return JsonResponse({'success': True, 'next_script': True})
                    else:
                        meeting.status = 'completed'
                        meeting.save()
                        
                        # Send email
                        try:
                            cat_name = link_db.topic_category if (link_db and link_db.topic_category) else "Unknown"
                            send_mail(
                                f'Alert: No More Scripts for {cat_name}',
                                f'Warning! Users have exhausted all scripts for the topic: {cat_name}.\n\nPlease upload more scripts immediately.',
                                'noreply@biswastech.com',
                                ['koushik271999@gmail.com'],
                                fail_silently=True,
                            )
                        except Exception: pass
                        
                        return JsonResponse({'success': True, 'empty_redirect': True, 'error': 'No more scripts available for this category!'})
                        
                return JsonResponse({'success': True, 'waiting_partner': True})
        except MeetingDatabase.DoesNotExist:
            pass
    return JsonResponse({'success': False})

@login_required
def next_script_api(request):
    return JsonResponse({'success': False, 'empty_redirect': True, 'error': 'Function deprecated'})
