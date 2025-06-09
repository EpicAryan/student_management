# from django.shortcuts import get_object_or_404, render, redirect
# from django.views import View
# from django.contrib import messages
# from .models import Subject, Staff, Student, StudentResult
# from .forms import EditResultForm
# from django.urls import reverse


# class EditResultView(View):
#     def get(self, request, *args, **kwargs):
#         resultForm = EditResultForm()
#         staff = get_object_or_404(Staff, admin=request.user)
#         resultForm.fields['subject'].queryset = Subject.objects.filter(staff=staff)
#         context = {
#             'form': resultForm,
#             'page_title': "Edit Student's Result"
#         }
#         return render(request, "staff_template/edit_student_result.html", context)

#     def post(self, request, *args, **kwargs):
#         form = EditResultForm(request.POST)
#         context = {'form': form, 'page_title': "Edit Student's Result"}
#         if form.is_valid():
#             try:
#                 student = form.cleaned_data.get('student')
#                 subject = form.cleaned_data.get('subject')
#                 test = form.cleaned_data.get('test')
#                 exam = form.cleaned_data.get('exam')
#                 # Validating
#                 result = StudentResult.objects.get(student=student, subject=subject)
#                 result.exam = exam
#                 result.test = test
#                 result.save()
#                 messages.success(request, "Result Updated")
#                 return redirect(reverse('edit_student_result'))
#             except Exception as e:
#                 messages.warning(request, "Result Could Not Be Updated")
#         else:
#             messages.warning(request, "Result Could Not Be Updated")
#         return render(request, "staff_template/edit_student_result.html", context)

from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from .models import Subject, Professor, Student, TheoryMarks
from .forms import EditResultForm
from django.urls import reverse


class EditResultView(View):
    def get(self, request, *args, **kwargs):
        resultForm = EditResultForm()
        
        # ✅ FIXED LINE
        professor = get_object_or_404(Professor, user=request.user)
        
        resultForm.fields['subject'].queryset = Subject.objects.filter(taught_by=professor)
        context = {
            'form': resultForm,
            'page_title': "Edit Student's Result"
        }
        return render(request, "staff_template/edit_student_result.html", context)

    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST)
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            try:
                student = form.cleaned_data.get('student')
                subject = form.cleaned_data.get('subject')
                test = form.cleaned_data.get('test')
                exam = form.cleaned_data.get('exam')
                
                # Get or create the theory marks record
                result, created = TheoryMarks.objects.get_or_create(
                    student=student, 
                    subject=subject,
                    defaults={'ca1': 0, 'ca2': 0, 'ca3': 0, 'end_sem': 0}
                )
                
                # Map old test/exam fields to new structure
                # Assuming 'test' maps to ca3 and 'exam' maps to end_sem
                result.ca3 = test if test is not None else 0
                result.end_sem = exam if exam is not None else 0
                result.save()  # This will auto-calculate total_marks
                
                messages.success(request, "Result Updated Successfully")
                return redirect(reverse('edit_student_result'))
                
            except Exception as e:
                messages.error(request, f"Result Could Not Be Updated: {str(e)}")
        else:
            messages.warning(request, "Please correct the form errors")
            
        return render(request, "staff_template/edit_student_result.html", context)
