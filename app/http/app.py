#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/2 11:44
@Author :yange2615@gmail.com
@File   :app
"""
import dotenv
from flask_sqlalchemy import SQLAlchemy

from injector import Injector

from .module import ExtensionModule
from internal.router import Router
from internal.server import Http
from config import Config


# 将env加载到环境变量中
dotenv.load_dotenv()

injector = Injector([ExtensionModule])

conf = Config()

app = Http(__name__,conf=conf,router= injector.get(Router), db=injector.get(SQLAlchemy))

if __name__ == "__main__":
    app.run(debug=True)