import importlib.util
import timeit
import tempfile
from textwrap import dedent

# apt-get install jsonschema json-spec validictory
import fastjsonschema
import jsonschema
import validictory
from jsonspec.validators import load


NUMBER = 1000

JSON_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-04/schema#',
    'type': 'array',
    'items': [
        {
            'type': 'number',
            'maximum': 10,
            'exclusiveMaximum': True,
        },
        {
            'type': 'string',
            'enum': ['hello', 'world'],
        },
        {
            'type': 'array',
            'minItems': 1,
            'maxItems': 3,
            'items': [
                {'type': 'number'},
                {'type': 'string'},
                {'type': 'boolean'},
            ],
        },
        {
            'type': 'object',
            'required': ['a', 'b'],
            'minProperties': 3,
            'properties': {
                'a': {'type': ['null', 'string']},
                'b': {'type': ['null', 'string']},
                'c': {'type': ['null', 'string'], 'default': 'abc'}
            },
            'additionalProperties': {'type': 'string'},
        },
        {'not': {'type': ['null']}},
        {'oneOf': [
            {'type': 'number', 'multipleOf': 3},
            {'type': 'number', 'multipleOf': 5},
        ]},
    ],
}

VALUES_OK = (
    [9, 'hello', [1, 'a', True], {'a': 'a', 'b': 'b', 'd': 'd'}, 42, 3],
    [9, 'world', [1, 'a', True], {'a': 'a', 'b': 'b', 'd': 'd'}, 42, 3],
    [9, 'world', [1, 'a', True], {'a': 'a', 'b': 'b', 'c': 'xy'}, 42, 3],
    [9, 'world', [1, 'a', True], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
)

VALUES_BAD = (
    [10, 'world', [1, 'a', True], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
    [9, 'xxx', [1, 'a', True], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
    [9, 'hello', [], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
    [9, 'hello', [1, 2, 3], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
    [9, 'hello', [1, 'a', True], {'a': 'a', 'x': 'x', 'y': 'y'}, 'str', 5],
    [9, 'hello', [1, 'a', True], {}, 'str', 5],
    [9, 'hello', [1, 'a', True], {'a': 'a', 'b': 'b', 'x': 'x'}, None, 5],
    [9, 'hello', [1, 'a', True], {'a': 'a', 'b': 'b', 'x': 'x'}, 42, 15],
)


fastjsonschema_validate = fastjsonschema.compile(JSON_SCHEMA)
fastjsonschema_validate_without_exc = fastjsonschema.compile(JSON_SCHEMA, detailed_exceptions=False)


def fast_compiled(value, _):
    fastjsonschema_validate(value)


def fast_not_compiled(value, json_schema):
    fastjsonschema.compile(json_schema)(value)


def fast_compiled_without_exc(value, _):
    fastjsonschema_validate_without_exc(value)


validator_class = jsonschema.validators.validator_for(JSON_SCHEMA)
validator = validator_class(JSON_SCHEMA)


def jsonschema_compiled(value, _):
    validator.validate(value)


with tempfile.NamedTemporaryFile('w', suffix='.py') as tmp_file:
    tmp_file.write(fastjsonschema.compile_to_code(JSON_SCHEMA))
    tmp_file.flush()
    spec = importlib.util.spec_from_file_location("temp.performance", tmp_file.name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def fast_file(value, _):
    module.validate(value)


jsonspec = load(JSON_SCHEMA)


def t(func, valid_values=True):
    module = func.split('.')[0]

    setup = """from __main__ import (
        JSON_SCHEMA,
        VALUES_OK,
        VALUES_BAD,
        validictory,
        jsonschema,
        jsonspec,
        fast_compiled,
        fast_compiled_without_exc,
        fast_file,
        fast_not_compiled,
        jsonschema_compiled,
    )
    """

    if valid_values:
        code = dedent("""
        for value in VALUES_OK:
            {}(value, JSON_SCHEMA)
        """.format(func))
    else:
        code = dedent("""
        try:
            for value in VALUES_BAD:
                {}(value, JSON_SCHEMA)
        except:
            pass
        """.format(func))

    res = timeit.timeit(code, setup, number=NUMBER)
    print('{:<30} {:<10} ==> {:10.7f}'.format(module, 'valid' if valid_values else 'invalid', res))


print('Number: {}'.format(NUMBER))

t('fast_compiled')
t('fast_compiled', valid_values=False)

t('fast_compiled_without_exc')
t('fast_compiled_without_exc', valid_values=False)

t('fast_file')
t('fast_file', valid_values=False)

t('fast_not_compiled')
t('fast_not_compiled', valid_values=False)

t('jsonschema.validate')
t('jsonschema.validate', valid_values=False)

t('jsonschema_compiled')
t('jsonschema_compiled', valid_values=False)

t('jsonspec.validate')
t('jsonspec.validate', valid_values=False)

t('validictory.validate')
t('validictory.validate', valid_values=False)
