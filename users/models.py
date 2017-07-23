from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


from .conf import settings
from .managers import UserInheritanceManager, UserManager
from isc_auth.tools.uniform_tools import createRandomFields

import random

# Create your models here.

class AbstractUser(AbstractBaseUser, PermissionsMixin):
    USERS_AUTO_ACTIVATE = not settings.USERS_VERIFY_EMAIL

    email = models.EmailField(
        _('email address'), max_length=255, unique=True, db_index=True)
    is_staff = models.BooleanField(
        _('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin site.'))

    is_active = models.BooleanField(
        _('active'), default=USERS_AUTO_ACTIVATE,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    user_type = models.ForeignKey(ContentType, null=True, editable=False)

    account_name = models.CharField(max_length=30)
    account_phone = models.CharField(max_length=11)
    api_hostname = models.CharField(max_length=8,unique=True)

    objects = UserInheritanceManager()
    base_objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        abstract = True

    def get_full_name(self):
        """ Return the email."""
        return self.account_name

    def get_short_name(self):
        """ Return the email."""
        return self.email

    def email_user(self, subject, message, from_email=None):
        """ Send an email to this User."""
        send_mail(subject, message, from_email, [self.email])

    def activate(self):
        self.is_active = True
        self.save()

    def save(self, *args, **kwargs):
        if not self.user_type_id:
            self.user_type = ContentType.objects.get_for_model(self, for_concrete_model=False)
        super(AbstractUser, self).save(*args, **kwargs)


class Account(AbstractUser):

    """
    Concrete class of AbstractUser.
    Use this if you don't need to extend User.
    """


    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'

    @classmethod
    def new_account_hostname(self):
        '''
        返回随机生成的hostname（唯一）
        '''
        api_hostname = createRandomFields(8)
        while len(Account.objects.filter(api_hostname=api_hostname)) > 0:
            api_hostname = createRandomFields(8)
        return api_hostname

    @classmethod
    def get_account(self,api_hostname):
        return self.objects.get(api_hostname=api_hostname)

    def __str__(self):
        return "%s | %s | %s" %(self.email,self.account_name,self.api_hostname)
