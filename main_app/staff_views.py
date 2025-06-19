import json
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Q
from django.db import transaction

from .forms import *
from .models import *

def staff_home(request):
    print("staff here")
    professor = get_object_or_404(Professor, user=request.user)
    total_students = Student.objects.filter(department=professor.department).count()
    total_leave = LeaveReportStaff.objects.filter(professor=professor).count()
    subjects = Subject.objects.filter(taught_by=professor)
    total_subject = subjects.count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.subject_name)
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Staff Panel - ' + str(professor.user.last_name) + ' (' + str(professor.department) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, 'staff_template/home_content.html', context)

def staff_take_attendance(request):
    professor = get_object_or_404(Professor, user=request.user)
    subjects = Subject.objects.filter(taught_by=professor)
    batches = Batch.objects.all()
    
    today = timezone.now().date()
    todays_classes = Attendance.objects.filter(
        subject__taught_by=professor,
        date=today
    ).values('subject').distinct().count()
    
    context = {
        'subjects': subjects,
        'batches': batches,
        'page_title': 'Take Attendance',
        'today': today,
        'todays_classes': todays_classes
    }
    return render(request, 'staff_template/staff_take_attendance.html', context)

@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    batch_id = request.POST.get("batch_year") or request.POST.get("batch")
    date_str = request.POST.get('date')
    
    try:
        subject = get_object_or_404(Subject, pk=subject_id)
        batch = get_object_or_404(Batch, pk=batch_id)
        
        students = Student.objects.filter(
            semester=subject.semester,
            batch=batch
        ).select_related('user').order_by('roll_no')
        
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = timezone.now().date()
            
            existing_attendance_query = Attendance.objects.filter(
                subject=subject,
                student__batch=batch,
                date=selected_date
            )
            
            attendance_exists = existing_attendance_query.exists()
            
            student_data = []
            for student in students:
                total_classes = Attendance.objects.filter(
                    student=student, 
                    subject=subject
                ).count()
                
                present_classes = Attendance.objects.filter(
                    student=student, 
                    subject=subject, 
                    status=True
                ).count()
                
                attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
                
                attendance_status = None
                if attendance_exists:
                    try:
                        attendance_record = Attendance.objects.get(
                            student=student,
                            subject=subject,
                            date=selected_date
                        )
                        attendance_status = attendance_record.status
                    except Attendance.DoesNotExist:
                        attendance_status = None
                
                data = {
                    "id": student.pk,
                    "name": f"{student.roll_no} - {student.user.first_name} {student.user.last_name}",
                    "roll_no": student.roll_no,
                    "attendance_percentage": round(attendance_percentage, 1),
                    "total_classes": total_classes,
                    "profile_pic": student.user.profile_pic.url if student.user.profile_pic else None,
                    "attendance_status": attendance_status,
                    "is_past_date": selected_date < today,
                    "is_today": selected_date == today,
                    "has_attendance_record": attendance_status is not None
                }
                student_data.append(data)
            
            return JsonResponse({
                'students': json.dumps(student_data),
                'is_past_date': selected_date < today,
                'is_today': selected_date == today,
                'attendance_exists': attendance_exists,
                'selected_date': selected_date.strftime('%Y-%m-%d'),
                'total_students': len(student_data),
                'students_with_attendance': existing_attendance_query.count() if attendance_exists else 0
            })
            
        else:
            student_data = []
            for student in students:
                data = {
                    "id": student.pk,
                    "name": f"{student.roll_no} - {student.user.first_name} {student.user.last_name}"
                }
                student_data.append(data)
            
            return JsonResponse(student_data, safe=False)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def save_attendance(request):
    try:
        student_data = request.POST.get('student_ids')
        date_str = request.POST.get('date')
        subject_id = request.POST.get('subject')
        batch_id = request.POST.get('batch')
        
        if not all([student_data, date_str, subject_id, batch_id]):
            return JsonResponse({
                'success': False, 
                'error': 'Missing required fields'
            }, status=400)
        
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = timezone.now().date()
            
            if attendance_date > today:
                return JsonResponse({
                    'success': False, 
                    'error': 'Future dates are not allowed for attendance'
                }, status=400)
            
            if attendance_date < today:
                return JsonResponse({
                    'success': False, 
                    'error': 'Cannot save attendance for past dates. You can only view past records.'
                }, status=400)
                
        except ValueError:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid date format'
            }, status=400)
        
        batch = get_object_or_404(Batch, pk=batch_id)
        subject = get_object_or_404(Subject, pk=subject_id)
        professor = get_object_or_404(Professor, user=request.user)
        
        existing_attendance = Attendance.objects.filter(
            subject=subject,
            date=attendance_date,
            student__batch=batch
        ).exists()
        
        if existing_attendance and attendance_date == today:
            return JsonResponse({
                'success': False, 
                'error': "Today's attendance has already been recorded and cannot be modified.",
                'view_only': True
            }, status=400)
        
        try:
            students = json.loads(student_data)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid student data format'
            }, status=400)
        
        if attendance_date == today and not existing_attendance:
            created_count = 0
            
            for student_dict in students:
                student_id = student_dict.get('id')
                if not student_id:
                    continue
                    
                student = get_object_or_404(Student, pk=student_id)
                status_value = student_dict.get('status') == 1
                
                Attendance.objects.create(
                    student=student,
                    subject=subject,
                    date=attendance_date,
                    status=status_value,
                    marked_by=professor
                )
                created_count += 1

            return JsonResponse({
                'success': True,
                'message': f'Attendance saved successfully for {attendance_date.strftime("%B %d, %Y")}! {created_count} students recorded.',
                'created': created_count,
                'date': attendance_date.strftime("%B %d, %Y")
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Cannot save attendance for this date.'
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e)
        }, status=400)

