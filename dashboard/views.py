from django.shortcuts import render
from django.template.response import TemplateResponse

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from .models import Application,Account,User,Group
from django.core import serializers
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage

import time,json

@login_required
def index(request):
    user = request.user
    content = {
        'active_menu' : 'Dashboard',
        'user' : user,
    }
    return render(request,'dashboard/index.html',content)

@login_required
def applications(request,args=None):
    user = request.user
    state=None
    if args:
        print(args)
        state = args['state']
    content = {
        'active_menu' : 'Dashboard',
        'user' : user,
        'state': state,
    }
    return render(request,'dashboard/applications/index.html',content)

@login_required
def get_applications(request):
    '''
    get application lists
    :param request:
    :return:
    '''
    user = request.user
    if request.method == "GET":
        limit = request.GET.get('limit')   # how many items per page
        offset = request.GET.get('offset')  # how many items in total in the DB
        search = request.GET.get('search')
        sort_column = request.GET.get('sort')   # which column need to sort
        order = request.GET.get('order')      # ascending or descending
        if search:    #    判断是否有搜索字
            all_records = Application.objects.filter(id=search,asset_type=search,business_unit=search,idc=search)
        else:
            all_records = Application.objects.filter(account= user)   # must be wirte the line code here

        if sort_column:   # 判断是否有排序需求
            sort_column = sort_column.replace('asset_', '')
            if sort_column in ['app_type','name']:   # 如果排序的列表在这些内容里面
                if order == 'desc':   # 如果排序是反向
                    sort_column = '-%s' % (sort_column)
                all_records = Application.objects.filter(account= user).order_by(sort_column)

        all_records_count=all_records.count()

        if not offset:
            offset = 0
        if not limit:
            limit = 20    # 默认是每页20行的内容，与前端默认行数一致
        pageinator = Paginator(all_records, limit)   # 开始做分页

        page = int(int(offset) / int(limit) + 1)
        response_data = {'total':all_records_count,'rows':[]}   # 必须带有rows和total这2个key，total表示总页数，rows表示每行的内容


        for asset in pageinator.page(page):
            response_data['rows'].append({
                "asset_name": '<a href="/dashboard/applications/detail/?iKey=%s">%s</a>' %(asset.iKey,asset.name),
                "asset_app_type": asset.app_type if asset.app_type else "",
            })
        return  HttpResponse(json.dumps(response_data))    # 需要json处理下数据格式

@login_required
def app_detail(request):
    '''
    show application detail
    :param request:
    :return:
    '''
    user = request.user
    app_iKey = request.GET.get('iKey','')
    if app_iKey == '':
        return HttpResponseRedirect(reverse('applications'))
    try:
        app = Application.objects.get(iKey= app_iKey)
        print(app.iKey)
    except Application.DoesNotExist:
        return HttpResponseRedirect(reverse('applications'))
    content = {
        'active_menu' : 'Applications',
        'user' : user,
        'app' :app,
    }
    return render(request,'dashboard/applications/app_detail.html',content)


@login_required
def add_applications(request):
    user = request.user
    state = None
    if request.method == 'POST':
        new_applications = Application(
            sKey = Application.new_app(user.api_hostname)['sKey'],
            iKey = Application.new_app(user.api_hostname)['iKey'],
            name = request.POST.get('application_name','')+str(int(time.time())),
            app_type = request.POST.get('type',''),
            account = Account.get_account(user.api_hostname),
            is_admin = False,
        )
        new_applications.save()
        state = 'success'
        return HttpResponseRedirect("/dashboard/applications/detail/?iKey=%s"%(new_applications.iKey))

    content = {
        'active_menu' : 'add_applications',
        'user' : user,
        'state': state,
    }
    return render(request,'dashboard/applications/add.html',content)

@login_required
def delete_applications(request):
    user = request.user
    if request.method == 'POST':
        iKey = request.POST.get('iKey','')
        Application.objects.filter(iKey=iKey).delete()
    return HttpResponseRedirect(reverse('applications'))


