#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/2 11:44
@Author :yange2615@gmail.com
@File   :app
"""
from injector import Injector
from internal.router import Router
from internal.server import Http

injector = Injector()

app = Http(__name__,router= injector.get(Router))

if __name__ == "__main__":
    app.run(debug=True)