@csrf_exempt
def mark_all_present(request):
    subject_id = request.POST.get('subject')
    batch_id = request.POST.get('batch')
    date = request.POST.get('date')
    
    try:
        subject = get_object_or_404(Subject, pk=subject_id)
        batch = get_object_or_404(Batch, pk=batch_id)
        professor = get_object_or_404(Professor, user=request.user)
        
        students = Student.objects.filter(semester=subject.semester, batch=batch)
        
        for student in students:
            Attendance.objects.update_or_create(
                student=student,
                subject=subject,
                date=date,
                defaults={
                    'status': True,
                    'marked_by': professor,
                    'marked_at': timezone.now()
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': f'All {students.count()} students marked as present!'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@csrf_exempt
def get_attendance_summary(request):
    subject_id = request.POST.get('subject')
    batch_id = request.POST.get('batch')
    
    try:
        subject = get_object_or_404(Subject, pk=subject_id)
        batch = get_object_or_404(Batch, pk=batch_id)
        
        students = Student.objects.filter(semester=subject.semester, batch=batch)
        total_students = students.count()
        
        recent_attendance = Attendance.objects.filter(
            subject=subject,
            student__batch=batch,
            date__gte=timezone.now().date() - timedelta(days=30)
        )
        
        total_classes = recent_attendance.values('date').distinct().count()
        total_present = recent_attendance.filter(status=True).count()
        average_attendance = (total_present / (total_students * total_classes) * 100) if total_classes > 0 else 0
        
        return JsonResponse({
            'total_students': total_students,
            'total_classes': total_classes,
            'average_attendance': round(average_attendance, 1),
            'subject_name': subject.subject_name
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def get_attendance_dates(request):
    subject_id = request.POST.get('subject')
    batch_id = request.POST.get('batch')
    
    try:
        subject = get_object_or_404(Subject, pk=subject_id)
        batch = get_object_or_404(Batch, pk=batch_id)
        
        dates = Attendance.objects.filter(
            subject=subject,
            student__batch=batch
        ).values('date').annotate(
            total_students=Count('student', distinct=True),
            present_count=Count('student', filter=Q(status=True)),
            absent_count=Count('student', filter=Q(status=False))
        ).order_by('-date')
        
        json_data = []
        for date_info in dates:
            date = date_info['date']
            data = {
                "date": str(date),
                "attendance_date": date.strftime("%Y-%m-%d (%A)"),
                "display_text": f"{date.strftime('%B %d, %Y (%A)')} - {date_info['present_count']}P/{date_info['absent_count']}A ({date_info['total_students']} total)",
                "total_students": date_info['total_students'],
                "present_count": date_info['present_count'],
                "absent_count": date_info['absent_count']
            }
            json_data.append(data)
        
        return JsonResponse(json.dumps(json_data), content_type='application/json', safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def get_student_attendance(request):
    attendance_date = request.POST.get('attendance_date')
    subject_id = request.POST.get('subject')
    batch_id = request.POST.get('batch')
    
    try:
        subject = get_object_or_404(Subject, pk=subject_id)
        batch = get_object_or_404(Batch, pk=batch_id)
        
        attendance_records = Attendance.objects.filter(
            date=attendance_date,
            subject=subject,
            student__batch=batch
        ).select_related('student__user').order_by('student__roll_no')
        
        student_data = []
        for attendance in attendance_records:
            total_classes = Attendance.objects.filter(
                student=attendance.student,
                subject=subject
            ).count()
            
            present_classes = Attendance.objects.filter(
                student=attendance.student,
                subject=subject,
                status=True
            ).count()
            
            attendance_percentage = (present_classes / total_classes * 100) if total_classes > 0 else 0
            
            data = {
                "id": attendance.student.pk,
                "name": f"{attendance.student.roll_no} - {attendance.student.user.first_name} {attendance.student.user.last_name}",
                "roll_no": attendance.student.roll_no,
                "status": attendance.status,
                "attendance_percentage": round(attendance_percentage, 1),
                "total_classes": total_classes,
                "profile_pic": attendance.student.user.profile_pic.url if attendance.student.user.profile_pic else None,
                "marked_by": f"{attendance.marked_by.user.first_name} {attendance.marked_by.user.last_name}" if attendance.marked_by else "System",
                "marked_at": attendance.created_at.strftime("%I:%M %p") if hasattr(attendance, 'created_at') else "Unknown"
            }
            student_data.append(data)
        
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def staff_update_attendance(request):
    professor = get_object_or_404(Professor, user=request.user)
    subjects = Subject.objects.filter(taught_by=professor)
    batches = Batch.objects.all()
    
    today = timezone.now().date()
    todays_classes_taken = Attendance.objects.filter(
        subject__taught_by=professor,
        date=today
    ).values('subject').distinct().count()
    
    total_subjects = subjects.count()
    
    context = {
        'subjects': subjects,
        'batches': batches,
        'page_title': 'Update Attendance',
        'professor': professor,
        'todays_classes_taken': todays_classes_taken,
        'total_subjects': total_subjects,
        'today': today,
    }
    return render(request, 'staff_template/staff_update_attendance.html', context)

def staff_apply_leave(request):
    professor = get_object_or_404(Professor, user=request.user)
    form = LeaveReportStaffForm(request.POST or None)
    
    leave_history = LeaveReportStaff.objects.filter(
        professor=professor
    ).order_by('-created_at')
    
    total_applications = leave_history.count() or 0
    pending_count = leave_history.filter(status=0).count() or 0
    approved_count = leave_history.filter(status=1).count() or 0
    rejected_count = leave_history.filter(status=-1).count() or 0
    
    context = {
        'form': form,
        'leave_history': leave_history,
        'page_title': 'Apply for Leave',
        'professor': professor,
        'total_applications': total_applications,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.professor = professor
                obj.save()
                messages.success(
                    request, 
                    f"Leave application for {obj.from_date} to {obj.to_date} has been submitted for review"
                )
                return redirect(reverse('staff_apply_leave'))
            except Exception as e:
                messages.error(request, f"Could not submit application: {str(e)}")
        else:
            messages.error(request, "Please correct the form errors below!")
    
    return render(request, "staff_template/staff_apply_leave.html", context)

def staff_feedback(request):
    professor = get_object_or_404(Professor, user=request.user)
    form = FeedbackStaffForm(request.POST or None)
    
    feedbacks = FeedbackStaff.objects.filter(professor=professor).order_by('-created_at')
    
    total_feedbacks = feedbacks.count()
    replied_feedbacks = feedbacks.exclude(reply__isnull=True).exclude(reply__exact='').count()
    pending_feedbacks = feedbacks.filter(reply__isnull=True).count() + feedbacks.filter(reply__exact='').count()
    
    context = {
        'form': form,
        'feedbacks': feedbacks,
        'page_title': 'Staff Feedback',
        'professor': professor,
        'total_feedbacks': total_feedbacks,
        'replied_feedbacks': replied_feedbacks,
        'pending_feedbacks': pending_feedbacks,
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.professor = professor
                obj.save()
                messages.success(request, "Your feedback has been submitted successfully and will be reviewed by administration.")
                return redirect(reverse('staff_feedback'))
            except Exception as e:
                messages.error(request, f"Could not submit feedback: {str(e)}")
        else:
            messages.error(request, "Please correct the form errors below!")
    
    return render(request, "staff_template/staff_feedback.html", context)

def staff_view_profile(request):
    professor = get_object_or_404(Professor, user=request.user)
    form = ProfessorEditForm(request.POST or None, request.FILES or None, instance=professor)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                user = professor.user
                if password != None:
                    user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.first_name = first_name
                user.last_name = last_name
                user.address = address
                user.gender = gender
                user.save()
                professor.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occurred While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)

@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")

def staff_view_notification(request):
    professor = get_object_or_404(Professor, user=request.user)
    
    notifications = NotificationStaff.objects.filter(professor=professor).order_by('-created_at')
    
    total_notifications = notifications.count()
    unread_notifications = notifications.filter(is_read=False).count()
    read_notifications = notifications.filter(is_read=True).count()
    
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)
    
    context = {
        'notifications': notifications,
        'page_title': "Notifications",
        'professor': professor,
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
        'current_filter': filter_type,
    }
    return render(request, "staff_template/staff_view_notification.html", context)

def staff_add_result(request):
    professor = get_object_or_404(Professor, user=request.user)
    subjects = Subject.objects.filter(taught_by=professor)
    batches = Batch.objects.all()
    
    context = {
        'page_title': 'Add/Update Results',
        'subjects': subjects,
        'batches': batches
    }

    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list') or request.POST.get('student')
            subject_id = request.POST.get('subject')
            
            if not student_id or not subject_id:
                messages.error(request, "Please select both student and subject")
                return redirect('staff_add_result')

            student = get_object_or_404(Student, pk=student_id)
            subject = get_object_or_404(Subject, pk=subject_id)
            
            saved_something = False
            
            theory_fields = ['ca1', 'ca2', 'ca3', 'end_sem']
            theory_data = {}
            
            for field in theory_fields:
                value = request.POST.get(field)
                if value and value.strip():
                    try:
                        theory_data[field] = int(value)
                    except ValueError:
                        messages.warning(request, f"Invalid value for {field}")
                        continue
            
            if theory_data:
                theory_marks, created = TheoryMarks.objects.get_or_create(
                    student=student, 
                    subject=subject,
                    defaults=theory_data
                )
                if not created:
                    for field, value in theory_data.items():
                        setattr(theory_marks, field, value)
                    theory_marks.save()
                
                saved_something = True
                action = "Created" if created else "Updated"
                messages.success(request, f"Theory marks {action.lower()} for {student.roll_no}")
            
            lab_fields = ['pca1', 'pca2', 'end_sem_practical']
            lab_data = {}
            
            for field in lab_fields:
                value = request.POST.get(field)
                if value and value.strip():
                    try:
                        lab_data[field] = int(value)
                    except ValueError:
                        messages.warning(request, f"Invalid value for {field}")
                        continue
            
            if lab_data:
                lab_marks, created = LabMarks.objects.get_or_create(
                    student=student, 
                    subject=subject,
                    defaults=lab_data
                )
                if not created:
                    for field, value in lab_data.items():
                        setattr(lab_marks, field, value)
                    lab_marks.save()
                
                saved_something = True
                action = "Created" if created else "Updated"
                messages.success(request, f"Lab marks {action.lower()} for {student.roll_no}")
            
            if saved_something:
                messages.success(request, f"Results updated for {student.roll_no} - {student.user.first_name} {student.user.last_name}")
            else:
                messages.warning(request, "No marks were provided to save")
                
        except Exception as e:
            messages.error(request, f"Error occurred: {str(e)}")
        
        return redirect('staff_add_result')

    return render(request, 'staff_template/staff_add_result.html', context)

@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        
        if not subject_id or not student_id:
            return JsonResponse({'error': 'Missing subject or student ID'}, status=400)
        
        student = get_object_or_404(Student, pk=student_id)
        subject = get_object_or_404(Subject, pk=subject_id)
        
        result_data = {
            'subject_type': subject.subject_type or 'Mixed',
            'theory': None,
            'lab': None,
            'has_theory': False,
            'has_lab': False
        }
        
        try:
            theory_result = TheoryMarks.objects.get(student=student, subject=subject)
            result_data['theory'] = {
                'ca1': theory_result.ca1 if theory_result.ca1 is not None else '',
                'ca2': theory_result.ca2 if theory_result.ca2 is not None else '',
                'ca3': theory_result.ca3 if theory_result.ca3 is not None else '',
                'end_sem': theory_result.end_sem if theory_result.end_sem is not None else '',
            }
            result_data['has_theory'] = True
        except TheoryMarks.DoesNotExist:
            result_data['theory'] = {
                'ca1': '', 'ca2': '', 'ca3': '', 'end_sem': ''
            }
        
        try:
            lab_result = LabMarks.objects.get(student=student, subject=subject)
            result_data['lab'] = {
                'pca1': lab_result.pca1 if lab_result.pca1 is not None else '',
                'pca2': lab_result.pca2 if lab_result.pca2 is not None else '',
                'end_sem_practical': lab_result.end_sem_practical if lab_result.end_sem_practical is not None else '',
            }
            result_data['has_lab'] = True
        except LabMarks.DoesNotExist:
            result_data['lab'] = {
                'pca1': '', 'pca2': '', 'end_sem_practical': ''
            }
        
        return JsonResponse(result_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def staff_add_lab_result(request):
    professor = get_object_or_404(Professor, user=request.user)
    subjects = Subject.objects.filter(taught_by=professor, subject_type='Lab')
    batches = Batch.objects.all()
    
    context = {
        'page_title': 'Lab Result Upload',
        'subjects': subjects,
        'batches': batches
    }

    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            pca1 = int(request.POST.get('pca1', 0))
            pca2 = int(request.POST.get('pca2', 0))
            end_sem_practical = int(request.POST.get('end_sem_practical', 0))

            student = get_object_or_404(Student, pk=student_id)
            subject = get_object_or_404(Subject, pk=subject_id)

            if pca1 > 50 or pca2 > 50 or end_sem_practical > 100:
                messages.error(request, "Scores exceed maximum allowed values")
                return redirect('staff_add_lab_result')

            try:
                data = LabMarks.objects.get(student=student, subject=subject)
                data.pca1 = pca1
                data.pca2 = pca2
                data.end_sem_practical = end_sem_practical
                data.save()
                messages.success(request, f"Lab Scores Updated for {student.user.first_name} {student.user.last_name}")
            except LabMarks.DoesNotExist:
                result = LabMarks(
                    student=student,
                    subject=subject,
                    pca1=pca1,
                    pca2=pca2,
                    end_sem_practical=end_sem_practical
                )
                result.save()
                messages.success(request, f"Lab Scores Saved for {student.user.first_name} {student.user.last_name}")
                
        except ValueError:
            messages.error(request, "Please enter valid numeric scores")
        except Exception as e:
            messages.error(request, f"Error occurred: {str(e)}")
        
        return redirect('staff_add_lab_result')

    return render(request, 'staff_template/staff_add_lab_result.html', context)

from django.views.decorators.http import require_POST

@require_POST
def delete_leave_application(request, leave_id):
    try:
        professor = get_object_or_404(Professor, user=request.user)
        leave = get_object_or_404(LeaveReportStaff, id=leave_id, professor=professor)
        
        if leave.status != 0:
            messages.error(request, "You can only delete pending leave applications.")
        else:
            leave_info = f"{leave.from_date} to {leave.to_date}"
            leave.delete()
            messages.success(request, f"Leave application for {leave_info} has been deleted successfully.")
        
    except Exception as e:
        messages.error(request, f"Error deleting leave application: {str(e)}")
    
    return redirect(reverse('staff_apply_leave'))

@require_POST
def delete_all_leave_history(request):
    try:
        professor = get_object_or_404(Professor, user=request.user)
        deleted_count = LeaveReportStaff.objects.filter(professor=professor).count()
        
        if deleted_count > 0:
            LeaveReportStaff.objects.filter(professor=professor).delete()
            messages.success(request, f"All {deleted_count} leave applications have been deleted successfully.")
        else:
            messages.info(request, "No leave applications to delete.")
            
    except Exception as e:
        messages.error(request, f"Error deleting leave history: {str(e)}")
    
    return redirect(reverse('staff_apply_leave'))

@require_POST
def delete_staff_feedback(request, feedback_id):
    try:
        professor = get_object_or_404(Professor, user=request.user)
        feedback = get_object_or_404(FeedbackStaff, id=feedback_id, professor=professor)
        
        if feedback.reply and feedback.reply.strip():
            messages.error(request, "Cannot delete feedback that has already been replied to.")
        else:
            feedback.delete()
            messages.success(request, "Feedback has been deleted successfully.")
        
    except Exception as e:
        messages.error(request, f"Error deleting feedback: {str(e)}")
    
    return redirect(reverse('staff_feedback'))

@csrf_exempt
@require_POST
def mark_notification_read(request, notification_id):
    try:
        professor = get_object_or_404(Professor, user=request.user)
        notification = get_object_or_404(NotificationStaff, id=notification_id, professor=professor)
        notification.is_read = True
        notification.save()
        return JsonResponse({
            'success': True, 
            'message': 'Notification marked as read successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e),
            'message': 'Failed to mark notification as read'
        }, status=400)

@csrf_exempt
@require_POST
def mark_all_notifications_read(request):
    try:
        professor = get_object_or_404(Professor, user=request.user)
        updated_count = NotificationStaff.objects.filter(professor=professor, is_read=False).update(is_read=True)
        return JsonResponse({
            'success': True, 
            'message': f'{updated_count} notifications marked as read',
            'updated_count': updated_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': str(e),
            'message': 'Failed to mark all notifications as read'
        }, status=400)

@csrf_exempt
def update_attendance(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        student_data = request.POST.get('student_ids')
        date_str = request.POST.get('date')
        subject_id = request.POST.get('subject')
        
        if not all([student_data, date_str, subject_id]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required fields',
                'received': {
                    'date': date_str,
                    'subject': subject_id,
                    'student_data_present': bool(student_data)
                }
            }, status=400)
        
        try:
            students = json.loads(student_data)
            if not isinstance(students, list) or len(students) == 0:
                raise ValueError("Student data must be a non-empty list")
        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid student data format: {str(e)}'
            }, status=400)
        
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid date format: {str(e)}'
            }, status=400)
        
        try:
            subject = Subject.objects.get(pk=subject_id)
            professor = Professor.objects.get(user=request.user)
        except Subject.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': f'Subject with ID {subject_id} not found'
            }, status=400)
        except Professor.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Professor profile not found for current user'
            }, status=400)
        
        updated_count = 0
        changes_made = []
        errors = []
        
        for student_dict in students:
            try:
                student_id = student_dict.get('id')
                new_status = bool(student_dict.get('status'))
                
                if not student_id:
                    errors.append("Missing student ID in data")
                    continue
                
                try:
                    student = Student.objects.get(pk=student_id)
                    attendance = Attendance.objects.get(
                        student=student,
                        date=attendance_date,
                        subject=subject
                    )
                except Student.DoesNotExist:
                    errors.append(f"Student with ID {student_id} not found")
                    continue
                except Attendance.DoesNotExist:
                    errors.append(f"No attendance record found for student {student_id} on {attendance_date}")
                    continue
                
                if attendance.status != new_status:
                    old_status = "Present" if attendance.status else "Absent"
                    new_status_text = "Present" if new_status else "Absent"
                    
                    attendance.status = new_status
                    attendance.marked_by = professor
                    attendance.save()
                    
                    updated_count += 1
                    changes_made.append({
                        'student': f"{student.roll_no} - {student.user.first_name} {student.user.last_name}",
                        'from': old_status,
                        'to': new_status_text
                    })
                
            except Exception as e:
                errors.append(f"Error updating student {student_dict.get('id', 'unknown')}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'message': f'Attendance updated successfully! {updated_count} changes made.' + 
                      (f' ({len(errors)} errors occurred)' if errors else ''),
            'updated_count': updated_count,
            'changes': changes_made,
            'errors': errors,
            'date': attendance_date.strftime('%B %d, %Y')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unexpected server error: {str(e)}'
        }, status=500)