@login_required
def users(request,args=None):
    user = request.user
    state=None
    if args:
        print(args)
        state = args['state']
    content = {
        'active_menu' : 'Users',
        'user' : user,
        'state': state,
    }
    return render(request,'dashboard/users/index.html',content)

@login_required
def get_users(request):
    '''
    get application lists
    :param request:
    :return:
    '''
    user = request.user
    if request.method == "GET":
        limit = request.GET.get('limit')   # how many items per page
        offset = request.GET.get('offset')  # how many items in total in the DB
        search = request.GET.get('search')
        sort_column = request.GET.get('sort')   # which column need to sort
        order = request.GET.get('order')      # ascending or descending
        if search:    #    判断是否有搜索字
            all_records = User.objects.filter(id=search,asset_type=search,business_unit=search)
        else:
            all_records = User.objects.filter(account= user)  # must be wirte the line code here

        if sort_column:   # 判断是否有排序需求
            sort_column = sort_column.replace('asset_', '')
            if sort_column in ['user_name','name','email','status','last_login']:   # 如果排序的列表在这些内容里面
                if order == 'desc':   # 如果排序是反向
                    sort_column = '-%s' % (sort_column)
                all_records = User.objects.filter(account= user).order_by(sort_column)

        all_records_count=all_records.count()

        if not offset:
            offset = 0
        if not limit:
            limit = 20    # 默认是每页20行的内容，与前端默认行数一致
        pageinator = Paginator(all_records, limit)   # 开始做分页

        page = int(int(offset) / int(limit) + 1)
        response_data = {'total':all_records_count,'rows':[]}   # 必须带有rows和total这2个key，total表示总页数，rows表示每行的内容


        for asset in pageinator.page(page):
            response_data['rows'].append({
                "asset_user_name": '<a href="/dashboard/users/detail/?uKey=%s">%s</a>' %(asset.uKey,asset.user_name),
                "asset_name": asset.user_real_name if asset.user_real_name else "",
                "asset_email": asset.user_email if asset.user_email else "",
                "asset_status": asset.user_status if asset.user_status else "",
                "asset_last_login": asset.last_login if asset.last_login else "未激活",
            })
        return  HttpResponse(json.dumps(response_data))    # 需要json处理下数据格式

@login_required
def add_users(request):
    user = request.user
    state = None
    if request.method == 'POST':
        user_name = request.POST.get('user_name')
        account = Account.objects.get(api_hostname= user.api_hostname)
        account_user = User.objects.filter(account= account)
        qs = account_user.filter(user_name__iexact=user_name)
        if qs.exists():
            content = {
                'duplicate_name': '您所填写的用户名已被其它用户使用.',
                'state': 'error',
            }
            return render(request,'dashboard/users/add.html',content)
        new_user = User(
            uKey = User.new_user_key()['uKey'],
            user_name = request.POST.get('user_name'),
            account = Account.get_account(user.api_hostname),
        )
        new_user.save()
        return HttpResponseRedirect("/dashboard/users/detail/?uKey=%s"%(new_user.uKey))
    print(123)
    content = {
        'active_menu' : 'add_users',
        'user' : user,
        'state': state,

    }
    return render(request,'dashboard/users/add.html',content)

@login_required
def users_detail(request):
    '''
    show application detail
    :param request:
    :return:
    '''
    user = request.user
    uKey = request.GET.get('uKey','')
    if uKey == '':
        return HttpResponseRedirect(reverse('users'))
    try:
        users = User.objects.get(uKey= uKey)
        print(users.uKey)
    except Application.DoesNotExist:
        return HttpResponseRedirect(reverse('users'))
    content = {
        'active_menu' : 'Users',
        'user' : user,
        'users' :users,
    }
    return render(request,'dashboard/users/users_detail.html',content)

@login_required
def delete_user(request):
    user = request.user
    if request.method == 'POST':
        uKey = request.POST.get('uKey','')
        User.objects.filter(uKey=uKey).delete()
    return HttpResponseRedirect(reverse('users'))



