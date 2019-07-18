from core import info_collection
import json
from conf import settings
import os
import sys
from urllib import request, parse
import datetime
from core import api_token


class ArgvHandler:
    def __init__(self, argv_list):
        self.argv = argv_list
        self.parse_argv()

    def parse_argv(self):
        if len(self.argv) > 1:  # 有参数
            if hasattr(self, self.argv[1]):
                func = getattr(self, self.argv[1])
                func()
        else:
            self.help_msg()

    def help_msg(self):
        msg = '''
        collect_data
        run_forever
        get_asset_id
        report_asset
        '''
        print(msg)

    def collect_data(self):
        """收集资产数据，但不汇报"""
        obj = info_collection.InfoCollection()
        asset_data = obj.collect()
        print(asset_data)

    def report_asset(self):
        obj = info_collection.InfoCollection()
        asset_data = obj.collect()

        asset_id = self.load_asset_id()
        if asset_id:  # reported to server before
            asset_data['asset_id'] = asset_id
            post_url = 'asset_report'
        else:  # first time report to server
            '''report to another url,this will put the asset into approval waiting zone, 
            when the asset is approved , this request returns asset's ID'''
            asset_data['asset_id'] = None
            post_url = 'asset_report_with_no_id'

        data = {'asset_data': json.dumps(asset_data)}
        response = self.__submit_data(post_url, data, method='post')
        if 'asset_id' in response:  # 第二次报告还会走asset_with_no_asset_id, 返回asset_id, 表示已审核通过
            self.__update_asset_id(response['asset_id'])

        self.log_record(response)

    def load_asset_id(self):
        asset_id_file = settings.Params['asset_id']
        if os.path.isfile(asset_id_file):
            asset_id = open(asset_id_file).read().strip()
            if asset_id.isdigit():
                return asset_id
            else:
                has_asset_id = False
        else:
            has_asset_id = False

    def __submit_data(self, url_name, data, method):
        if url_name in settings.Params['urls']:
            if type(settings.Params['port']) is int:
                url = "http://%s:%s%s" % (settings.Params['server'], settings.Params['port'], settings.Params['urls'][url_name])
            else:
                url = "http://%s%s" % (settings.Params['server'], settings.Params['urls'][url_name])

            url = self.__attach_token(url)  # api认证
            print('Connecting [%s], it may take a minute' % url)
            if method == 'get':
                args = ''
                for k, v in data.items():
                    args += '&%s=%s' % (k, v)
                args = args[1:]
                url_with_args = '%s?%s' % (url, args)
                try:
                    req = request.Request(url_with_args)
                    req_data = request.urlopen(req, timeout=settings.Params['request_timeout'])
                    callback = req_data.read()
                    print("-->server response:", callback)
                    return json.loads(callback)
                except request.URLError as e:
                    sys.exit('\033[31;1m%s\033[0m' % e)
            elif method == 'post':
                try:
                    data_encode = parse.urlencode(data).encode()
                    req = request.Request(url=url, data=data_encode)
                    req_data = request.urlopen(req, timeout=settings.Params['request_timeout'])
                    callback = req_data.read()  # bytes类型
                    callback = json.loads(callback)  # dict类型
                    print("\033[33;1m[%s]:[%s]\033[0m response:\n%s" % (method, url, callback))
                    return callback
                except Exception as e:
                    sys.exit("\033[31;1m%s\033[0m" % e)
        else:
            raise KeyError

    def __update_asset_id(self, new_asset_id):
        asset_id_file = settings.Params['asset_id']
        f = open(asset_id_file, 'wb')
        f.write(str(new_asset_id).encode())
        f.close()

    def log_record(self, log):
        f = open(settings.Params['log_file'], 'ab')
        if type(log) == str:
            pass

        if type(log) == dict:
            if "info" in log:
                for msg in log["info"]:
                    log_format = "%s\tINFO\t%s\n" % (datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"), msg)
                    f.write(log_format.encode())
            if "error" in log:
                for msg in log["error"]:
                    log_format = "%s\tERROR\t%s\n" % (datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"), msg)
                    f.write(log_format.encode())
            if "warning" in log:
                for msg in log["warning"]:
                    log_format = "%s\tWARNING\t%s\n" % (datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S"), msg)
                    f.write(log_format.encode())
        f.close()

    def __attach_token(self, url_str):
        user = settings.Params['auth']['user']
        token_id = settings.Params['auth']['token']
        md5_token, timestamp = api_token.get_token(user, token_id)
        url_arg_str = "user=%s&timestamp=%s&token=%s" % (user, timestamp, md5_token)
        if "?" in url_str:
            new_url = url_str + "&" + url_arg_str
        else:
            new_url = url_str + "?" + url_arg_str
        return new_url
