#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/9 17:38
@Author :yange2615@gmail.com
@File   :app_service
"""

from injector import inject
from dataclasses import dataclass
from pkg.sqlalchemy import SQLAlchemy
from internal.model import App
import uuid

@inject
@dataclass
class AppService:
    """应用服务逻辑"""
    db: SQLAlchemy
    def create_app(self) -> App:
        with self.db.auto_commit():
            app = App(name="测试机器人",account_id=uuid.uuid4(), icon="", description="测试聊天机器人")
            self.db.session.add(app)
        return app

    def get_app(self,id: uuid.UUID) -> App:
        return self.db.session.query(App).get(id)

    def update_app(self,id: uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.get_app(id)
            app.name = '修改的聊天机器人'
        return app

    def delete_app(self,id: uuid.UUID) -> App:
        with self.db.auto_commit():
            app = self.get_app(id)
            self.db.session.delete(app)
        return app