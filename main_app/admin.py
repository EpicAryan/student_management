# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import *
# # Register your models here.


# class UserModel(UserAdmin):
#     ordering = ('email',)


# admin.site.register(CustomUser, UserModel)
# admin.site.register(Staff)
# admin.site.register(Student)
# admin.site.register(Course)
# admin.site.register(Subject)
# admin.site.register(Session)
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Admin, Professor, Student, Department, 
    Batch, Year, Semester, Subject, Attendance, 
    TheoryMarks, LabMarks, LeaveReportStudent, 
    LeaveReportStaff, FeedbackStudent, FeedbackStaff,
    NotificationStudent, NotificationStaff
)

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'is_staff']
    list_filter = ['user_type', 'is_staff', 'is_superuser', 'gender']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'gender', 'address', 'profile_pic')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Additional Info', {'fields': ('user_type', 'fcm_token')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'first_name', 'last_name')}
        ),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

# Register CustomUser with custom admin
admin.site.register(CustomUser, CustomUserAdmin)

# Basic model registrations
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['dept_name', 'created_at']
    search_fields = ['dept_name']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['department', 'start_year', 'end_year']
    list_filter = ['department', 'start_year']

@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ['year_no', 'department']
    list_filter = ['department', 'year_no']
    search_fields = ['department__dept_name']

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['sem_no', 'year']
    list_filter = ['year__department', 'sem_no']
    search_fields = ['year__department__dept_name']
     
@admin.register(Admin)
class AdminModelAdmin(admin.ModelAdmin):
    list_display = ['user', 'department']  # ✅ FIXED: Changed from 'admin' to 'user'
    list_filter = ['department']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']  # ✅ FIXED: Updated search fields

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'managed_by']  # ✅ FIXED: Changed from 'admin' to 'user'
    list_filter = ['department']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']  # ✅ FIXED: Updated search fields

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['roll_no', 'user', 'department', 'year', 'semester']  # ✅ FIXED: Changed from 'admin' to 'user'
    list_filter = ['department', 'year', 'semester', 'batch']
    search_fields = ['roll_no', 'user__first_name', 'user__last_name', 'user__email']  # ✅ FIXED: Updated search fields

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['subject_code', 'subject_name', 'subject_type', 'semester']
    list_filter = ['subject_type', 'semester__year__department']
    search_fields = ['subject_name', 'subject_code']
    filter_horizontal = ['taught_by']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'date', 'status', 'marked_by']
    list_filter = ['status', 'date', 'subject__semester']
    search_fields = ['student__roll_no', 'student__user__first_name']  # ✅ FIXED: Updated search fields
    date_hierarchy = 'date'

@admin.register(TheoryMarks)
class TheoryMarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'ca1', 'ca2', 'ca3', 'end_sem', 'total_marks']
    list_filter = ['subject__semester']
    search_fields = ['student__roll_no', 'subject__subject_name']
    readonly_fields = ['total_marks']

@admin.register(LabMarks)
class LabMarksAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'pca1', 'pca2', 'end_sem_practical', 'total_marks']
    list_filter = ['subject__semester']
    search_fields = ['student__roll_no', 'subject__subject_name']
    readonly_fields = ['total_marks']

@admin.register(LeaveReportStudent)
class LeaveReportStudentAdmin(admin.ModelAdmin):
    list_display = ['student', 'from_date', 'to_date', 'status', 'approved_by']
    list_filter = ['status', 'from_date']
    search_fields = ['student__roll_no', 'student__user__first_name']  # ✅ FIXED: Updated search fields

@admin.register(LeaveReportStaff)
class LeaveReportStaffAdmin(admin.ModelAdmin):
    list_display = ['professor', 'from_date', 'to_date', 'status', 'approved_by']
    list_filter = ['status', 'from_date']
    search_fields = ['professor__user__first_name', 'professor__user__last_name']  # ✅ FIXED: Updated search fields

@admin.register(FeedbackStudent)
class FeedbackStudentAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'created_at', 'replied_by']
    list_filter = ['subject', 'created_at']
    search_fields = ['student__roll_no']

@admin.register(FeedbackStaff)
class FeedbackStaffAdmin(admin.ModelAdmin):
    list_display = ['professor', 'created_at', 'replied_by']
    list_filter = ['created_at']
    search_fields = ['professor__user__first_name']  # ✅ FIXED: Updated search fields

@admin.register(NotificationStudent)
class NotificationStudentAdmin(admin.ModelAdmin):
    list_display = ['student', 'is_read', 'sent_by', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['student__roll_no']

@admin.register(NotificationStaff)
class NotificationStaffAdmin(admin.ModelAdmin):
    list_display = ['professor', 'is_read', 'sent_by', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['professor__user__first_name']  # ✅ FIXED: Updated search fields