@login_required
def groups(request,args=None):
    user = request.user
    state=None
    if args:
        print(args)
        state = args['state']
    content = {
        'active_menu' : 'Groups',
        'user' : user,
        'state': state,
    }
    return render(request,'dashboard/groups/index.html',content)

@login_required
def get_groups(request):
    '''
    get application lists
    :param request:
    :return:
    '''
    user = request.user
    if request.method == "GET":
        limit = request.GET.get('limit')   # how many items per page
        offset = request.GET.get('offset')  # how many items in total in the DB
        search = request.GET.get('search')
        sort_column = request.GET.get('sort')   # which column need to sort
        order = request.GET.get('order')      # ascending or descending
        if search:    #    判断是否有搜索字
            all_records = Group.objects.filter(id=search,asset_type=search,business_unit=search)
        else:
            all_records = Group.objects.filter(account= user)   # must be wirte the line code here

        if sort_column:   # 判断是否有排序需求
            sort_column = sort_column.replace('asset_', '')
            if sort_column in ['group_name','user_count','status']:   # 如果排序的列表在这些内容里面
                if order == 'desc':   # 如果排序是反向
                    sort_column = '-%s' % (sort_column)
                all_records = Group.objects.filter(account= user).order_by(sort_column)

        all_records_count=all_records.count()

        if not offset:
            offset = 0
        if not limit:
            limit = 20    # 默认是每页20行的内容，与前端默认行数一致
        pageinator = Paginator(all_records, limit)   # 开始做分页

        page = int(int(offset) / int(limit) + 1)
        response_data = {'total':all_records_count,'rows':[]}   # 必须带有rows和total这2个key，total表示总页数，rows表示每行的内容


        for asset in pageinator.page(page):
            response_data['rows'].append({
                "asset_group_name": '<a href="/dashboard/groups/detail/?gKey=%s">%s</a>' %(asset.gKey,asset.group_name),
                "asset_user_count": '0',
                "asset_status": asset.group_status if asset.group_status else "",
                "asset_description": asset.group_description if asset.group_description else "",
            })
        return  HttpResponse(json.dumps(response_data))    # 需要json处理下数据格式

@login_required
def add_groups(request):
    user = request.user
    state = None
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        group_description = request.POST.get('group_description')
        if group_description == None:
            group_description = ' '
        print(group_description)
        account = Account.objects.get(api_hostname= user.api_hostname)
        account_group = Group.objects.filter(account = account)
        qs = account_group.filter(group_name__iexact= group_name)
        if qs.exists():
            content = {
                'duplicate_name': '您所填写的组名已存在.',
                'state': 'error',
            }
            return render(request,'dashboard/groups/add.html',content)
        new_group = Group(
            gKey = Group.new_group_key(user.api_hostname)['gKey'],
            group_name = group_name,
            group_description = group_description,
            account = Account.get_account(user.api_hostname),
        )
        new_group.save()
        return HttpResponseRedirect("/dashboard/groups/detail/?gKey=%s"%(new_group.gKey))
    print(123)
    content = {
        'active_menu' : 'add_group',
        'user' : user,
        'state': state,

    }
    return render(request,'dashboard/groups/add.html',content)

@login_required
def groups_detail(request):
    '''
    show application detail
    :param request:
    :return:
    '''
    user = request.user
    gKey = request.GET.get('gKey','')
    if gKey == '':
        return HttpResponseRedirect(reverse('groups'))
    try:
        group = Group.objects.get(gKey= gKey)
        print(group.gKey)
    except Application.DoesNotExist:
        return HttpResponseRedirect(reverse('groups'))
    content = {
        'active_menu' : 'Groups',
        'user' : user,
        'group' :group,
    }
    return render(request,'dashboard/groups/group_detail.html',content)

@login_required
def delete_groups(request):
    user = request.user
    if request.method == 'POST':
        uKey = request.POST.get('uKey','')
        User.objects.filter(uKey=uKey).delete()
    return HttpResponseRedirect(reverse('users'))
