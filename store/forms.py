from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    payment_method = forms.CharField(
        widget=forms.HiddenInput(attrs={
            'id': 'id_payment_method',
            'value': 'cod'
        }),
        required=False,
        initial='cod'
    )

    class Meta:
        model = Order
        fields = ['full_name', 'phone_number', 'shipping_address', 'payment_method']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control block w-full px-4 py-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-800 focus:ring-4 focus:ring-slate-800/5 transition duration-200',
                'placeholder': 'Juan Dela Cruz',
                'required': 'required'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control block w-full px-4 py-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-800 focus:ring-4 focus:ring-slate-800/5 transition duration-200',
                'placeholder': '09171234567',
                'pattern': '^(09|\\+639)\\d{9}$',
                'title': 'Enter a valid Philippine mobile number (e.g. 09171234567)',
                'required': 'required'
            }),
            'shipping_address': forms.Textarea(attrs={
                'class': 'form-control block w-full px-4 py-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-800 focus:ring-4 focus:ring-slate-800/5 transition duration-200',
                'placeholder': 'House/Bldg No., Street, Barangay, City, Province',
                'rows': 3,
                'required': 'required'
            }),
        }

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        # Basic validation for Philippine numbers
        import re
        if not re.match(r'^(09|\+639)\d{9}$', phone):
            raise forms.ValidationError("Please enter a valid Philippine mobile number (e.g., 09171234567).")
        return phone

    def clean_payment_method(self):
        method = self.cleaned_data.get('payment_method')
        if not method or method not in ['cod', 'online']:
            return 'cod'
        return method

