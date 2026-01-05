#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/5 17:12
@Author :yange2615@gmail.com
@File   :conftest
"""
import pytest

from app.http.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client