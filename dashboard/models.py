from django.db import models

# Create your models here.
from users.models import Account
from django.utils.translation import ugettext_lazy as _
from isc_auth.tools.uniform_tools import createRandomFields

import random
import pyotp

# Create your models here.

class Application(models.Model):
    '''
    iKey唯一
    '''
    sKey = models.CharField('Secret Key',max_length=40)
    iKey = models.CharField('Integration Key',max_length=20,unique=True)
    name = models.CharField(max_length=30)
    app_type = models.CharField(max_length=30)
    account = models.ForeignKey(Account,on_delete=models.CASCADE)
    is_admin = models.BooleanField(
        _('admin status'), default=False,
        help_text=_('Designates whether the application create by admin'))

    def __str__(self):
        return "%s | %s" % (self.name,self.iKey)

    @classmethod
    def new_app(self,api_hostname):
        '''
        返回一个参数字典，包含随机生成的sKey,iKey(唯一)，凭借iKey可唯一确定application
        '''
        sKey = createRandomFields(40)
        iKey = createRandomFields(20)
        while len(Application.objects.filter(iKey=iKey))>0:
            iKey = createRandomFields(20)
        ret = {
            'sKey':sKey,
            'iKey':iKey,

        }
        return ret

class Group(models.Model):
    '''
    在一个hostname下，group_name唯一
    '''
    gKey = models.CharField('Group Key',max_length=20,unique=True)
    group_name = models.CharField(max_length=30)
    group_description = models.EmailField(max_length=100,blank=True,default=' ')
    group_status = models.CharField(max_length=10,default='Active',
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    account = models.ForeignKey(Account,on_delete=models.CASCADE)

    @classmethod
    def new_group_key(self,api_hostname):
        '''
        返回一个参数字典，包含随机生成的gKey(唯一)
        '''
        gKey = createRandomFields(20)
        while len(self.objects.filter(gKey=gKey))>0:
            gKey = createRandomFields(20)
        ret = {
            'gKey':gKey,
        }
        return ret

    class Meta():
        unique_together=(("group_name","account"),)

class User(models.Model):
    '''
    在一个hostname下，user_name唯一
    '''
    uKey = models.CharField('User Key',max_length=20,unique=True)
    user_name = models.CharField(max_length=30)
    user_real_name = models.CharField(max_length=30,blank= True)
    user_phone = models.CharField(max_length=11,blank=True,)
    user_email = models.EmailField(max_length=30,blank=True)
    user_status = models.CharField(max_length=10,default='Active',
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    account = models.ForeignKey(Account,on_delete=models.CASCADE)
    # group = models.ForeignKey(Group,on_delete=models.CASCADE,blank=True)
    group = models.ForeignKey(Group,on_delete=models.CASCADE,default= 1)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)

    @classmethod
    def new_user_key(self,api_hostname):
        '''
        返回一个参数字典，包含随机生成的uKey(唯一)
        '''
        uKey = createRandomFields(20)
        while len(User.objects.filter(uKey=uKey))>0:
            uKey = createRandomFields(20)
        ret = {
            'uKey':uKey,
        }
        return ret

    class Meta():
        unique_together=(("user_name","account"),)

    def __str__(self):
        return "%s | %s" %(self.user_name,self.account)

class Device(models.Model):
    '''
    一个user，多个设备。设备ID唯一,凭借ID可唯一确定设备
    '''
    identifer = models.CharField(max_length=20)
    is_activated = models.BooleanField(default=False)
    #用于与APP的通信
    dKey = models.CharField('Device Key',max_length=256,null=True)
    seed = models.CharField('Random Seed',max_length=16,null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    account = models.ForeignKey(Account,on_delete=models.CASCADE)
    device_name = models.CharField(max_length=30,null=True)
    device_model = models.CharField(max_length=20,null=True)
    platform = models.CharField(max_length=20,null=True)

    def __str__(self):
        return "%s | %s | %s" %(self.identifer,self.is_activated,self.user.user_name)

    @classmethod
    def new_device(self,api_hostname):
        '''
        返回一个参数字典，包含随机生成的identifer(唯一)
        '''
        identifer = createRandomFields(20)
        while len(Device.objects.filter(identifer=identifer))>0:
            identifer = createRandomFields(20)
        ret = {
            'identifer':identifer,
            'seed':pyotp.random_base32()
        }
        return ret

    class Meta():
        unique_together=(("identifer","account"),)
