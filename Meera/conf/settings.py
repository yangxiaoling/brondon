import os
BaseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Params = {
    'server': 'localhost',
    'port': 8000,
    'request_timeout': 30,
    'urls': {
        'asset_report_with_no_id': '/asset/report/asset_with_no_asset_id/',
        'asset_report': '/asset/report/',
    },
    'asset_id': '%s/var/.asset_id' % BaseDir,  # 存放asset_id的文件
    'log_file': '%s/logs/run_log' % BaseDir,
    'auth': {
        'user': 'brondon@126.com',
        'token': 'brondon'
    }
}