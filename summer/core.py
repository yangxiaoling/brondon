import json
from summer import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

class Asset:
    def __init__(self, request):
        self.request = request
        self.mandatory_fields = ['sn', 'asset_id', 'asset_type']  # must contains 'sn' , 'asset_id' and 'asset_type'
        self.field_sets = {
            'asset': ['manufactory'],
            'server': ['model', 'cpu_count', 'cpu_core_count', 'cpu_model', 'raid_type', 'os_type', 'os_distribution', 'os_release'],
            'networkdevice': []
        }
        self.response = {
            'error': [],
            'info': [],
            'warning': []
        }

    def get_asset_id_by_sn(self):
        data = self.request.POST.get('asset_data')
        if data:
            try:
                data = json.loads(data)
                if self.mandatory_check(data, only_check_sn=True):
                    response = {'asset_id': self.asset_obj.id}  # 对应可能二, 第二次报告执行这里
                else:
                    if hasattr(self, 'waiting_approval'):  # 对应可能三, 首次报告执行这里
                        response = {'needs_aproval': "this is a new asset,needs IT admin's approval to create the new asset id."}
                        self.clean_data = data
                        self.save_new_asset_to_approval_zone()
                    else:
                        response = self.response  # 对应可能一
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
                response = self.response
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")
            response = self.response
        return response

    def mandatory_check(self, data, only_check_sn=False):
        for field in self.mandatory_fields:
            if field not in data:
                self.response_msg('error', 'MandatoryCheckFailed', "The field [%s] is mandatory and not provided in your reporting data" % field)
        else:
            if self.response['error']:
                return False  # 没通过强制性验证  # 可能一

        try:
            if not only_check_sn:
                self.asset_obj = models.Asset.objects.get(id=int(data['asset_id']), sn=data['sn'])  # 审核执行这里
            else:
                self.asset_obj = models.Asset.objects.get(sn=data['sn'])  # 首次报告这里, 但找不到
            return True  # 可能二
        except ObjectDoesNotExist as e:
            self.response_msg('error', 'AssetDataInvalid', 'Cannot find asset object in DB by using asset id [%s] and SN [%s]' % (data['asset_id'], data['sn']))
            self.waiting_approval = True
            return False  # 可能三

    def response_msg(self, msg_type, key, msg):
        if msg_type in self.response:
            self.response[msg_type].append({key: msg})
        else:
            raise ValueError

    def save_new_asset_to_approval_zone(self):
        asset_sn = self.clean_data.get('sn')
        models.NewAssetApprovalZone.objects.get_or_create(
            sn=asset_sn,
            asset_type=self.clean_data.get('asset_type'),
            manufactory=self.clean_data.get('manufactory'),
            model=self.clean_data.get('model'),
            ram_size=self.clean_data.get('ram_size'),
            cpu_model=self.clean_data.get('cpu_model'),
            cpu_count=self.clean_data.get('cpu_count'),
            cpu_core_count=self.clean_data.get('cpu_core_count'),
            os_distribution=self.clean_data.get('os_distribution'),
            os_type=self.clean_data.get('os_type'),
            os_release=self.clean_data.get('os_release'),
            data=json.dumps(self.clean_data),
        )
        return True

    def data_is_valid_without_id(self):
        data = self.request.POST.get("asset_data")
        if data:
            try:
                data = json.loads(data)
                asset_obj = models.Asset.objects.get_or_create(sn=data.get('sn'))  # (<Asset: <id:11 name:>>, False)
                data['asset_id'] = asset_obj[0].id
                self.mandatory_check(data)
                self.clean_data = data
                if not self.response['error']:
                    return True
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")

    def data_is_valid(self):
        data = self.request.POST.get("asset_data")
        if data:
            try:
                data = json.loads(data)
                self.mandatory_check(data)
                self.clean_data = data
                if not self.response['error']:
                    return True
            except ValueError as e:
                self.response_msg('error', 'AssetDataInvalid', str(e))
        else:
            self.response_msg('error', 'AssetDataInvalid', "The reported asset data is not valid or provided")


    def data_inject(self):
        if self.__is_new_asset():
            print('\033[32;1m---new asset, going to create---\033[0m')
            self.create_asset()
        else:
            print('\033[33;1m---asset already exist, going to update---\033[0m')
            self.update_asset()

    def __is_new_asset(self):
        if not hasattr(self.asset_obj, self.clean_data['asset_type']):  # 仅判断Asset中有无asset_type字段
            return True
        else:
            return False

    def create_asset(self):
        func = getattr(self, '_create_%s' % self.clean_data['asset_type'])
        func()

    def update_asset(self):
        func = getattr(self, '_update_%s' % self.clean_data['asset_type'])
        func()

    def _create_server(self):
        self.__create_server_info()
        self.__create_or_update_manufactory()
        self.__create_cpu_component()
        self.__create_disk_component()
        self.__create_nic_component()
        self.__create_ram_component()

    def __create_server_info(self, ignore_errs=False):
        '''创建server表里的相关信息'''
        try:
            self.__verify_field(self.clean_data, 'model', str)
            if not len(self.response['error']) or ignore_errs:
                data_set = {
                    'asset_id': self.asset_obj.id,
                    'raid_type': self.clean_data.get('raid_type'),
                    'os_type': self.clean_data.get('os_type'),
                    'os_distribution': self.clean_data.get('os_distribution'),
                    'os_release': self.clean_data.get('os_release'),
                }
            obj = models.Server(**data_set)
            obj.asset.model = self.clean_data.get('model')  # 更新Asset
            obj.save()
            obj.asset.save()
            # return obj
        except Exception as e:
            self.response_msg('error', 'ObjectCreationException', 'Object [server] %s' % str(e))

    def __verify_field(self, data_set, field_key, data_type, required=True):
        field_val = data_set.get(field_key)
        if field_val or field_val == 0:  # 硬盘插槽slot=0
            try:
                data_set[field_key] = data_type(field_val)
            except ValueError as e:
                self.response_msg('error', 'InvalidField', "The field [%s]'s data type is invalid, the correct data type should be [%s]" % (field_key, data_type))
        elif required:
            self.response_msg('error', 'LackOfField', "The field [%s] has no value provided in your reporting data [%s]" % (field_key, data_set))

    def __create_or_update_manufactory(self, ignore_errs=False):
        try:
            self.__verify_field(self.clean_data, 'manufactory', str)
            manufactory = self.clean_data.get('manufactory')
            if not len(self.response['error']) or ignore_errs:
                obj_exist = models.Manufactory.objects.filter(manufactory=manufactory)  # queryset可以用来判断, 忘了是哪个了不能直接判断
                if obj_exist:
                    obj = obj_exist[0]
                else:
                    obj = models.Manufactory(manufactory=manufactory)
                    obj.save()
                self.asset_obj.manufactory = obj  # 更新Asset
                self.asset_obj.save()
        except Exception as e:
            self.response_msg('error', 'ObjectCreationException', 'Object [manufactory] %s' % str(e))

    def __create_cpu_component(self, ignore_errs=False):
        try:
            self.__verify_field(self.clean_data, 'cpu_model', str)
            self.__verify_field(self.clean_data, 'cpu_count', int)
            self.__verify_field(self.clean_data, 'cpu_core_count', int)
            if not len(self.response['error']) or ignore_errs:
                data_set = {
                    'asset_id': self.asset_obj.id,
                    'cpu_model': self.clean_data.get('cpu_model'),
                    'cpu_count': self.clean_data.get('cpu_count'),
                    'cpu_core_count': self.clean_data.get('cpu_core_count'),
                }
                obj = models.CPU(**data_set)
                obj.save()
                log_msg = "Asset[%s] --> has added new [cpu] component with data [%s]" % (self.asset_obj, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                # return obj
        except Exception as e:
            self.response_msg('error', 'ObjectCreationException', 'Object [cpu] %s' % str(e))

    def __create_disk_component(self):
        disk_info = self.clean_data.get('physical_disk_driver')
        if disk_info:
            for disk_item in disk_info:
                try:
                    self.__verify_field(disk_item, 'slot', str)
                    self.__verify_field(disk_item, 'capacity', float)
                    self.__verify_field(disk_item, 'iface_type', str)
                    self.__verify_field(disk_item, 'model', str)
                    if not len(self.response['error']):
                        data_set = {
                            'asset_id': self.asset_obj.id,
                            'sn': disk_item.get('sn'),
                            'slot': disk_item.get('slot'),
                            'capacity': disk_item.get('capacity'),
                            'model': disk_item.get('model'),
                            'iface_type': disk_item.get('iface_type'),
                            'manufactory': disk_item.get('manufactory')
                        }
                        obj = models.Disk(**data_set)
                        obj.save()
                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [disk] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'Disk info is not provied in your reporting data')

    def __create_nic_component(self):
        nic_info = self.clean_data.get('nic')
        if nic_info:
            for nic_item in nic_info:
                try:
                    self.__verify_field(nic_item, 'macaddress', str)
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_id': self.asset_obj.id,
                            'name': nic_item.get('name'),
                            'sn': nic_item.get('sn'),
                            'macaddress': nic_item.get('macaddress'),
                            'ipaddress': nic_item.get('ipaddress'),
                            'bonding': nic_item.get('bonding'),
                            'model': nic_item.get('model'),
                            'netmask': nic_item.get('netmask'),
                        }
                        obj = models.NIC(**data_set)
                        obj.save()
                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [nic] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'NIC info is not provied in your reporting data')

    def __create_ram_component(self):
        ram_info = self.clean_data.get('ram')
        if ram_info:
            for ram_item in ram_info:
                try:
                    self.__verify_field(ram_item, 'capacity', int)
                    print('ram', self.response)
                    if not len(self.response['error']):  # no processing when there's no error happend
                        data_set = {
                            'asset_id': self.asset_obj.id,
                            'slot': ram_item.get("slot"),
                            'sn': ram_item.get('sn'),
                            'capacity': ram_item.get('capacity'),
                            'model': ram_item.get('model'),
                        }
                        obj = models.RAM(**data_set)
                        obj.save()
                except Exception as e:
                    self.response_msg('error', 'ObjectCreationException', 'Object [ram] %s' % str(e))
        else:
            self.response_msg('error', 'LackOfData', 'RAM info is not provied in your reporting data')

    def _update_server(self):
        self.__update_asset_component(data_source=self.clean_data['nic'],
                                      fk='nic_set',
                                      update_fields=['name', 'sn', 'model', 'macaddress', 'ipaddress', 'netmask', 'bonding'],
                                      identify_field='macaddress')
        self.__update_asset_component(data_source=self.clean_data['physical_disk_driver'],
                                      fk='disk_set',
                                      # update_fields=['slot', 'sn', 'model', 'manufactory', 'capacity', 'iface_type'],
                                      update_fields=['slot', 'sn', 'model', 'capacity', 'iface_type'],
                                      identify_field='slot',
                                      )
        self.__update_asset_component(data_source=self.clean_data['ram'],
                                      fk='ram_set',
                                      update_fields=['slot', 'sn', 'model', 'capacity'],
                                      identify_field='slot'
                                      )
        self.__update_cpu_component()
        self.__update_manufactory_component()
        self.__update_server_component()

    def __update_asset_component(self, data_source, fk, update_fields, identify_field=None):
        component_obj = getattr(self.asset_obj, fk)  # asset_obj.nic_set
        if hasattr(component_obj, 'select_related'):
            objects_from_db = component_obj.select_related()
            for obj in objects_from_db:
                key_field_data = getattr(obj, identify_field)  # db中的mac地址

                for source_data_item in data_source:
                    key_field_data_from_source_data = source_data_item.get(identify_field)  # 客户端发来的mac地址
                    if key_field_data_from_source_data:
                        if key_field_data == key_field_data_from_source_data:
                            self.__compare_componet(model_obj=obj,
                                                    fields_from_db=update_fields,
                                                    data_source=source_data_item)
                            break
                    else:
                        self.response_msg('warning', 'AssetUpdateWarning', "Asset component [%s]'s key field [%s] is not provided in reporting data " % (fk, identify_field))
                else:
                    print('\033[33;1mError:cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!\033[0m' % (key_field_data))
                    self.response_msg("error", "AssetUpdateWarning", "Cannot find any matches in source data by using key field val [%s],component data is missing in reporting data!" % (key_field_data))

            self.__filter_add_or_deleted_components(
                model_obj_name=component_obj.model._meta.object_name,
                data_from_db=objects_from_db,
                data_source=data_source,
                identify_field=identify_field,
            )

    def __update_cpu_component(self):
        update_fields = ['cpu_model', 'cpu_count', 'cpu_core_count']
        if hasattr(self.asset_obj, 'cpu'):
            self.__compare_componet(model_obj=self.asset_obj.cpu,
                                    fields_from_db=update_fields,
                                    data_source=self.clean_data)
        else:
            self.__create_cpu_component(ignore_errs=True)

    def __update_manufactory_component(self):
        self.__create_or_update_manufactory(ignore_errs=True)

    def __update_server_component(self):
        update_fields = ['model', 'raid_type', 'os_type', 'os_distribution', 'os_release']
        if hasattr(self.asset_obj, 'server'):
            self.__compare_componet(model_obj=self.asset_obj.server,
                                    fields_from_db=update_fields,
                                    data_source=self.clean_data)
        else:
            self.__create_server_info(ignore_errs=True)

    def __compare_componet(self, model_obj, fields_from_db, data_source):
        for field in fields_from_db:
            val_from_db = getattr(model_obj, field)
            val_from_data_source = data_source.get(field)
            if val_from_data_source:
                if type(val_from_db) == int:
                    val_from_data_source = int(val_from_data_source)
                elif type(val_from_db) == float:
                    val_from_data_source = float(val_from_data_source)
                elif type(val_from_db) == str:
                    val_from_data_source = str(val_from_data_source).strip()

                if val_from_db == val_from_data_source:
                    pass
                else:
                    print('\033[34;1m val_from_db[%s] != val_from_data_source[%s]\033[0m' % (val_from_db, val_from_data_source), type(val_from_db), type(val_from_data_source), field)
                    db_field = model_obj._meta.get_field(field)
                    db_field.save_form_data(model_obj, val_from_data_source)
                    model_obj.update_date = timezone.now()
                    log_msg = "Asset[%s] --> component[%s] --> field[%s] has changed from [%s] to [%s]" % (self.asset_obj, model_obj, field, val_from_db, val_from_data_source)
                    self.response_msg('info', 'FieldChanged', log_msg)
                    log_handler(self.asset_obj, 'FieldChanged', self.request.user, log_msg, model_obj)
            else:
                self.response_msg('warning', 'AssetUpdateWarning', "Asset component [%s]'s field [%s] is not provided in reporting data " % (model_obj, field))

        model_obj.save()

    def __filter_add_or_deleted_components(self, model_obj_name, data_from_db, data_source, identify_field):
        data_source_key_list = []
        for data in data_source:
            data_source_key_list.append(data.get(identify_field))
        data_source_key_list = set(data_source_key_list)
        data_identify_val_from_db = set([getattr(obj, identify_field) for obj in data_from_db])
        data_only_in_db = data_identify_val_from_db - data_source_key_list
        data_only_in_data_source = data_source_key_list - data_identify_val_from_db
        self.__delete_components(
            all_components=data_from_db,
            delete_list=data_only_in_db,
            identify_field=identify_field,
        )
        if data_only_in_data_source:
            self._add_components(
                model_obj_name=model_obj_name,
                all_components=data_source,
                add_list=data_only_in_data_source,
                identify_field=identify_field,
            )

    def __delete_components(self, all_components, delete_list, identify_field):
        deleting_obj_list = []
        for obj in all_components:
            val = getattr(obj, identify_field)
            if val in delete_list:
                deleting_obj_list.append(obj)
        for i in deleting_obj_list:
            log_msg = "Asset[%s] --> component[%s] --> is lacking from reporting source data, assume it has been removed or replaced,will also delete it from DB" %(self.asset_obj,i)
            self.response_msg('info','HardwareChanges',log_msg)
            log_handler(self.asset_obj,'HardwareChanges',self.request.user,log_msg,i)
            i.delete()

    def _add_components(self, model_obj_name, all_components, add_list, identify_field):
        model_class = getattr(models, model_obj_name)
        will_be_creating_list = []
        for data in all_components:
            if data[identify_field] in add_list:
                will_be_creating_list.append(data)

        try:
            for component in will_be_creating_list:
                data_set = {}
                for field in model_class.auto_create_fields:
                    data_set[field] = component.get(field)
                data_set['asset_id'] = self.asset_obj.id
                obj = model_class(**data_set)
                obj.save()
                print('\033[32;1mCreated component with data:\033[0m', data_set)
                log_msg = "Asset[%s] --> component[%s] has justed added a new item [%s]" % (
                self.asset_obj, model_obj_name, data_set)
                self.response_msg('info', 'NewComponentAdded', log_msg)
                log_handler(self.asset_obj,
                            'NewComponentAdded',
                            self.request.user,
                            log_msg,
                            model_obj_name)
        except Exception as e:
            print("\033[31;1m %s \033[0m" % e)
            log_msg = "Asset[%s] --> component[%s] has error: %s" % (self.asset_obj, model_obj_name, str(e))
            self.response_msg('error', "AddingComponentException", log_msg)


def log_handler(asset_obj, event_name, user, detail, component=None):
    print('fff', component)
    log_catelog = {
        1: ['FieldChanged', 'HardwareChanges'],
        2: ['NewComponentAdded'],
    }
    if not user.id:
        user = models.UserProfile.objects.filter(is_admin=True).last()
    event_type = None

    for k, v in log_catelog.items():
        if event_name in v:
            event_type = k
            break
    log_obj = models.EventLog(
        name=event_name,
        event_type=event_type,
        asset_id=asset_obj.id,
        component=component,
        detail=detail,
        user_id=user.id
    )
    log_obj.save()