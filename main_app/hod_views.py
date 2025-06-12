import json
import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView

from .forms import *
from .models import *

# Displays the admin dashboard with a complete overview of students, professors, subjects, departments, and attendance statistics.
def admin_home(request):
    total_staff = Professor.objects.all().count()  # ✅ FIXED: Staff -> Professor
    total_students = Student.objects.all().count()
    subjects = Subject.objects.all()
    total_subject = subjects.count()
    total_course = Department.objects.all().count()  # ✅ FIXED: Course -> Department
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.subject_name[:7])  # ✅ FIXED: name -> subject_name
        attendance_list.append(attendance_count)
    context = {
        'page_title': "Administrative Dashboard",
        'total_students': total_students,
        'total_staff': total_staff,
        'total_course': total_course,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, 'hod_template/home_content.html', context)


def add_staff(request):
    form = ProfessorForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Staff'}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            department = form.cleaned_data.get('department')
            passport = request.FILES.get('profile_pic')
            
            try:
                # Create the CustomUser first
                user = CustomUser.objects.create_user(
                    email=email, 
                    password=password, 
                    user_type=2, 
                    first_name=first_name, 
                    last_name=last_name
                )
                user.gender = gender
                user.address = address
                
                # Handle profile picture
                if passport:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                
                user.save()
                
                # ✅ NOW manually create the Professor with department
                Professor.objects.create(user=user, department=department)
                
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_staff'))

            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Please fulfil all requirements")

    return render(request, 'hod_template/add_staff_template.html', context)



def add_student(request):
    student_form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': student_form, 'page_title': 'Add Student'}
    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name = student_form.cleaned_data.get('last_name')
            address = student_form.cleaned_data.get('address')
            email = student_form.cleaned_data.get('email')
            gender = student_form.cleaned_data.get('gender')
            password = student_form.cleaned_data.get('password')
            department = student_form.cleaned_data.get('department')  # ✅ FIXED: course -> department
            batch = student_form.cleaned_data.get('batch')  # ✅ FIXED: Batch -> batch
            roll_no = student_form.cleaned_data.get('roll_no')  # ✅ ADDED: roll_no field
            year = student_form.cleaned_data.get('year')  # ✅ ADDED: year field
            semester = student_form.cleaned_data.get('semester')  # ✅ ADDED: semester field
            passport = request.FILES['profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, first_name=first_name, last_name=last_name, profile_pic=passport_url)
                user.gender = gender
                user.address = address
                user.student.batch = batch  # ✅ FIXED: Batch -> batch
                user.student.department = department  # ✅ FIXED: course -> department
                user.student.roll_no = roll_no  # ✅ ADDED
                user.student.year = year  # ✅ ADDED
                user.student.semester = semester  # ✅ ADDED
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
        else:
            messages.error(request, "Could Not Add: ")
    return render(request, 'hod_template/add_student_template.html', context)


def add_course(request):
    form = DepartmentForm(request.POST or None)  # ✅ FIXED: CourseForm -> DepartmentForm
    context = {
        'form': form,
        'page_title': 'Add Department'  # ✅ FIXED: Course -> Department
    }
    if request.method == 'POST':
        if form.is_valid():
            dept_name = form.cleaned_data.get('dept_name')  # ✅ FIXED: name -> dept_name
            try:
                department = Department()  # ✅ FIXED: Course -> Department
                department.dept_name = dept_name  # ✅ FIXED: name -> dept_name
                department.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_course'))
            except:
                messages.error(request, "Could Not Add")
        else:
            messages.error(request, "Could Not Add")
    return render(request, 'hod_template/add_course_template.html', context)


def add_subject(request):
    form = SubjectForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            subject_name = form.cleaned_data.get('subject_name')  # ✅ FIXED: name -> subject_name
            semester = form.cleaned_data.get('semester')  # ✅ FIXED: course -> semester
            taught_by = form.cleaned_data.get('taught_by')  # ✅ FIXED: staff -> taught_by
            subject_code = form.cleaned_data.get('subject_code')  # ✅ ADDED
            subject_type = form.cleaned_data.get('subject_type')  # ✅ ADDED
            try:
                subject = Subject()
                subject.subject_name = subject_name  # ✅ FIXED
                subject.subject_code = subject_code  # ✅ ADDED
                subject.subject_type = subject_type  # ✅ ADDED
                subject.semester = semester  # ✅ FIXED
                subject.save()
                subject.taught_by.set(taught_by)  # ✅ FIXED: ManyToMany field
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_subject'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")

    return render(request, 'hod_template/add_subject_template.html', context)



def manage_staff(request):
    allStaff = CustomUser.objects.filter(user_type=2).select_related('professor__department') 
    context = {
        'allStaff': allStaff,
        'page_title': 'Manage Staff'
    }
    return render(request, "hod_template/manage_staff.html", context)



def manage_student(request):
    students = CustomUser.objects.filter(user_type=3)
    context = {
        'students': students,
        'page_title': 'Manage Students'
    }
    return render(request, "hod_template/manage_student.html", context)


def manage_course(request):
    departments  = Department.objects.all()  # ✅ FIXED: Course -> Department
    context = {
        'courses': departments,
        'page_title': 'Manage Departments'  # ✅ FIXED
    }
    return render(request, "hod_template/manage_course.html", context)


def manage_subject(request):
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects,
        'page_title': 'Manage Subjects'
    }
    return render(request, "hod_template/manage_subject.html", context)


