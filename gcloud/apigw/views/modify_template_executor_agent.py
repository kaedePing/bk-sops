# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making 蓝鲸智云PaaS平台社区版 (BlueKing PaaS Community
Edition) available.
Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
Licensed under the MIT License (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://opensource.org/licenses/MIT
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
the specific language governing permissions and limitations under the License.
"""

import ujson as json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from blueapps.account.decorators import login_exempt
from gcloud import err_code
from gcloud.apigw.decorators import mark_request_whether_is_trust, return_json_response
from gcloud.apigw.decorators import project_inject
from gcloud.core.apis.drf.serilaziers import CreateTaskTemplateSerializer
from gcloud.iam_auth.intercept import iam_intercept
from gcloud.iam_auth.view_interceptors.apigw import TemplateEditInterceptor
from gcloud.tasktmpl3.models import TaskTemplate
from apigw_manager.apigw.decorators import apigw_require


@login_exempt
@csrf_exempt
@require_POST
@apigw_require
@return_json_response
@mark_request_whether_is_trust
@project_inject
@iam_intercept(TemplateEditInterceptor())
def modify_template_executor_agent(request, template_id, project_id):
    project = request.project
    try:
        params = json.loads(request.body)
    except Exception:
        return {"result": False, "message": "invalid json format", "code": err_code.REQUEST_PARAM_INVALID.code}

    executor_proxy = params.get("executor_proxy", "")
    
    try:
        template = TaskTemplate.objects.get(id=template_id, project_id=project.id, is_deleted=False)
    except TaskTemplate.DoesNotExist:
        return {
            "result": False,
            "message": "template[id={template_id}] of project[project_id={project_id}] does not exist".format(
                template_id=template_id,
                project_id=project.id
            ),
            "code": err_code.CONTENT_NOT_EXIST.code,
        }

    # 直接调用字段级别的验证方法
    serializer = CreateTaskTemplateSerializer(instance=template, data={}, partial=True, context={"request": request})
    
    # 只验证executor_proxy字段
    try:
        validated_executor_proxy = serializer.validate_executor_proxy(executor_proxy)
    except Exception as e:
        return {
            "result": False,
            "message": str(e),
            "code": err_code.REQUEST_PARAM_INVALID.code,
        }
    
    # 直接更新字段并保存
    template.executor_proxy = validated_executor_proxy
    template.save()

    return {
        "result": True,
        "data": {
            "template_id": template.id,
            "executor_proxy": template.executor_proxy
        },
        "code": err_code.SUCCESS.code,
    }
