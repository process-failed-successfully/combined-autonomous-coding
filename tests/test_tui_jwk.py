import pytest
import json
from textual.app import App
from shared.tui_jwk import JwkLabTab
from textual.widgets import TextArea, Input, Select, Button

class JwkLabApp(App):
    def compose(self):
        yield JwkLabTab()

@pytest.mark.asyncio
async def test_jwk_generate_rsa():
    app = JwkLabApp()
    async with app.run_test() as pilot:
        # Default is RSA, size 2048
        app.query_one('#btn-jwk-generate', Button).press()
        await pilot.pause()

        output = app.query_one("#jwk-output", TextArea).text
        assert output != ""

        jwk = json.loads(output)
        assert jwk["kty"] == "RSA"
        assert "n" in jwk
        assert "e" in jwk
        assert "d" in jwk

@pytest.mark.asyncio
async def test_jwk_generate_ec():
    app = JwkLabApp()
    async with app.run_test() as pilot:
        select = app.query_one("#gen-type", Select)
        select.value = "EC"

        app.query_one('#btn-jwk-generate', Button).press()
        await pilot.pause()

        output = app.query_one("#jwk-output", TextArea).text
        assert output != ""

        jwk = json.loads(output)
        assert jwk["kty"] == "EC"
        assert jwk["crv"] == "P-256"
        assert "x" in jwk
        assert "y" in jwk
        assert "d" in jwk

@pytest.mark.asyncio
async def test_jwk_pem_to_jwk_empty():
    app = JwkLabApp()
    async with app.run_test() as pilot:
        app.query_one('#btn-jwk-pem2jwk', Button).press()
        await pilot.pause()

        output = app.query_one("#jwk-output", TextArea).text
        assert output == "" # It notifies but doesn't set text

@pytest.mark.asyncio
async def test_jwk_jwk_to_pem_empty():
    app = JwkLabApp()
    async with app.run_test() as pilot:
        app.query_one('#btn-jwk-jwk2pem', Button).press()
        await pilot.pause()

        output = app.query_one("#jwk-output", TextArea).text
        assert output == ""

@pytest.mark.asyncio
async def test_jwk_roundtrip():
    app = JwkLabApp()
    async with app.run_test() as pilot:
        # 1. Generate RSA
        app.query_one('#btn-jwk-generate', Button).press()
        await pilot.pause()

        jwk_text = app.query_one("#jwk-output", TextArea).text
        assert jwk_text != ""

        # 2. Convert JWK to PEM
        app.query_one('#btn-jwk-jwk2pem', Button).press()
        await pilot.pause()

        pem_text = app.query_one("#jwk-output", TextArea).text
        assert pem_text.startswith("-----BEGIN PRIVATE KEY-----")

        # 3. Convert PEM back to JWK
        app.query_one("#pem-input", TextArea).text = pem_text
        app.query_one('#btn-jwk-pem2jwk', Button).press()
        await pilot.pause()

        new_jwk_text = app.query_one("#jwk-output", TextArea).text
        new_jwk = json.loads(new_jwk_text)

        orig_jwk = json.loads(jwk_text)

        assert new_jwk["kty"] == "RSA"
        assert new_jwk["n"] == orig_jwk["n"]
