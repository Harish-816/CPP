from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Crop

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CropForm(forms.ModelForm):
    class Meta:
        model = Crop
        fields = ['name', 'summary', 'image']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 4}),
        }
