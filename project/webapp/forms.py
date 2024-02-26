from django import forms

class form_login(forms.Form):
    password = forms.CharField(max_length=32)