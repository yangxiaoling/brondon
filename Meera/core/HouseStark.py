from core import info_collection

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
