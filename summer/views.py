from django.shortcuts import render, HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
from summer import core
from summer import models
from summer import utils
# Create your views here.


@csrf_exempt
def asset_with_no_asset_id(request):
    if request.method == 'POST':
        ass_handler = core.Asset(request)
        res = ass_handler.get_asset_id_by_sn()
        print('rrr', res)
        return HttpResponse(json.dumps(res))


def new_assets_approval(request):
    if request.method == 'POST':
        request.POST = request.POST.copy()
        approved_asset_list = request.POST.getlist('approved_asset_list')
        approved_asset_list = models.NewAssetApprovalZone.objects.filter(id__in=approved_asset_list)
        response_dic = {}
        for obj in approved_asset_list:
            request.POST['asset_data'] = obj.data
            ass_handler = core.Asset(request)
            if ass_handler.data_is_valid_without_id():
                ass_handler.data_inject()
                obj.approved = True
                obj.save()
            response_dic[obj.id] = ass_handler.response
        return render(request, 'assets/new_assets_approval.html', {'new_assets': approved_asset_list, 'response_dic': response_dic})
    else:
        ids = request.GET.get('ids')
        id_list = ids.split(',')
        new_assets = models.NewAssetApprovalZone.objects.filter(id__in=id_list)
        return render(request, 'assets/new_assets_approval.html', {'new_assets': new_assets})

@csrf_exempt
@utils.token_required
def asset_report(request):
    if request.method == "POST":
        asset_handler = core.Asset(request)
        if asset_handler.data_is_valid():
            asset_handler.data_inject()
        return HttpResponse(json.dumps(asset_handler.response))