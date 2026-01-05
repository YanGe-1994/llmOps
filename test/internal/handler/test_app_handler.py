#!/use/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   :2026/1/5 17:16
@Author :yange2615@gmail.com
@File   :test_app_handler
"""
import pytest
from pkg.response import HttpCode

class TestAppHandler:
    @pytest.mark.parametrize("query", [None, "你好，你是?"])
    def test_completion(self, client, query):
        r = client.post("/app/completion", json={"query": query})
        assert r.status_code == 200
        if query is None:
            assert r.json.get("code") == HttpCode.VALIDATE_ERROR
        else:
            assert r.json.get("code") == HttpCode.SUCCESS