import json
import math
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *

# Displays the student's dashboard with overall and subject-wise attendance statistics.
def student_home(request):
    student = get_object_or_404(Student, user=request.user)  # ✅ FIXED: admin -> user
    total_subject = Subject.objects.filter(semester=student.semester).count()  # ✅ FIXED: course -> semester
    total_attendance = Attendance.objects.filter(student=student).count()  # ✅ FIXED: AttendanceReport -> Attendance
    total_present = Attendance.objects.filter(student=student, status=True).count()  # ✅ FIXED
    
    if total_attendance == 0:  # Don't divide. DivisionByZero
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present/total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)
    
    subject_name = []
    data_present = []
    data_absent = []
    subjects = Subject.objects.filter(semester=student.semester)  # ✅ FIXED: course -> semester
    
    for subject in subjects:
        present_count = Attendance.objects.filter(
            subject=subject, status=True, student=student).count()  # ✅ FIXED: Simplified
        absent_count = Attendance.objects.filter(
            subject=subject, status=False, student=student).count()  # ✅ FIXED: Simplified
        subject_name.append(subject.subject_name)  # ✅ FIXED: name -> subject_name
        data_present.append(present_count)
        data_absent.append(absent_count)
    
    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'page_title': 'Student Homepage'
    }
    return render(request, 'student_template/home_content.html', context)


@csrf_exempt
def student_view_attendance(request):
    student = get_object_or_404(Student, user=request.user)
    
    if request.method != 'POST':
        # GET request - show the form
        context = {
            'subjects': Subject.objects.filter(semester=student.semester),
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    
    else:
        # POST request - process the form
        subject_id = request.POST.get('subject')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Enhanced debugging
        print(f"DEBUG: Received POST data: subject={subject_id}, start={start_date}, end={end_date}")
        print(f"DEBUG: All POST data: {dict(request.POST)}")
        
        # Enhanced validation
        if not subject_id:
            return JsonResponse({'error': 'Subject is required'}, status=400)
        
        if not start_date:
            return JsonResponse({'error': 'Start date is required'}, status=400)
            
        if not end_date:
            return JsonResponse({'error': 'End date is required'}, status=400)
        
        try:
            # Validate subject exists and belongs to student's semester
            subject = get_object_or_404(Subject, id=subject_id, semester=student.semester)
            
            # Parse dates
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Validate date range
            if start_date_obj > end_date_obj:
                return JsonResponse({'error': 'Start date cannot be later than end date'}, status=400)
            
            # Fetch attendance records
            attendance_records = Attendance.objects.filter(
                date__range=(start_date_obj, end_date_obj),
                subject=subject,
                student=student
            ).order_by('date')
            
            # Format response
            json_data = []
            for record in attendance_records:
                data = {
                    "date": str(record.date),
                    "status": record.status
                }
                json_data.append(data)
            
            print(f"DEBUG: Returning {len(json_data)} attendance records")
            return JsonResponse(json_data, safe=False)
            
        except Subject.DoesNotExist:
            return JsonResponse({'error': 'Invalid subject selected'}, status=400)
        except ValueError as e:
            return JsonResponse({'error': f'Invalid date format: {str(e)}'}, status=400)
        except Exception as e:
            print(f"ERROR in student_view_attendance: {str(e)}")
            return JsonResponse({'error': f'Server error: {str(e)}'}, status=500)


def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, user_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student).order_by('-created_at'),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                # ✅ CRITICAL FIX: Set to_date to same as from_date for single-day leave
                obj.to_date = obj.from_date
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception as e:
                messages.error(request, f"Could not submit: {str(e)}")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_apply_leave.html", context)



def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, user_id=request.user.id)  # ✅ FIXED: Keep user_id for now
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, user=request.user)  # ✅ FIXED: admin -> user
    form = StudentEditForm(request.POST or None, request.FILES or None,
                           instance=student)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                user = student.user  # ✅ FIXED: admin -> user
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
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occurred While Updating Profile " + str(e))

    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, user=request.user)  # ✅ FIXED: admin -> user
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


def student_view_result(request):
    student = get_object_or_404(Student, user=request.user)  # ✅ FIXED: admin -> user
    theory_results = TheoryMarks.objects.filter(student=student)  # ✅ FIXED: StudentResult -> TheoryMarks
    lab_results = LabMarks.objects.filter(student=student)  # ✅ ADDED: Lab results
    context = {
        'theory_results': theory_results,
        'lab_results': lab_results,
        'page_title': "View Results"
    }
    return render(request, "student_template/student_view_result.html", context)
