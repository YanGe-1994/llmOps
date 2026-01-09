#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/9 14:56
@Author :yange2615@gmail.com
@File   :module
"""
from flask_sqlalchemy import SQLAlchemy
from injector import Module, Binder
from internal.extension.database_extension import db

class ExtensionModule(Module):
    """扩展模块的依赖注入"""
    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)