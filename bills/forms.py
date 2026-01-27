from django import forms
from .models import Bill

class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['name', 'amount', 'due_date', 'status', 'category', 'notes', 'recurring', 'receipt_image']
        widgets = {
            'due_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter bill name'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any notes about this bill (optional)'
            }),
            'recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'receipt_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'receipt_image': 'Receipt Image (Optional)',
            'recurring': 'Is this a recurring bill?',
        }