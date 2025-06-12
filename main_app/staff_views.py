import json

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404, redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *

# Displays the professor's dashboard with stats on students, subjects, leaves, and subject-wise attendance.
def staff_home(request):  # ✅ FIXED: Function name
    professor = get_object_or_404(Professor, user=request.user)  # ✅ FIXED: user=request.user
    total_students = Student.objects.filter(department=professor.department).count()  # ✅ FIXED: department instead of course
    total_leave = LeaveReportStaff.objects.filter(professor=professor).count()  # ✅ FIXED: Model name
    subjects = Subject.objects.filter(taught_by=professor)
    total_subject = subjects.count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.subject_name)  # ✅ FIXED: subject_name instead of name
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Staff Panel - ' + str(professor.user.last_name) + ' (' + str(professor.department) + ')',  # ✅ FIXED: department instead of course
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, 'staff_template/home_content.html', context)  # ✅ FIXED: Template path


def staff_take_attendance(request):  # ✅ FIXED: Function name
    professor = get_object_or_404(Professor, user=request.user)  # ✅ FIXED: user=request.user
    subjects = Subject.objects.filter(taught_by=professor)  # ✅ FIXED: taught_by=professor
    batches = Batch.objects.all()  # ✅ FIXED: Variable name
    context = {
        'subjects': subjects,
        'batches': batches,  # ✅ FIXED: Variable name
        'page_title': 'Take Attendance'
    }
    return render(request, 'staff_template/staff_take_attendance.html', context)  # ✅ FIXED: Template path


@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    batch_id = request.POST.get('batch')  # ✅ FIXED: Variable name
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        batch = get_object_or_404(Batch, id=batch_id)
        students = Student.objects.filter(
            department_id=subject.semester.year.department.id, batch=batch)  # ✅ FIXED: department and batch
        student_data = []
        for student in students:
            data = {
                "id": student.id,
                "name": student.user.last_name + " " + student.user.first_name  # ✅ FIXED: user instead of admin
            }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    batch_id = request.POST.get('batch')  # ✅ FIXED: Variable name
    students = json.loads(student_data)
    try:
        batch = get_object_or_404(Batch, id=batch_id)
        subject = get_object_or_404(Subject, id=subject_id)
        professor = get_object_or_404(Professor, user=request.user)

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            
            # Create or update attendance record
            attendance, created = Attendance.objects.get_or_create(
                student=student,
                subject=subject,
                date=date,
                defaults={'status': student_dict.get('status'), 'marked_by': professor}
            )
            if not created:
                attendance.status = student_dict.get('status')
                attendance.save()

    except Exception as e:
        return HttpResponse("Error: " + str(e))

    return HttpResponse("OK")


def staff_update_attendance(request):  # ✅ FIXED: Function name
    professor = get_object_or_404(Professor, user=request.user)  # ✅ FIXED: user=request.user
    subjects = Subject.objects.filter(taught_by=professor)  # ✅ FIXED: taught_by=professor
    batches = Batch.objects.all()  # ✅ FIXED: Variable name
    context = {
        'subjects': subjects,
        'batches': batches,  # ✅ FIXED: Variable name
        'page_title': 'Update Attendance'
    }
    return render(request, 'staff_template/staff_update_attendance.html', context)  # ✅ FIXED: Template path


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = Attendance.objects.filter(date=date.date, subject=date.subject)  # ✅ FIXED: Updated query
        student_data = []
        for attendance in attendance_data:
            data = {
                "id": attendance.student.user.id,  # ✅ FIXED: user instead of admin
                "name": attendance.student.user.last_name + " " + attendance.student.user.first_name,  # ✅ FIXED: user instead of admin
                "status": attendance.status
            }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        for student_dict in students:
            student = get_object_or_404(Student, user_id=student_dict.get('id'))
            attendance = get_object_or_404(Attendance, student=student, date=date)
            attendance.status = student_dict.get('status')
            attendance.save()
    except Exception as e:
        return HttpResponse("Error: " + str(e))

    return HttpResponse("OK")


def staff_apply_leave(request):  # ✅ FIXED: Function name
    form = LeaveReportStaffForm(request.POST or None)
    professor = get_object_or_404(Professor, user_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(professor=professor),  # ✅ FIXED: professor=professor
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.professor = professor  # ✅ FIXED: professor instead of Professor
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)  # ✅ FIXED: Template path


def staff_feedback(request):  # ✅ FIXED: Function name
    form = FeedbackStaffForm(request.POST or None)
    professor = get_object_or_404(Professor, user_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(professor=professor),  # ✅ FIXED: professor=professor
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.professor = professor  # ✅ FIXED: professor instead of Professor
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)  # ✅ FIXED: Template path


def staff_view_profile(request):  # ✅ FIXED: Function name
    professor = get_object_or_404(Professor, user=request.user)  # ✅ FIXED: user=request.user
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
                user = professor.user  # ✅ FIXED: user instead of admin
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

    return render(request, "staff_template/staff_view_profile.html", context)  # ✅ FIXED: Template path


@csrf_exempt
def staff_fcmtoken(request):  # ✅ FIXED: Function name
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):  # ✅ FIXED: Function name
    professor = get_object_or_404(Professor, user=request.user)  # ✅ FIXED: user=request.user
    notifications = NotificationStaff.objects.filter(professor=professor)  # ✅ FIXED: professor=professor
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)  # ✅ FIXED: Template path


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Professor, Subject, Batch, Student, TheoryMarks

def staff_add_result(request):
    professor = get_object_or_404(Professor, user=request.user)
    subjects = Subject.objects.filter(taught_by=professor)
    batches = Batch.objects.all()
    
    context = {
        'page_title': 'Result Upload',
        'subjects': subjects,
        'batches': batches
    }

    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            ca1 = request.POST.get('ca1', 0)
            ca2 = request.POST.get('ca2', 0)
            ca3 = request.POST.get('ca3', 0)
            end_sem = request.POST.get('end_sem', 0)

            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)

            try:
                data = TheoryMarks.objects.get(student=student, subject=subject)
                data.ca1 = ca1
                data.ca2 = ca2
                data.ca3 = ca3
                data.end_sem = end_sem
                data.save()
                messages.success(request, "Scores Updated")
            except TheoryMarks.DoesNotExist:
                result = TheoryMarks(
                    student=student,
                    subject=subject,
                    ca1=ca1,
                    ca2=ca2,
                    ca3=ca3,
                    end_sem=end_sem
                )
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, f"Something went wrong: {e}")
        
        return redirect('staff_add_result')  # ✅ Return something after POST

    return render(request, 'staff_template/staff_add_result.html', context)  # ✅ Return on GET


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = TheoryMarks.objects.get(student=student, subject=subject)
        result_data = {
            'ca1': result.ca1,
            'ca2': result.ca2,
            'ca3': result.ca3,
            'end_sem': result.end_sem
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')
