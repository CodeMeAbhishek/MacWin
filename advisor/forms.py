from django import forms

from django import forms

class ResumeForm(forms.Form):
    resume_text = forms.CharField(
        label='Paste your resume here',
        widget=forms.Textarea(attrs={
            'rows': 12,
            'placeholder': 'Paste your resume text (not the PDF) here...',
            'class': 'form-control'
        })
    )
