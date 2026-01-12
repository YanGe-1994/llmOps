#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/9 14:56
@Author :yange2615@gmail.com
@File   :module
"""
from pkg.sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from injector import Module, Binder
from internal.extension.database_extension import db
from internal.extension.migrate_extension import migrate
class ExtensionModule(Module):
    """扩展模块的依赖注入"""
    def configure(self, binder: Binder) -> None:
        binder.bind(SQLAlchemy, to=db)
        binder.bind(Migrate, to=migrate)