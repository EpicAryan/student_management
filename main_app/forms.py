
from django import forms
from django.forms.widgets import DateInput, TextInput

from .models import *


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField()

    # def __init__(self, *args, **kwargs):
    #     super(CustomUserForm, self).__init__(*args, **kwargs)
    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            # instance = kwargs.get('instance').admin.__dict__
            professor_instance = kwargs.get('instance')  # this is a Professor object
            user_instance = professor_instance.user
            self.fields['password'].required = False
            # for field in CustomUserForm.Meta.fields:
            #     self.fields[field].initial = instance.get(field)
            for field in CustomUserForm.Meta.fields:
                if hasattr(user_instance, field):
                    self.fields[field].initial = getattr(user_instance, field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk).user.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender', 'password', 'profile_pic', 'address']


class StudentForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + \
            ['roll_no', 'department', 'batch', 'year', 'semester']  # Updated field names


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields + ['department']  # Added department field


class ProfessorForm(CustomUserForm):  # Renamed from StaffForm
    def __init__(self, *args, **kwargs):
        super(ProfessorForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Professor
        fields = CustomUserForm.Meta.fields + \
            ['department']  # Updated field name


class DepartmentForm(FormSettings):  # Renamed from CourseForm
    def __init__(self, *args, **kwargs):
        super(DepartmentForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['dept_name']  # Updated field name
        model = Department


class SubjectForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Subject
        fields = ['subject_name', 'subject_code', 'subject_type', 'semester', 'taught_by']  # Updated field names


class BatchForm(FormSettings):
    start_year = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 2000, 'max': 2050, 'class': 'form-control'}),
        help_text="Enter start year (e.g., 2024)"
    )
    end_year = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': 2000, 'max': 2050, 'class': 'form-control'}),
        help_text="Enter end year (e.g., 2028)"
    )

    def __init__(self, *args, **kwargs):
        super(BatchForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Batch
        fields = ['department', 'start_year', 'end_year']

class YearForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(YearForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Year
        fields = ['year_no', 'department']
        widgets = {
            'year_no': forms.Select(choices=[(1, '1st Year'), (2, '2nd Year'), (3, '3rd Year'), (4, '4th Year')]),
        }


class SemesterForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SemesterForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Semester
        fields = ['sem_no', 'year']
        widgets = {
            'sem_no': forms.Select(choices=[(1, '1st Semester'), (2, '2nd Semester')]),
        }


class LeaveReportStaffForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStaff
        fields = ['from_date', 'to_date', 'message']  # Updated field names
        widgets = {
            'from_date': DateInput(attrs={'type': 'date'}),
            'to_date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStaffForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(FeedbackStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStaff
        fields = ['feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Share your feedback, suggestions, or concerns here...',
                'maxlength': 1000
            })
        }


class LeaveReportStudentForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStudent
        fields = ['from_date', 'message']  # ✅ FIXED: Use existing model fields
        widgets = {
            'from_date': DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'id': 'id_date'  # ✅ Use 'id_date' for JavaScript compatibility
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide a detailed reason for your leave request...',
                'maxlength': 500,
                'id': 'id_message'
            })
        }
        
    # ✅ Override field labels to hide the technical field names
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['from_date'].label = 'Leave Date'
        self.fields['message'].label = 'Reason for Leave'




class FeedbackStudentForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(FeedbackStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStudent
        fields = ['feedback', 'subject']  # Added subject field


class StudentEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + ['roll_no', 'department', 'batch']  # Updated fields


class ProfessorEditForm(CustomUserForm):  # Renamed from StaffEditForm
    def __init__(self, *args, **kwargs):
        super(ProfessorEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Professor
        fields = CustomUserForm.Meta.fields + ['department']  # Updated fields


# class EditResultForm(FormSettings):
#     batch_list = Batch.objects.all()  # Updated from Batch_list
#     batch_year = forms.ModelChoiceField(  # Updated from Batch_year
#         label="Batch Year", queryset=batch_list, required=True)

#     def __init__(self, *args, **kwargs):
#         super(EditResultForm, self).__init__(*args, **kwargs)

#     class Meta:
#         model = TheoryMarks  # Updated from StudentResult
#         fields = ['subject', 'student', 'ca1', 'ca2', 'ca3', 'end_sem']  # Updated field names


# Additional forms for the new models
class YearForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(YearForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Year
        fields = ['year_no', 'department']


class SemesterForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SemesterForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Semester
        fields = ['sem_no', 'year']


class LabMarksForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LabMarksForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LabMarks
        fields = ['subject', 'student', 'pca1', 'pca2', 'end_sem_practical']


class EditResultForm(forms.Form):
    """Form for editing both theory and lab results"""
    
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=True,
        empty_label="Select Subject",
        widget=forms.Select(attrs={
            'class': 'form-control enhanced-select',
            'id': 'id_subject'
        }),
        error_messages={
            'required': 'Please select a subject.',
            'invalid_choice': 'Please select a valid subject.'
        }
    )
    
    batch_year = forms.ModelChoiceField(
        queryset=Batch.objects.all().select_related('department').order_by('-start_year'),
        required=True,
        empty_label="Select Batch Year",
        widget=forms.Select(attrs={
            'class': 'form-control enhanced-select',
            'id': 'id_batch_year'
        }),
        error_messages={
            'required': 'Please select a batch year.',
            'invalid_choice': 'Please select a valid batch year.'
        }
    )
    
    student = forms.ModelChoiceField(
        queryset=Student.objects.none(),  # Will be populated via AJAX
        required=True,
        empty_label="Select Student",
        widget=forms.Select(attrs={
            'class': 'form-control enhanced-select',
            'id': 'id_student'
        }),
        error_messages={
            'required': 'Please select a student.',
            'invalid_choice': 'Please select a valid student.'
        }
    )
    
    # ✅ FIXED: Use FloatField to match your decimal data
    # Theory fields - all optional since user might only update some
    ca1 = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control enhanced-input',
            'step': '0.01',
            'placeholder': 'Enter CA1 Score'
        })
    )
    
    ca2 = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control enhanced-input',
            'step': '0.01',
            'placeholder': 'Enter CA2 Score'
        })
    )
    
    ca3 = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control enhanced-input',
            'step': '0.01',
            'placeholder': 'Enter CA3 Score'
        })
    )
    
    end_sem = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control enhanced-input',
            'step': '0.01',
            'placeholder': 'Enter End Semester Score'
        })
    )
    
    # Lab fields - all optional
    pca1 = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control enhanced-input',
            'step': '0.01',
            'placeholder': 'Enter PCA1 Score'
        })
    )
    
    pca2 = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control enhanced-input',
            'step': '0.01',
            'placeholder': 'Enter PCA2 Score'
        })
    )
    
    end_sem_practical = forms.FloatField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control enhanced-input',
            'step': '0.01',
            'placeholder': 'Enter End Sem Practical Score'
        })
    )

    def __init__(self, *args, **kwargs):
        student_queryset = kwargs.pop('student_queryset', None)
        super().__init__(*args, **kwargs)
        if student_queryset is not None:
            self.fields['student'].queryset = student_queryset
        
    def clean(self):
        """Custom validation to ensure at least one mark is provided"""
        cleaned_data = super().clean()
        
        # Check if at least one mark field has a value
        mark_fields = ['ca1', 'ca2', 'ca3', 'end_sem', 'pca1', 'pca2', 'end_sem_practical']
        has_marks = any(cleaned_data.get(field) is not None for field in mark_fields)
        
        if not has_marks:
            raise forms.ValidationError("Please enter at least one mark to update.")
        
        return cleaned_data


class StudentAttendanceViewForm(FormSettings):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.none(),  # Will be set in __init__
        empty_label="-- Choose a Subject --",
        widget=forms.Select(attrs={
            'class': 'subject-select',
            'id': 'subject_dropdown'
        }),
        error_messages={
            'required': 'Please select a subject.',
            'invalid_choice': 'Please select a valid subject.'
        }
    )
    
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'clean-input',
            'id': 'start_date'
        }),
        error_messages={
            'required': 'Please select a start date.',
            'invalid': 'Please enter a valid start date.'
        }
    )
    
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'clean-input',
            'id': 'end_date'
        }),
        error_messages={
            'required': 'Please select an end date.',
            'invalid': 'Please enter a valid end date.'
        }
    )
    
    def __init__(self, student=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if student:
            self.fields['subject'].queryset = Subject.objects.filter(semester=student.semester)
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise forms.ValidationError("Start date cannot be later than end date.")
        
        return cleaned_data

    class Meta:
        model = Subject  # Just for FormSettings inheritance
        fields = []  # We're not actually saving to a model
