from django import forms
from django.utils.translation import ugettext_lazy as _
from .models import User

class UserForm(forms.ModelForm):
    
    error_messages = {
        'duplicate_name': _('您所填写的用户名已被其它用户使用.'),
    }
    user_name = forms.CharField(max_length=30)
    class Meta:
        model = User
        fields = '__all__'
    def clean(self):
        
        # Since User.email is unique, this check is redundant,
        # but it sets a nicer error message than the ORM. See #13147.
        user_name = self.cleaned_data['user_name']
        qs = User.objects.filter(user_name__iexact=user_name)
        if qs.exists():
            raise forms.ValidationError(
                self.error_messages['duplicate_name'],
                code='duplicate_name',
            )
        return self.cleaned_data
        
    def save(self, commit=True):
        new_user = super(UserForm, self).save(commit=False)
        new_user.uKey = User.new_user_key(user.api_hostname)['uKey']
        if commit:
            new_user.save()
        return new_user
    