def edit_staff(request, staff_id):
    professor = get_object_or_404(Professor, id=staff_id)  # ✅ FIXED: Staff -> Professor
    form = ProfessorForm(request.POST or None, instance=professor)  # ✅ FIXED: StaffForm -> ProfessorForm
    context = {
        'form': form,
        'staff_id': staff_id,
        'page_title': 'Edit Staff'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            department = form.cleaned_data.get('department')  # ✅ FIXED: course -> department
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=professor.user.id)  # ✅ FIXED: admin -> user
                user.email = email
                if password != None:
                    user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.first_name = first_name
                user.last_name = last_name
                user.gender = gender
                user.address = address
                professor.department = department  # ✅ FIXED: course -> department
                user.save()
                professor.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_staff', args=[staff_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please fill form properly")
    else:
        return render(request, "hod_template/edit_staff_template.html", context)


def edit_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    context = {
        'form': form,
        'student_id': student_id,
        'page_title': 'Edit Student'
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            department = form.cleaned_data.get('department')  # ✅ FIXED: course -> department
            batch = form.cleaned_data.get('batch')  # ✅ FIXED: Batch -> batch
            passport = request.FILES.get('profile_pic') or None
            try:
                user = CustomUser.objects.get(id=student.user.id)  # ✅ FIXED: admin -> user
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    user.profile_pic = passport_url
                user.email = email
                if password != None:
                    user.set_password(password)
                user.first_name = first_name
                user.last_name = last_name
                student.batch = batch  # ✅ FIXED: Batch -> batch
                user.gender = gender
                user.address = address
                student.department = department  # ✅ FIXED: course -> department
                user.save()
                student.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly!")
    else:
        return render(request, "hod_template/edit_student_template.html", context)


def edit_course(request, course_id):
    instance = get_object_or_404(Department, id=course_id)  # ✅ FIXED: Course -> Department
    form = DepartmentForm(request.POST or None, instance=instance)  # ✅ FIXED: CourseForm -> DepartmentForm
    context = {
        'form': form,
        'course_id': course_id,
        'page_title': 'Edit Department'  # ✅ FIXED
    }
    if request.method == 'POST':
        if form.is_valid():
            dept_name = form.cleaned_data.get('dept_name')  # ✅ FIXED: name -> dept_name
            try:
                department = Department.objects.get(id=course_id)  # ✅ FIXED: Course -> Department
                department.dept_name = dept_name  # ✅ FIXED: name -> dept_name
                department.save()
                messages.success(request, "Successfully Updated")
            except:
                messages.error(request, "Could Not Update")
        else:
            messages.error(request, "Could Not Update")

    return render(request, 'hod_template/edit_course_template.html', context)


def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'subject_id': subject_id,
        'page_title': 'Edit Subject'
    }
    if request.method == 'POST':
        if form.is_valid():
            subject_name = form.cleaned_data.get('subject_name')  # ✅ FIXED: name -> subject_name
            semester = form.cleaned_data.get('semester')  # ✅ FIXED: course -> semester
            taught_by = form.cleaned_data.get('taught_by')  # ✅ FIXED: staff -> taught_by
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.subject_name = subject_name  # ✅ FIXED
                subject.semester = semester  # ✅ FIXED
                subject.taught_by.set(taught_by)  # ✅ FIXED: ManyToMany
                subject.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'hod_template/edit_subject_template.html', context)


