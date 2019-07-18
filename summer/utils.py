#_*_coding:utf-8_*_
__author__ = 'Alex Li'

import time,hashlib,json
from summer import models
from django.shortcuts import render,HttpResponse
from brondon import settings

from django.core.exceptions import ObjectDoesNotExist
def json_date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.strftime("%Y-%m-%d")


def json_datetime_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.strftime("%Y-%m-%d %H:%M:%S")


def gen_token(username,timestamp,token):
    token_format = "%s\n%s\n%s" %(username,timestamp,token)
    print('--->token format:[%s]'% token_format)

    obj = hashlib.md5()
    obj.update(token_format.encode())
    return obj.hexdigest()[10:17]


def token_required(func):
    def wrapper(*args,**kwargs):
        response = {"errors":[]}

        get_args = args[0].GET
        username = get_args.get("user")
        token_md5_from_client = get_args.get("token")
        timestamp = get_args.get("timestamp")
        if not username or not timestamp or not token_md5_from_client:  #只要有一个为空就完了
            response['errors'].append({"auth_failed":"This api requires token authentication!"})
            return HttpResponse(json.dumps(response))
        try:
            user_obj = models.UserProfile.objects.get(email=username)
            token_md5_from_server = gen_token(username,timestamp,user_obj.token)    #服务端也生成一个token，然后对比
            if token_md5_from_client != token_md5_from_server:
                response['errors'].append({"auth_failed":"Invalid username or token_id"})
            else:   #在相等的基础上判断是否超时
                if abs(time.time() - int(timestamp)) > settings.TOKEN_TIMEOUT:# default timeout 120  #一次失效
                    response['errors'].append({"auth_failed":"The token is expired!"})
                else:
                    #缺少一步，在缓存中比较
                    #要求速度，只能存放在缓存
                    #防止黑客攻击的原理：
                    # 一般情况下，黑客截取到数据会进行加工，所以黑客发送请求会迟于用户请求，
                    # 当服务端接收到用户请求先保存到缓存，当黑客发送请求后，那么服务端接收到的请求就不是第一次了。
                    # 但是用户请求不能永远保存在缓存，所以给缓存设置一个超时时间，当超过超时时间时请求无效。
                    pass #print "\033[31;1mPass authentication\033[0m"

                print("\033[41;1m;%s ---client:%s\033[0m" %(time.time(),timestamp), time.time() - int(timestamp))
        except ObjectDoesNotExist as e:
            response['errors'].append({"auth_failed":"Invalid username or token_id"})
        if response['errors']:
            return HttpResponse(json.dumps(response))
        else:
            return  func(*args,**kwargs)
    return wrapper



