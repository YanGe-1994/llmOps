#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/4 11:30
@Author :yange2615@gmail.com
@File   :app_schema
"""
from  flask_wtf import FlaskForm
from  wtforms import StringField
from wtforms.validators import DataRequired, length


class CompletionReq(FlaskForm):
    """基础聊天接口请求验证"""
    query = StringField('query', validators=[
        DataRequired(message="用户的提问是必填的"), # 必填校验
        length(max=2000,message="用户的提问最大请求是2000") #长度校验
    ])