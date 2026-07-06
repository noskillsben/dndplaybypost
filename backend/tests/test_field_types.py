import pytest
from pydantic import ValidationError

from core import field_types as ft
from core.schema_builder import ObjectRegistration


def build(name, field, required=True):
    reg = ObjectRegistration(system="testsys", entry_type="thing")
    reg.add_field(name, field, required=required)
    return reg.model()


class TestShortText:
    def test_accepts_string(self):
        Model = build("title", ft.short_text(10))
        assert Model(title="hello").title == "hello"

    def test_rejects_too_long(self):
        Model = build("title", ft.short_text(5))
        with pytest.raises(ValidationError):
            Model(title="too long for five")

    def test_form_field(self):
        f = ft.short_text(50, placeholder="Name")
        assert f.to_form_field() == {"type": "text", "maxLength": 50, "placeholder": "Name"}


class TestLongTextAndMarkdown:
    def test_long_text_form(self):
        assert ft.long_text(200).to_form_field()["type"] == "textarea"

    def test_markdown_form(self):
        assert ft.markdown().to_form_field()["type"] == "markdown"

    def test_markdown_max_len(self):
        Model = build("body", ft.markdown(max_len=10))
        with pytest.raises(ValidationError):
            Model(body="x" * 11)


class TestInteger:
    def test_range_enforced(self):
        Model = build("level", ft.integer(0, 9))
        assert Model(level=3).level == 3
        with pytest.raises(ValidationError):
            Model(level=10)
        with pytest.raises(ValidationError):
            Model(level=-1)

    def test_required_integer_enforced(self):
        Model = build("level", ft.integer(0, 9), required=True)
        with pytest.raises(ValidationError):
            Model()

    def test_form_field(self):
        f = ft.integer(1, 20).to_form_field()
        assert f == {"type": "number", "step": 1, "min": 1, "max": 20}


class TestDecimal:
    def test_accepts_float(self):
        Model = build("weight", ft.decimal(0))
        assert Model(weight=2.5).weight == 2.5

    def test_range_enforced(self):
        Model = build("weight", ft.decimal(0, 100))
        with pytest.raises(ValidationError):
            Model(weight=-0.1)
        with pytest.raises(ValidationError):
            Model(weight=100.5)

    def test_form_field_defaults_step_any(self):
        f = ft.decimal(0).to_form_field()
        assert f["type"] == "number"
        assert f["step"] == "any"
        assert f["min"] == 0


class TestBoolean:
    def test_accepts_bool(self):
        Model = build("ritual", ft.boolean())
        assert Model(ritual=True).ritual is True

    def test_optional_defaults_none(self):
        Model = build("ritual", ft.boolean(), required=False)
        assert Model().ritual is None

    def test_form_field(self):
        assert ft.boolean("Ritual?").to_form_field() == {"type": "checkbox", "label": "Ritual?"}


class TestSelect:
    def test_accepts_valid_option(self):
        Model = build("school", ft.select(["evocation", "abjuration"]))
        assert Model(school="evocation").school == "evocation"

    def test_rejects_invalid_option(self):
        Model = build("school", ft.select(["evocation", "abjuration"]))
        with pytest.raises(ValidationError):
            Model(school="necromancy")

    def test_requires_options(self):
        with pytest.raises(ValueError):
            ft.select([])

    def test_form_field(self):
        f = ft.select(["a", "b"], label="Pick").to_form_field()
        assert f == {"type": "select", "options": ["a", "b"], "label": "Pick"}
