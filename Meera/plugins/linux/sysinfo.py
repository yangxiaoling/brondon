import subprocess, os


def collect():
    filter_keys = ['Manufacturer', 'Serial Number', 'Product Name', 'UUID', 'Wake-up Type']
    raw_data = {}

    for key in filter_keys:
        try:
            cmd_res = subprocess.Popen('sudo dmidecode -t system | grep "%s"' % key, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().decode()  # 在Linux系统下获取有关硬件方面的信息, Desktop Management Interface,DMI
            res_to_list = cmd_res.split(':')  # the second one is wanted string
            if len(res_to_list) > 1:
                raw_data[key] = res_to_list[1].strip()
            else:
                raw_data[key] = -1

        except Exception as e:
            print(e)
            raw_data[key] = -2  # means cmd went wrong

    data = {"asset_type": 'server'}
    data['manufactory'] = raw_data['Manufacturer']
    data['sn'] = raw_data['Serial Number']
    data['model'] = raw_data['Product Name']
    data['uuid'] = raw_data['UUID']
    data['wake_up_type'] = raw_data['Wake-up Type']

    data.update(cpuinfo())
    data.update(osinfo())
    data.update(raminfo())
    # data.update(nicinfo())
    # data.update(diskinfo())
    return data


def cpuinfo():
    base_cmd = 'cat /proc/cpuinfo'

    raw_data = {
        'cpu_model': "%s |grep 'model name' |head -1 " % base_cmd,  # 多核会输出多行
        'cpu_count': "%s |grep 'processor' |wc -l " % base_cmd,
        'cpu_core_count': "%s |grep 'cpu cores' |awk -F: '{SUM +=$2} END {print SUM}'" % base_cmd,
    }

    for k, cmd in raw_data.items():
        try:
            cmd_res = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().decode()
            raw_data[k] = cmd_res

        except ValueError as e:
            print(e)

    data = {
        "cpu_count": raw_data["cpu_count"],
        "cpu_core_count": raw_data["cpu_core_count"]
        }
    cpu_model = raw_data["cpu_model"].split(":")
    if len(cpu_model) > 1:
        data["cpu_model"] = cpu_model[1].strip()
    else:
        data["cpu_model"] = -1

    return data


def osinfo():
    distributor = subprocess.Popen("lsb_release -a |grep 'Distributor ID'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().decode().split(':')
    release = subprocess.Popen("lsb_release -a |grep Description", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().decode().split(':')
    data_dic = {
        "os_distribution": distributor[1].strip() if len(distributor) > 1 else None,
        "os_release": release[1].strip() if len(release) > 1 else None,
        "os_type": "linux",
    }
    return data_dic


def raminfo():
    raw_data = subprocess.Popen('sudo dmidecode -t 17', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # 内存
    raw_list = raw_data.stdout.read().decode().split('\n')
    raw_ram_list = []
    item_list = []

    for line in raw_list:
        if line.startswith('Memory Device'):
            raw_ram_list.append(item_list)
            item_list = []
        else:
            item_list.append(line.strip())

    ram_list = []
    for item in raw_ram_list:
        item_ram_size = 0
        ram_item_to_dic = {}
        for i in item:
            data = i.split(':')
            if len(data) == 2:
                key, v = data

                if key == 'Size':
                    if v.strip() != 'No Module Installed':
                        ram_item_to_dic['capacity'] = v.split()[0].strip()  # e.g split "1024 MB"
                        item_ram_size = int(v.split()[0])
                    else:
                        ram_item_to_dic['capacity'] = 0

                if key == 'Type':
                    ram_item_to_dic['model'] = v.strip()

                if key == 'Manufacturer':
                    ram_item_to_dic['manufacturer'] = v.strip()

                if key == 'Serial Number':
                    ram_item_to_dic['sn'] = v.strip()

                if key == 'Asset Tag':
                    ram_item_to_dic['asset Tag'] = v.strip()

                if key == 'Locator':
                    ram_item_to_dic['slot'] = v.strip()

        if item_ram_size == 0:
            pass
        else:
            ram_list.append(ram_item_to_dic)

    raw_total_size = subprocess.Popen("cat /proc/meminfo |grep MemTotal", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().decode().split(':')
    ram_data = {'ram': ram_list}

    if len(raw_total_size) == 2:
        total_md_size = int(raw_total_size[1].split()[0]) / 1024
        ram_data['ram_size'] = total_md_size

    return ram_data


def nicinfo():
    raw_data = subprocess.Popen('ifconfig -a', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raw_data = raw_data.stdout.read().decode().split('\n')

    nic_dic = {}
    next_ip_line = False
    last_mac_addr = None
    for line in raw_data:
        if next_ip_line:
            pass


def diskinfo():
    obj = DiskPlugin()
    return obj.linux()


class DiskPlugin:
    def linux(self):
        result = {'physical_disk_driver': []}
        try:
            script_path = os.path.dirname(os.path.abspath(__file__))
            shell_command = "sudo %s/MegaCli -PDList -aAll" % script_path  # 只能在戴尔服务器上执行， 查看做磁盘阵列之前的真实信息
            output = subprocess.Popen(shell_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.read().decode()
            result['physical_disk_driver'] = self.parse(output[1])
        except Exception as e:
            result['error'] = e
            return result

    def parse(self, content):
        pass