from plugins.linux import sysinfo


def LinuxSysInfo():
    return sysinfo.collect()


def WindowsSysInfo():
    from plugins.windows import sysinfo as win_sysinfo  # 写在函数里面, 否则在Linux运行时会报错
    return win_sysinfo.collect()
