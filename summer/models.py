#__author:  Administrator
#date:  2017/3/6


from django.db import models


from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser,Group,PermissionsMixin
)
import django


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            # token=token,
            # department=department,
            # tel=tel,
            # memo=memo,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name ,password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(email,
            password=password,
            name=name,
            # token=token,
            # department=department,
            # tel=tel,
            # memo=memo,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


# class UserProfile(AbstractBaseUser):
class UserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    name = models.CharField(max_length=32)
    token = models.CharField('token', max_length=128, default=None, blank=True, null=True)
    department = models.CharField('部门', max_length=32, default=None, blank=True, null=True)
    # business_unit = models.ManyToManyField(BusinessUnit)
    tel = models.CharField('座机', max_length=32, default=None, blank=True, null=True)
    mobile = models.CharField('手机', max_length=32, default=None, blank=True, null=True)

    memo = models.TextField('备注', blank=True, null=True, default=None)
    date_joined = models.DateTimeField(blank=True, auto_now_add=True)
    # valid_begin = models.DateTimeField(blank=True, auto_now=True)
    valid_begin_time = models.DateTimeField(default=django.utils.timezone.now)
    valid_end_time = models.DateTimeField(blank=True, null=True)

    # groups = models.ManyToManyField

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['name','token','department','tel','mobile','memo']
    REQUIRED_FIELDS = ['name']

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def __str__(self):              # __unicode__ on Python 2
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_perms(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    class Meta:
        verbose_name = '用户信息'
        verbose_name_plural = "用户信息"

    objects = UserManager()


class Asset(models.Model):
    asset_type_choices = (
        ('server', '服务器'),
        ('networkdevice', '网络设备'),
        ('storagedevice', '存储设备'),
        ('securitydevice', '安全设备'),
        ('idcdevice', '机房设备'),
        # ('switch', '交换机'),
        # ('router', '路由器'),
        # ('firewall', '防火墙'),
        # ('storage', '存储设备'),
        # ('NLB', 'NetScaler'),
        # ('wireless', '无线AP'),
        ('software', '软件资产'),
        # ('others', '其它类'),
    )
    asset_type = models.CharField(choices=asset_type_choices, max_length=64, default='server')  # 作用是在反查时, 能够区分是反查哪张表(server、networkdevice)
    name = models.CharField(max_length=64, unique=True)
    sn = models.CharField('资产SN号', max_length=128, unique=True)
    manufactory = models.ForeignKey('Manufactory', verbose_name='制造商', null=True, blank=True, on_delete=models.CASCADE)  # 为啥可以为空??
    # model = models.ForeignKey('ProductModel', verbose_name='型号')
    # model = models.CharField('型号',max_length=128,null=True, blank=True )

    management_ip = models.GenericIPAddressField('管理IP', blank=True, null=True)

    contract = models.ForeignKey('Contract', verbose_name='合同', null=True, blank=True, on_delete=models.CASCADE)
    trade_date = models.DateField('购买时间', null=True, blank=True)
    expire_date = models.DateField('过保修期', null=True, blank=True)
    price = models.FloatField('价格', null=True, blank=True)
    business_unit = models.ForeignKey('BusinessUnit', verbose_name='所属业务线', null=True, blank=True, on_delete=models.CASCADE)  # 设备属于哪个业务线, 本来是多对多字段, 但考虑到子业务线就不适用了
    tags = models.ManyToManyField('Tag', blank=True)
    admin = models.ForeignKey('UserProfile', verbose_name='资产管理员', null=True, blank=True, on_delete=models.CASCADE)
    idc = models.ForeignKey('IDC', verbose_name='IDC机房', null=True, blank=True, on_delete=models.CASCADE)

    status_choices = ((0, '在线'),
                      (1, '已下线'),
                      (2, '未知'),
                      (3, '故障'),
                      (4, '备用'),
                      )
    status = models.SmallIntegerField(choices=status_choices,default=0)
    #status = models.ForeignKey('Status', verbose_name = '设备状态',default=1)
    #Configuration = models.OneToOneField('Configuration',verbose_name='配置管理',blank=True,null=True)

    memo = models.TextField('备注', null=True, blank=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, auto_now=True)  # 自动更新

    class Meta:
        verbose_name = '资产总表'
        verbose_name_plural = "资产总表"

    def __str__(self):
        return '<id:%s name:%s>' % (self.id, self.name)


class Server(models.Model):
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_assset_type_choices = (
        (0, 'PC服务器'),
        (1, '刀片机'),
        (2, '小型机'),
    )
    created_by_choices = (
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_assset_type_choices, verbose_name="服务器类型", default=0)
    created_by = models.CharField(choices=created_by_choices, max_length=32, default='auto')  # auto: auto created, manual:created manually
    # hosted_on = models.ForeignKey('self', related_name='hosted_on_server', blank=True,null=True)  # for vitural server, 不支持虚拟机(因为虚拟机也有mac地址)
    # sn = models.CharField('SN号',max_length=128)
    # management_ip = models.CharField('管理IP',max_length=64,blank=True,null=True)
    # manufactory = models.ForeignKey(verbose_name='制造商',max_length=128,null=True, blank=True)
    model = models.CharField(verbose_name='型号', max_length=128, null=True, blank=True )
    # 若有多个CPU，型号应该都是一致的，故没做ForeignKey

    # nic = models.ManyToManyField('NIC', verbose_name='网卡列表')
    # disk
    raid_type = models.CharField('raid类型', max_length=512, blank=True, null=True)
    # physical_disk_driver = models.ManyToManyField('Disk', verbose_name='硬盘',blank=True,null=True)
    # raid_adaptor = models.ManyToManyField('RaidAdaptor', verbose_name='Raid卡',blank=True,null=True)
    # memory
    # ram_capacity = models.IntegerField('内存总大小GB',blank=True)
    # ram = models.ManyToManyField('Memory', verbose_name='内存配置',blank=True,null=True)

    os_type = models.CharField('操作系统类型', max_length=64, blank=True, null=True)
    os_distribution = models.CharField('发型版本', max_length=64, blank=True, null=True)
    os_release = models.CharField('操作系统版本', max_length=64, blank=True, null=True)

    class Meta:
        verbose_name = '服务器'
        verbose_name_plural = "服务器"
        # together = ["sn", "asset"]

    def __str__(self):
        return '%s sn:%s' % (self.asset.name, self.asset.sn)


class SecurityDevice(models.Model):
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_assset_type_choices = (
        (0, '防火墙'),
        (1, '入侵检测设备'),
        (2, '互联网网关'),
        (4, '运维审计系统'),
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_assset_type_choices, verbose_name="服务器类型", default=0)

    def __str__(self):
        return self.asset.id


class NetworkDevice(models.Model):
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)
    sub_assset_type_choices = (
        (0, '路由器'),
        (1, '交换机'),
        (2, '负载均衡'),
        (4, 'VPN设备'),
    )
    sub_asset_type = models.SmallIntegerField(choices=sub_assset_type_choices, verbose_name="服务器类型", default=0)

    vlan_ip = models.GenericIPAddressField('VlanIP', blank=True, null=True)
    intranet_ip = models.GenericIPAddressField('内网IP', blank=True, null=True)
    # sn = models.CharField('SN号',max_length=128,unique=True)
    # manufactory = models.CharField(verbose_name='制造商',max_length=128,null=True, blank=True)
    model = models.CharField('型号', max_length=128, null=True, blank=True)
    firmware = models.ForeignKey('Software', blank=True, null=True, on_delete=models.CASCADE)
    port_num = models.SmallIntegerField('端口个数', null=True, blank=True)
    device_detail = models.TextField('设置详细配置', null=True, blank=True)

    class Meta:
        verbose_name = '网络设备'
        verbose_name_plural = "网络设备"


