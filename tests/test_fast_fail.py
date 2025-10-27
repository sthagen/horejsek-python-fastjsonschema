import pytest

from fastjsonschema import JsonSchemaValueException, JsonSchemaValuesException, compile


def test_fast_fail():
    validator = compile({
        'type': 'object',
        'properties': {
            'string': {
                'type': 'string',
            },
            'number': {
                'type': 'number',
            },
        },
    })

    with pytest.raises(JsonSchemaValueException) as exc_info:
        validator({
            'string': 1,
            'number': 'a',
        })
    assert exc_info.value.message == 'data.string must be string'


def test_captures_all_errors():
    validator = compile({
        'type': 'object',
        'properties': {
            'string': {
                'type': 'string',
            },
            'number': {
                'type': 'number',
            },
        },
    }, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator({
            'string': 1,
            'number': 'a',
        })
    assert len(exc_info.value.errors) == 2
    assert exc_info.value.errors[0].message == 'data.string must be string'
    assert exc_info.value.errors[1].message == 'data.number must be number'
