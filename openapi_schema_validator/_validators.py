from jsonschema._utils import find_additional_properties, extras_msg
from jsonschema._validators import oneOf as _oneOf, anyOf as _anyOf, allOf as _allOf

from jsonschema.exceptions import ValidationError, FormatError


def handle_discriminator(validator, _, instance, schema):
    """
    Handle presence of discriminator in anyOf, oneOf and allOf.
    The behaviour is the same in all 3 cases because at most 1 schema will match.
    """
    discriminator = schema['discriminator']
    prop_name = discriminator['propertyName']
    prop_value = instance.get(prop_name)
    if not prop_value:
        # instance is missing $propertyName
        yield ValidationError(
            "%r does not contain discriminating property %r" % (instance, prop_name),
            context=[],
        )
        return

    # Use explicit mapping if available, otherwise try implicit value
    ref = discriminator.get('mapping', {}).get(prop_value) or f'#/components/schemas/{prop_value}'

    if not isinstance(ref, str):
        # this is a schema error
        yield ValidationError(
            "%r mapped value for %r should be a string, was %r" % (
                instance, prop_value, ref),
            context=[],
        )
        return

    try:
        validator.resolver.resolve(ref)
    except:
        yield ValidationError(
            "%r reference %r could not be resolved" % (
                instance, ref),
            context=[],
        )
        return

    yield from validator.descend(instance, {
        "$ref": ref
    })


def anyOf(validator, anyOf, instance, schema):
    if 'discriminator' not in schema:
        yield from _anyOf(validator, anyOf, instance, schema)
    else:
        yield from handle_discriminator(validator, anyOf, instance, schema)


def oneOf(validator, oneOf, instance, schema):
    if 'discriminator' not in schema:
        yield from _oneOf(validator, oneOf, instance, schema)
    else:
        yield from handle_discriminator(validator, oneOf, instance, schema)


def allOf(validator, allOf, instance, schema):
    if 'discriminator' not in schema:
        yield from _allOf(validator, allOf, instance, schema)
    else:
        yield from handle_discriminator(validator, allOf, instance, schema)


def type(validator, data_type, instance, schema):
    if instance is None:
        return

    if not validator.is_type(instance, data_type):
        yield ValidationError("%r is not of type %s" % (instance, data_type))


def format(validator, format, instance, schema):
    if instance is None:
        return

    if validator.format_checker is not None:
        try:
            validator.format_checker.check(instance, format)
        except FormatError as error:
            yield ValidationError(str(error), cause=error.cause)


def items(validator, items, instance, schema):
    if not validator.is_type(instance, "array"):
        return

    for index, item in enumerate(instance):
        for error in validator.descend(item, items, path=index):
            yield error


def nullable(validator, is_nullable, instance, schema):
    if instance is None and not is_nullable:
        yield ValidationError("None for not nullable")


def required(validator, required, instance, schema):
    if not validator.is_type(instance, "object"):
        return
    for property in required:
        if property not in instance:
            prop_schema = schema.get('properties', {}).get(property)
            if prop_schema:
                read_only = prop_schema.get('readOnly', False)
                write_only = prop_schema.get('writeOnly', False)
                if (
                        validator.write and read_only or
                        validator.read and write_only):
                    continue
            yield ValidationError("%r is a required property" % property)


def additionalProperties(validator, aP, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    extras = set(find_additional_properties(instance, schema))

    if not extras:
        return

    if validator.is_type(aP, "object"):
        for extra in extras:
            for error in validator.descend(instance[extra], aP, path=extra):
                yield error
    elif validator.is_type(aP, "boolean"):
        if not aP:
            error = "Additional properties are not allowed (%s %s unexpected)"
            yield ValidationError(error % extras_msg(extras))


def readOnly(validator, ro, instance, schema):
    if not validator.write or not ro:
        return

    yield ValidationError(
        "Tried to write read-only property with %s" % (instance))


def writeOnly(validator, wo, instance, schema):
    if not validator.read or not wo:
        return

    yield ValidationError(
        "Tried to read write-only property with %s" % (instance))


def not_implemented(validator, value, instance, schema):
    pass