class Software(models.Model):
    '''
    only save software which company purchased
    '''
    sub_assset_type_choices = (
        (0, 'OS'),
        (1, '办公\开发软件'),
        (2, '业务软件'),

    )
    sub_asset_type = models.SmallIntegerField(choices=sub_assset_type_choices, verbose_name="服务器类型", default=0)
    license_num = models.IntegerField(verbose_name="授权数")
    # os_distribution_choices = (('windows','Windows'),
    #                            ('centos','CentOS'),
    #                            ('ubunt', 'Ubunt'))
    # type = models.CharField('系统类型', choices=os_types_choice, max_length=64,help_text='eg. GNU/Linux',default=1)
    # distribution = models.CharField('发型版本', choices=os_distribution_choices,max_length=32,default='windows')
    version = models.CharField('软件/系统版本', max_length=64, help_text='eg. CentOS release 6.5 (Final)', unique=True)
    # language_choices = (('cn','中文'),
    #                     ('en','英文'))
    # language = models.CharField('系统语言',choices = language_choices, default='cn',max_length=32)
    # #version = models.CharField('版本号', max_length=64,help_text='2.6.32-431.3.1.el6.x86_64' )

    def __str__(self):
        return self.version

    class Meta:
        verbose_name = '软件/系统'
        verbose_name_plural = "软件/系统"


