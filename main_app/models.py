
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager, AbstractUser
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models

class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    USER_TYPE = ((1, "HOD"), (2, "Professor"), (3, "Student"))
    GENDER = [("M", "Male"), ("F", "Female")]

    username = None
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField(blank=True, null=True)
    address = models.TextField()
    fcm_token = models.TextField(default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"

class Department(models.Model):
    dept_id = models.AutoField(primary_key=True)
    dept_name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.dept_name

class Batch(models.Model):
    batch_id = models.AutoField(primary_key=True)
    start_year = models.PositiveIntegerField()  # ✅ Changed from DateField
    end_year = models.PositiveIntegerField()    # ✅ Changed from DateField
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.department.dept_name} - {self.start_year} to {self.end_year}"


class Year(models.Model):
    year_id = models.AutoField(primary_key=True)
    year_no = models.IntegerField()  # 1, 2, 3, 4
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['year_no', 'department']

    def __str__(self):
        return f"Year {self.year_no} - {self.department.dept_name}"

class Semester(models.Model):
    sem_id = models.AutoField(primary_key=True)
    sem_no = models.IntegerField()  # 1, 2
    year = models.ForeignKey(Year, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['sem_no', 'year']

    def __str__(self):
        return f"Semester {self.sem_no} - {self.year}"

# Represents a system administrator or HOD linked to a user account and optionally assigned to a specific department.
class Admin(models.Model):
    # ✅ FIXED: Removed the conflicting user_id field
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Admin: {self.user.first_name} {self.user.last_name}"


#Represents a professor with departmental association, linked user account, and optional admin manager.
class Professor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    managed_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Prof. {self.user.first_name} {self.user.last_name}"
    

# Represents a student with academic and personal details linked to a user account.
class Student(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    roll_no = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    year = models.ForeignKey(Year, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.roll_no} - {self.user.first_name} {self.user.last_name}"


class Subject(models.Model):
    SUBJECT_TYPES = [
        ('THEORY', 'Theory'),
        ('LAB', 'Laboratory'),
    ]
    
    subject_id = models.AutoField(primary_key=True)
    subject_name = models.CharField(max_length=120)
    subject_code = models.CharField(max_length=20, unique=True)
    subject_type = models.CharField(max_length=10, choices=SUBJECT_TYPES, default='THEORY')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    taught_by = models.ManyToManyField(Professor, related_name='subjects_taught')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"

class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.BooleanField(default=False)  # True = Present, False = Absent
    marked_by = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'subject', 'date']

    def __str__(self):
        status_text = "Present" if self.status else "Absent"
        return f"{self.student.roll_no} - {self.subject.subject_code} - {self.date} - {status_text}"

class TheoryMarks(models.Model):
    theory_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    ca1 = models.FloatField(default=0, help_text="Continuous Assessment 1")
    ca2 = models.FloatField(default=0, help_text="Continuous Assessment 2")
    ca3 = models.FloatField(default=0, help_text="Continuous Assessment 3")
    end_sem = models.FloatField(default=0, help_text="End Semester Exam")
    total_marks = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'subject']

    def save(self, *args, **kwargs):
        self.total_marks = self.ca1 + self.ca2 + self.ca3 + self.end_sem
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.roll_no} - {self.subject.subject_code} - Theory"

class LabMarks(models.Model):
    lab_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    pca1 = models.FloatField(default=0, help_text="Practical CA 1")
    pca2 = models.FloatField(default=0, help_text="Practical CA 2")
    end_sem_practical = models.FloatField(default=0, help_text="End Semester Practical")
    total_marks = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'subject']

    def save(self, *args, **kwargs):
        self.total_marks = self.pca1 + self.pca2 + self.end_sem_practical
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.roll_no} - {self.subject.subject_code} - Lab"

class LeaveReportStudent(models.Model):
    LEAVE_STATUS = [
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected')
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    message = models.TextField()
    status = models.SmallIntegerField(choices=LEAVE_STATUS, default=0)
    approved_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.roll_no} - Leave from {self.from_date} to {self.to_date}"

class LeaveReportStaff(models.Model):
    LEAVE_STATUS = [
        (0, 'Pending'),
        (1, 'Approved'),
        (2, 'Rejected')
    ]
    
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    message = models.TextField()
    status = models.SmallIntegerField(choices=LEAVE_STATUS, default=0)
    approved_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.professor.user.first_name} - Leave from {self.from_date} to {self.to_date}"

class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True)
    feedback = models.TextField()
    reply = models.TextField(blank=True)
    replied_by = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback by {self.student.roll_no}"

class FeedbackStaff(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField(blank=True)
    replied_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback by {self.professor.user.first_name}"

class NotificationStaff(models.Model):
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_by = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification for {self.professor.user.first_name}"

class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_by = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Notification for {self.student.roll_no}"

# Signal handlers
# @receiver(post_save, sender=CustomUser)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         if instance.user_type == 1:  # HOD/Admin
#             Admin.objects.create(user=instance)  # ✅ Changed from admin=instance
#         elif instance.user_type == 2:  # Professor
#             Professor.objects.create(user=instance)  # ✅ Changed from admin=instance
#         elif instance.user_type == 3:  # Student
#             Student.objects.create(user=instance)  # ✅ Changed from admin=instance

# @receiver(post_save, sender=CustomUser)
# def save_user_profile(sender, instance, **kwargs):
#     try:
#         if instance.user_type == 1:
#             if hasattr(instance, 'admin'):
#                 instance.admin.save()
#         elif instance.user_type == 2:
#             if hasattr(instance, 'professor'):
#                 instance.professor.save()
#         elif instance.user_type == 3:
#             if hasattr(instance, 'student'):
#                 instance.student.save()
#     except Exception:
#         pass

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:  # HOD/Admin
            Admin.objects.create(user=instance)
        elif instance.user_type == 2:  # Professor
            # ✅ FIXED: Don't create Professor automatically - let the view handle it
            pass  
        elif instance.user_type == 3:  # Student
            # ✅ FIXED: Don't create Student automatically - let the view handle it
            pass

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    # Remove or simplify this function since we're handling profile creation manually
    pass
