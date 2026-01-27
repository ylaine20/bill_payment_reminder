from django import forms
from .models import Bill, PaymentMethod, Budget, UserPreference, BillAttachment


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        fields = ['name', 'amount', 'due_date', 'status', 'category', 'notes', 
                  'recurring', 'recurrence_frequency', 'payment_method', 'receipt_image']
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
            'status': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add any notes about this bill (optional)'
            }),
            'recurring': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'recurrence_frequency': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'receipt_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        labels = {
            'receipt_image': 'Receipt Image (Optional)',
            'recurring': 'Recurring bill?',
            'recurrence_frequency': 'Repeat Every',
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=user)
        self.fields['payment_method'].required = False
        self.fields['recurrence_frequency'].required = False


class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['name', 'method_type', 'account_details', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., My GCash, BDO Savings'
            }),
            'method_type': forms.Select(attrs={'class': 'form-select'}),
            'account_details': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account number or details (optional)'
            }),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'monthly_limit', 'is_active']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'monthly_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ['email_reminders_enabled', 'remind_days_before', 'daily_digest_enabled', 'dark_mode']
        widgets = {
            'email_reminders_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'remind_days_before': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 30
            }),
            'daily_digest_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'dark_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'email_reminders_enabled': 'Enable email reminders',
            'remind_days_before': 'Days before due date to remind',
            'daily_digest_enabled': 'Receive daily bill summary',
            'dark_mode': 'Dark mode',
        }


class BillAttachmentForm(forms.ModelForm):
    class Meta:
        model = BillAttachment
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.gif'
            }),
        }