@csrf_exempt
def get_todays_attendance_count(request):
    try:
        professor = get_object_or_404(Professor, user=request.user)
        today = timezone.now().date()
        
        count = Attendance.objects.filter(
            subject__taught_by=professor,
            date=today
        ).values('subject').distinct().count()
        
        return JsonResponse({'count': count})
    except Exception as e:
        return JsonResponse({'count': 0, 'error': str(e)})

def staff_edit_result(request):
    try:
            professor = get_object_or_404(Professor, user=request.user)
    except Professor.DoesNotExist:
        messages.error(request, "Professor profile not found. Please contact admin.")
        return redirect('staff_home')
        
    form = EditResultForm()
    form.fields['subject'].queryset = Subject.objects.filter(taught_by=professor)
    context = {
        'form': form,
        'page_title': 'Update Student Results',
        'subjects': Subject.objects.filter(taught_by=professor),
        'batches': Batch.objects.all()
    }

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        batch_year_id = request.POST.get('batch_year')
        
        if subject_id and batch_year_id:
            try:
                subject = Subject.objects.get(subject_id=subject_id)
                batch = Batch.objects.get(batch_id=batch_year_id)
                student_queryset = Student.objects.filter(
                    semester=subject.semester,
                    batch=batch
                ).select_related('user').order_by('roll_no')
                
            except (Subject.DoesNotExist, Batch.DoesNotExist):
                messages.error(request, "Invalid subject or batch selected")
                return render(request, 'staff_template/staff_edit_result.html', context)
        else:
            messages.error(request, "Please select both subject and batch")
            return render(request, 'staff_template/staff_edit_result.html', context)
        
        form = EditResultForm(request.POST, student_queryset=student_queryset)
        form.fields['subject'].queryset = Subject.objects.filter(taught_by=professor)
        
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    student = form.cleaned_data['student']
                    subject = form.cleaned_data['subject']
                    
                    saved_something = False
                    
                    # Theory fields processing
                    theory_fields = ['ca1', 'ca2', 'ca3', 'end_sem']
                    theory_data = {}
                    
                    for field in theory_fields:
                        value = form.cleaned_data.get(field)
                        if value is not None:
                            theory_data[field] = float(value)
                    
                    if theory_data:
                        theory_marks, created = TheoryMarks.objects.get_or_create(
                            student=student, 
                            subject=subject,
                            defaults=theory_data
                        )
                        if not created:
                            for field, value in theory_data.items():
                                setattr(theory_marks, field, value)
                            theory_marks.save()
                        
                        saved_something = True
                    
                    # Lab fields processing
                    lab_fields = ['pca1', 'pca2', 'end_sem_practical']
                    lab_data = {}
                    
                    for field in lab_fields:
                        value = form.cleaned_data.get(field)
                        if value is not None:
                            lab_data[field] = float(value)
                    
                    if lab_data:
                        lab_marks, created = LabMarks.objects.get_or_create(
                            student=student, 
                            subject=subject,
                            defaults=lab_data
                        )
                        if not created:
                            for field, value in lab_data.items():
                                setattr(lab_marks, field, value)
                            lab_marks.save()
                        
                        saved_something = True
                    
                    if saved_something:
                        messages.success(request, f"Results updated successfully for {student.roll_no} - {student.user.first_name} {student.user.last_name}")
                        return redirect('staff_edit_result')
                    else:
                        messages.warning(request, "No marks were provided to save")
                        
            except Exception as e:
                messages.error(request, f"Error occurred: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f"Form Error: {error}")
                    else:
                        field_label = form.fields[field].label or field.replace('_', ' ').title()
                        messages.error(request, f"{field_label}: {error}")
            
            for error in form.non_field_errors():
                messages.error(request, f"Validation Error: {error}")

        context['form'] = form

    return render(request, 'staff_template/edit_student_result.html', context)