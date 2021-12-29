from jsonschema._types import (
    TypeChecker, is_array, is_bool, is_integer,
    is_object, is_number,
)


def is_string(checker, instance):
    return isinstance(instance, (str, bytes))


oas30_type_checker = TypeChecker(
    {
        u"string": is_string,
        u"number": is_number,
        u"integer": is_integer,
        u"boolean": is_bool,
        u"array": is_array,
        u"object": is_object,
    },
)
