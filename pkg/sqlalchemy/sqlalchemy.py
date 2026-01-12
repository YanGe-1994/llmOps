#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/10 16:05
@Author :yange2615@gmail.com
@File   :sqlalchemy
"""
from contextlib import contextmanager
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy

class SQLAlchemy(_SQLAlchemy):
    """重写SqlAlchemy的核心类，实现自动提交"""
    @contextmanager
    def auto_commit(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e