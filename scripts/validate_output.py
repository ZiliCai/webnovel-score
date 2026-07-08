import json, pathlib
from jsonschema import Draft7Validator

_SCHEMA_DIR = pathlib.Path(__file__).resolve().parents[1] / "schemas"


def _load(name):
    return json.loads((_SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _errors(obj, schema_name):
    v = Draft7Validator(_load(schema_name))
    return [e.message for e in v.iter_errors(obj)]


def validate_signal_card(obj):
    return _errors(obj, "signal_card.schema.json")


def validate_synthesis(obj):
    return _errors(obj, "synthesis.schema.json")