def add_Batch(request):
    form = BatchForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Batch'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Batch Created")
                return redirect(reverse('add_Batch'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
        else:
            messages.error(request, 'Fill Form Properly ')
    return render(request, "hod_template/add_Batch_template.html", context)


def manage_Batch(request):
    Batchs = Batch.objects.all() 
    context = {'Batchs': Batchs, 'page_title': 'Manage Batches'}
    return render(request, "hod_template/manage_Batch.html", context)


def edit_Batch(request, Batch_id):
    instance = get_object_or_404(Batch, id=Batch_id)
    form = BatchForm(request.POST or None, instance=instance)
    context = {'form': form, 'Batch_id': Batch_id,
               'page_title': 'Edit Batch'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Batch Updated")
                return redirect(reverse('edit_Batch', args=[Batch_id]))
            except Exception as e:
                messages.error(
                    request, "Batch Could Not Be Updated " + str(e))
                return render(request, "hod_template/edit_Batch_template.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "hod_template/edit_Batch_template.html", context)

    else:
        return render(request, "hod_template/edit_Batch_template.html", context)


@csrf_exempt
def check_email_availability(request):
    email = request.POST.get("email")
    try:
        user = CustomUser.objects.filter(email=email).exists()
        if user:
            return HttpResponse(True)
        return HttpResponse(False)
    except Exception as e:
        return HttpResponse(False)


@csrf_exempt
def student_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStudent.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Student Feedback Messages'
        }
        return render(request, 'hod_template/student_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStudent, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
def staff_feedback_message(request):
    if request.method != 'POST':
        feedbacks = FeedbackStaff.objects.all()
        context = {
            'feedbacks': feedbacks,
            'page_title': 'Staff Feedback Messages'
        }
        return render(request, 'hod_template/staff_feedback_template.html', context)
    else:
        feedback_id = request.POST.get('id')
        try:
            feedback = get_object_or_404(FeedbackStaff, id=feedback_id)
            reply = request.POST.get('reply')
            feedback.reply = reply
            feedback.save()
            return HttpResponse(True)
        except Exception as e:
            return HttpResponse(False)


@csrf_exempt
def view_staff_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStaff.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Staff'
        }
        return render(request, "hod_template/staff_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStaff, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


@csrf_exempt
def view_student_leave(request):
    if request.method != 'POST':
        allLeave = LeaveReportStudent.objects.all()
        context = {
            'allLeave': allLeave,
            'page_title': 'Leave Applications From Students'
        }
        return render(request, "hod_template/student_leave_view.html", context)
    else:
        id = request.POST.get('id')
        status = request.POST.get('status')
        if (status == '1'):
            status = 1
        else:
            status = -1
        try:
            leave = get_object_or_404(LeaveReportStudent, id=id)
            leave.status = status
            leave.save()
            return HttpResponse(True)
        except Exception as e:
            return False


def admin_view_attendance(request):
    subjects = Subject.objects.all()
    batches = Batch.objects.all()  # ✅ FIXED: Batchs -> batches
    context = {
        'subjects': subjects,
        'batches': batches,  # ✅ FIXED
        'page_title': 'View Attendance'
    }

    return render(request, "hod_template/admin_view_attendance.html", context)


@csrf_exempt
def get_admin_attendance(request):
    subject_id = request.POST.get('subject')
    batch_id = request.POST.get('batch')  # ✅ FIXED: Batch -> batch
    attendance_date = request.POST.get('attendance_date')  # ✅ SIMPLIFIED
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        batch = get_object_or_404(Batch, id=batch_id)  # ✅ FIXED
        # Simplified attendance logic - you may need to adjust based on your attendance structure
        attendance_records = Attendance.objects.filter(
            subject=subject, date=attendance_date)
        json_data = []
        for record in attendance_records:
            data = {
                "status": str(record.status),
                "name": str(record.student)
            }
            json_data.append(data)
        return JsonResponse(json.dumps(json_data), safe=False)
    except Exception as e:
        return None


def admin_view_profile(request):
    admin = get_object_or_404(Admin, user=request.user)  # ✅ FIXED: admin -> user
    form = AdminForm(request.POST or None, request.FILES or None,
                     instance=admin)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                passport = request.FILES.get('profile_pic') or None
                custom_user = admin.user  # ✅ FIXED: admin -> user
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('admin_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occurred While Updating Profile " + str(e))
    return render(request, "hod_template/admin_view_profile.html", context)


def admin_notify_staff(request):
    staff = CustomUser.objects.filter(user_type=2)
    context = {
        'page_title': "Send Notifications To Staff",
        'allStaff': staff
    }
    return render(request, "hod_template/staff_notification.html", context)


def admin_notify_student(request):
    student = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': "Send Notifications To Students",
        'students': student
    }
    return render(request, "hod_template/student_notification.html", context)


@csrf_exempt
def send_student_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    student = get_object_or_404(Student, user_id=id)  # ✅ FIXED: user_id -> user_id
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('student_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': student.user.fcm_token  # ✅ FIXED: admin -> user
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStudent(student=student, message=message)
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@csrf_exempt
def send_staff_notification(request):
    id = request.POST.get('id')
    message = request.POST.get('message')
    professor = get_object_or_404(Professor, user_id=id)  # ✅ FIXED: Staff -> Professor, user_id -> user_id
    try:
        url = "https://fcm.googleapis.com/fcm/send"
        body = {
            'notification': {
                'title': "Student Management System",
                'body': message,
                'click_action': reverse('staff_view_notification'),
                'icon': static('dist/img/AdminLTELogo.png')
            },
            'to': professor.user.fcm_token  # ✅ FIXED: admin -> user
        }
        headers = {'Authorization':
                   'key=AAAA3Bm8j_M:APA91bElZlOLetwV696SoEtgzpJr2qbxBfxVBfDWFiopBWzfCfzQp2nRyC7_A2mlukZEHV4g1AmyC6P_HonvSkY2YyliKt5tT3fe_1lrKod2Daigzhb2xnYQMxUWjCAIQcUexAMPZePB',
                   'Content-Type': 'application/json'}
        data = requests.post(url, data=json.dumps(body), headers=headers)
        notification = NotificationStaff(professor=professor, message=message)  # ✅ FIXED: staff -> professor
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def delete_staff(request, staff_id):
    professor = get_object_or_404(CustomUser, professor__id=staff_id)  # ✅ FIXED: staff -> professor
    professor.delete()
    messages.success(request, "Staff deleted successfully!")
    return redirect(reverse('manage_staff'))


def delete_student(request, student_id):
    student = get_object_or_404(CustomUser, student__id=student_id)
    student.delete()
    messages.success(request, "Student deleted successfully!")
    return redirect(reverse('manage_student'))


def delete_course(request, course_id):
    department = get_object_or_404(Department, id=course_id)  # ✅ FIXED: Course -> Department
    try:
        department.delete()
        messages.success(request, "Department deleted successfully!")  # ✅ FIXED
    except Exception:
        messages.error(
            request, "Sorry, some students are assigned to this department already. Kindly change the affected student department and try again")  # ✅ FIXED
    return redirect(reverse('manage_course'))


def delete_subject(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    subject.delete()
    messages.success(request, "Subject deleted successfully!")
    return redirect(reverse('manage_subject'))


def delete_Batch(request, Batch_id):
    batch = get_object_or_404(Batch, id=Batch_id)
    try:
        batch.delete()
        messages.success(request, "Batch deleted successfully!")
    except Exception:
        messages.error(
            request, "There are students assigned to this batch. Please move them to another batch.")
    return redirect(reverse('manage_Batch'))


def add_year(request):
    form = YearForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Academic Year'
    }
    if request.method == 'POST':
        if form.is_valid():
            year_no = form.cleaned_data.get('year_no')
            department = form.cleaned_data.get('department')
            try:
                year = Year()
                year.year_no = year_no
                year.department = department
                year.save()
                messages.success(request, "Academic Year Added Successfully")
                return redirect(reverse('add_year'))
            except Exception as e:
                messages.error(request, "Could Not Add Academic Year: " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly")
    return render(request, 'hod_template/add_year_template.html', context)

def manage_year(request):
    years = Year.objects.all().order_by('department', 'year_no')
    context = {
        'years': years,
        'page_title': 'Manage Academic Years'
    }
    return render(request, "hod_template/manage_year.html", context)

def edit_year(request, year_id):
    instance = get_object_or_404(Year, id=year_id)
    form = YearForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'year_id': year_id,
        'page_title': 'Edit Academic Year'
    }
    if request.method == 'POST':
        if form.is_valid():
            year_no = form.cleaned_data.get('year_no')
            department = form.cleaned_data.get('department')
            try:
                year = Year.objects.get(id=year_id)
                year.year_no = year_no
                year.department = department
                year.save()
                messages.success(request, "Academic Year Updated Successfully")
                return redirect(reverse('edit_year', args=[year_id]))
            except Exception as e:
                messages.error(request, "Could Not Update Academic Year: " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly")
    return render(request, 'hod_template/edit_year_template.html', context)

def delete_year(request, year_id):
    year = get_object_or_404(Year, id=year_id)
    try:
        year.delete()
        messages.success(request, "Academic Year deleted successfully!")
    except Exception as e:
        messages.error(request, "Could not delete Academic Year. It may be in use by semesters or students.")
    return redirect(reverse('manage_year'))


def add_semester(request):
    form = SemesterForm(request.POST or None)
    context = {
        'form': form,
        'page_title': 'Add Semester'
    }
    if request.method == 'POST':
        if form.is_valid():
            sem_no = form.cleaned_data.get('sem_no')
            year = form.cleaned_data.get('year')
            try:
                semester = Semester()
                semester.sem_no = sem_no
                semester.year = year
                semester.save()
                messages.success(request, "Semester Added Successfully")
                return redirect(reverse('add_semester'))
            except Exception as e:
                messages.error(request, "Could Not Add Semester: " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly")
    return render(request, 'hod_template/add_semester_template.html', context)

def manage_semester(request):
    semesters = Semester.objects.all().order_by('year__department', 'year__year_no', 'sem_no')
    context = {
        'semesters': semesters,
        'page_title': 'Manage Semesters'
    }
    return render(request, "hod_template/manage_semester.html", context)

def edit_semester(request, semester_id):
    instance = get_object_or_404(Semester, id=semester_id)
    form = SemesterForm(request.POST or None, instance=instance)
    context = {
        'form': form,
        'semester_id': semester_id,
        'page_title': 'Edit Semester'
    }
    if request.method == 'POST':
        if form.is_valid():
            sem_no = form.cleaned_data.get('sem_no')
            year = form.cleaned_data.get('year')
            try:
                semester = Semester.objects.get(id=semester_id)
                semester.sem_no = sem_no
                semester.year = year
                semester.save()
                messages.success(request, "Semester Updated Successfully")
                return redirect(reverse('edit_semester', args=[semester_id]))
            except Exception as e:
                messages.error(request, "Could Not Update Semester: " + str(e))
        else:
            messages.error(request, "Please Fill Form Properly")
    return render(request, 'hod_template/edit_semester_template.html', context)

def delete_semester(request, semester_id):
    semester = get_object_or_404(Semester, id=semester_id)
    try:
        semester.delete()
        messages.success(request, "Semester deleted successfully!")
    except Exception as e:
        messages.error(request, "Could not delete Semester. It may be in use by subjects or students.")
    return redirect(reverse('manage_semester'))

def fix_staff_profile(request, user_id):
    """Create missing Professor profile for staff user"""
    try:
        user = get_object_or_404(CustomUser, id=user_id, user_type=2)
        
        # Check if Professor already exists
        if hasattr(user, 'professor'):
            messages.info(request, "Professor profile already exists")
            return redirect(reverse('manage_staff'))
        
        # Create Professor profile
        professor = Professor.objects.create(user=user)
        messages.success(request, f"Professor profile created for {user.first_name} {user.last_name}")
        
    except Exception as e:
        messages.error(request, f"Could not fix profile: {str(e)}")
    
    return redirect(reverse('manage_staff'))

def delete_staff_user(request, user_id):
    """Delete CustomUser directly (for users without Professor profiles)"""
    try:
        user = get_object_or_404(CustomUser, id=user_id, user_type=2)
        user_name = f"{user.first_name} {user.last_name}"
        user.delete()
        messages.success(request, f"User {user_name} deleted successfully!")
    except Exception as e:
        messages.error(request, f"Could not delete user: {str(e)}")
    
    return redirect(reverse('manage_staff'))