class CPU(models.Model):
    asset = models.OneToOneField('Asset', on_delete=models.CASCADE)  # 因为一个server上的cpu必须型号相同, 没必要写多条数据(即不需要ForeignKey)
    cpu_model = models.CharField('CPU型号', max_length=128, blank=True)
    cpu_count = models.SmallIntegerField('物理cpu个数')
    cpu_core_count = models.SmallIntegerField('cpu核数')
    memo = models.TextField('备注', null=True,blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'CPU部件'
        verbose_name_plural = "CPU部件"

    def __str__(self):
        return self.cpu_model


class RAM(models.Model):
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    sn = models.CharField('SN号', max_length=128, blank=True, null=True)  # 重复了啊??
    model = models.CharField('内存型号', max_length=128)
    slot = models.CharField('插槽', max_length=64)
    capacity = models.IntegerField('内存大小(MB)')
    memo = models.CharField('备注', max_length=128, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '%s:%s:%s' % (self.asset_id, self.slot, self.capacity)

    class Meta:
        verbose_name = 'RAM'
        verbose_name_plural = "RAM"
        unique_together = ("asset", "slot")
    auto_create_fields = ['sn', 'slot', 'model', 'capacity']


class Disk(models.Model):
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    sn = models.CharField('SN号', max_length=128, blank=True, null=True)
    slot = models.CharField('插槽位', max_length=64)
    # manufactory = models.CharField('制造商', max_length=64,blank=True,null=True)
    model = models.CharField('磁盘型号', max_length=128, blank=True, null=True)
    capacity = models.FloatField('磁盘容量GB')
    disk_iface_choice = (
        ('SATA', 'SATA'),
        ('SAS', 'SAS'),
        ('SCSI', 'SCSI'),
        ('SSD', 'SSD'),
    )
    iface_type = models.CharField('接口类型', max_length=64, choices=disk_iface_choice, default='SAS')
    memo = models.TextField('备注', blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    auto_create_fields = ['sn', 'slot', 'manufactory', 'model', 'capacity', 'iface_type']

    class Meta:
        unique_together = ("asset", "slot")
        verbose_name = '硬盘'
        verbose_name_plural = "硬盘"

    def __str__(self):
        return '%s:slot:%s capacity:%s' % (self.asset_id, self.slot, self.capacity)


class NIC(models.Model):
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)  # 关联Assert表, 是因为server和newwork都有网卡, Foreignkey无法直接关联多张表
    name = models.CharField('网卡名', max_length=64, blank=True, null=True)
    sn = models.CharField('SN号', max_length=128, blank=True, null=True)
    model = models.CharField('网卡型号', max_length=128, blank=True,null=True)
    macaddress = models.CharField('MAC', max_length=64, unique=True)
    ipaddress = models.GenericIPAddressField('IP', blank=True, null=True)
    netmask = models.CharField(max_length=64, blank=True, null=True)
    bonding = models.CharField(max_length=64, blank=True, null=True)  # 网卡绑定(例如, 两个1M网卡可绑定为一个2M网卡)
    memo = models.CharField('备注', max_length=128, blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return '%s:%s' % (self.asset_id, self.macaddress)
    
    class Meta:
        verbose_name = '网卡'
        verbose_name_plural = "网卡"
        # unique_together = ("asset_id", "slot")
        unique_together = ("asset", "macaddress")
    auto_create_fields = ['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask', 'bonding']


class RaidAdaptor(models.Model):
    '''做磁盘阵列'''
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)  # 一般一台机器上只有一个raid卡, 也可以有多个
    sn = models.CharField('SN号', max_length=128, blank=True, null=True)
    slot = models.CharField('插口', max_length=64)
    model = models.CharField('型号', max_length=64, blank=True, null=True)
    memo = models.TextField('备注', blank=True, null=True)
    create_date = models.DateTimeField(blank=True, auto_now_add=True)
    update_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ("asset", "slot")


class Manufactory(models.Model):
    manufactory = models.CharField('厂商名称', max_length=64, unique=True)
    support_num = models.CharField('支持电话', max_length=30, blank=True)
    memo = models.CharField('备注', max_length=128, blank=True)

    def __str__(self):
        return self.manufactory

    class Meta:
        verbose_name = '厂商'
        verbose_name_plural = "厂商"


class BusinessUnit(models.Model):
    parent_unit = models.ForeignKey('self', related_name='parent_level', blank=True, null=True, on_delete=models.CASCADE)  # 子业务线
    name = models.CharField('业务线', max_length=64)

    # contact = models.ForeignKey('UserProfile',default=None)
    memo = models.CharField('备注', max_length=64, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '业务线'
        verbose_name_plural = "业务线"
        unique_together = ("parent_unit", "name")


class Contract(models.Model):
    sn = models.CharField('合同号', max_length=128, unique=True)
    name = models.CharField('合同名称', max_length=64)
    memo = models.TextField('备注', blank=True, null=True)
    price = models.IntegerField('合同金额')
    detail = models.TextField('合同详细', blank=True, null=True)
    start_date = models.DateField(blank=True)
    end_date = models.DateField(blank=True)
    license_num = models.IntegerField('license数量', blank=True)
    create_date = models.DateField(auto_now_add=True)
    update_date = models.DateField(auto_now=True)

    class Meta:
        verbose_name = '合同'
        verbose_name_plural = "合同"

    def __str__(self):
        return self.name


class IDC(models.Model):
    name = models.CharField('机房名称', max_length=64, unique=True)
    memo = models.CharField('备注', max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '机房'
        verbose_name_plural = "机房"


class Tag(models.Model):
    name = models.CharField('Tag name', max_length=32, unique=True)
    creater = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    create_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name


class EventLog(models.Model):
    name = models.CharField('事件名称', max_length=100)
    event_type_choices = (
        (1, '硬件变更'),
        (2, '新增配件'),
        (3, '设备下线'),
        (4, '设备上线'),
        (5, '定期维护'),
        (6, '业务上线\更新\变更'),
        (7, '其它'),
    )
    event_type = models.SmallIntegerField('事件类型', choices=event_type_choices)
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE)
    component = models.CharField('事件子项', max_length=255, blank=True, null=True)
    detail = models.TextField('事件详情')
    date = models.DateTimeField('事件时间', auto_now_add=True)
    user = models.ForeignKey('UserProfile', verbose_name='事件源', on_delete=models.CASCADE)
    memo = models.TextField('备注', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '事件纪录'
        verbose_name_plural = "事件纪录"

    def colored_event_type(self):
        if self.event_type == 1:
            cell_html = '<span style="background: orange;">%s</span>'
        elif self.event_type == 2:
            cell_html = '<span style="background: yellowgreen;">%s</span>'
        else:
            cell_html = '<span >%s</span>'
        return cell_html % self.get_event_type_display()
    colored_event_type.allow_tags = True
    colored_event_type.short_description = '事件类型'


class NewAssetApprovalZone(models.Model):
    sn = models.CharField('资产SN号', max_length=128, unique=True)
    asset_type_choices = (
        ('server', '服务器'),
        ('switch', '交换机'),
        ('router', '路由器'),
        ('firewall', '防火墙'),
        ('storage', '存储设备'),
        ('NLB', 'NetScaler'),
        ('wireless', '无线AP'),
        ('software', '软件资产'),
        ('others', '其它类'),
    )
    asset_type = models.CharField(choices=asset_type_choices, max_length=64, blank=True, null=True)
    manufactory = models.CharField(max_length=64, blank=True, null=True)
    model = models.CharField(max_length=128, blank=True, null=True)
    ram_size = models.IntegerField(blank=True, null=True)
    cpu_model = models.CharField(max_length=128, blank=True, null=True)
    cpu_count = models.IntegerField(blank=True, null=True)
    cpu_core_count = models.IntegerField(blank=True, null=True)
    os_distribution = models.CharField(max_length=64, blank=True, null=True)
    os_type = models.CharField(max_length=64, blank=True, null=True)
    os_release = models.CharField(max_length=64, blank=True, null=True)
    data = models.TextField('资产数据')
    date = models.DateTimeField('汇报日期', auto_now_add=True)
    approved = models.BooleanField('已批准', default=False)
    approved_by = models.ForeignKey('UserProfile', verbose_name='批准人', blank=True, null=True, on_delete=models.CASCADE)
    approved_date = models.DateTimeField('批准日期', blank=True, null=True)

    def __str__(self):
        return self.sn

    class Meta:
        verbose_name = '新上线待批准资产'
        verbose_name_plural = "新上线待批准资产"
