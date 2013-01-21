# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

login_required = method_decorator(login_required)
permission_required = method_decorator(permission_required)