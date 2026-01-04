#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/4 11:37
@Author :yange2615@gmail.com
@File   :config
"""
class Config():
    def __init__(self):
        # 关闭wtf CSRF 保护
        self.WTF_CSRF_ENABLED = False