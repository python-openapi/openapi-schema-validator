from typing import Any
from typing import Iterator
from typing import Mapping
from typing import cast

from jsonschema._keywords import allOf as _allOf
from jsonschema._keywords import anyOf as _anyOf
from jsonschema._keywords import oneOf as _oneOf
from jsonschema._utils import extras_msg
from jsonschema._utils import find_additional_properties
from jsonschema.exceptions import FormatError
from jsonschema.exceptions import ValidationError
from jsonschema.exceptions import _WrappedReferencingError


def handle_discriminator(
    validator: Any, _: Any, instance: Any, schema: Mapping[str, Any]
) -> Iterator[ValidationError]:
    """
    Handle presence of discriminator in anyOf, oneOf and allOf.
    The behaviour is the same in all 3 cases because at most 1 schema will match.
    """
    discriminator = schema["discriminator"]
    prop_name = discriminator["propertyName"]

    if not validator.is_type(instance, "object"):
        yield ValidationError(
            f"{instance!r} is not of type 'object'", context=[]
        )
        return

    prop_value = instance.get(prop_name)
    if not prop_value:
        # instance is missing $propertyName
        yield ValidationError(
            f"{instance!r} does not contain discriminating property {prop_name!r}",
            context=[],
        )
        return

    # Use explicit mapping if available, otherwise try implicit value
    ref = (
        discriminator.get("mapping", {}).get(prop_value)
        or f"#/components/schemas/{prop_value}"
    )

    if not isinstance(ref, str):
        # this is a schema error
        yield ValidationError(
            f"{instance!r} mapped value for {prop_value!r} should be a string, was {ref!r}",
            context=[],
        )
        return

    try:
        validator._validate_reference(ref=ref, instance=instance)
    except _WrappedReferencingError:
        yield ValidationError(
            f"{instance!r} reference {ref!r} could not be resolved",
            context=[],
        )
        return

    yield from validator.descend(instance, {"$ref": ref})


def anyOf(
    validator: Any,
    anyOf: list[Mapping[str, Any]],
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if "discriminator" not in schema:
        yield from cast(
            Iterator[ValidationError],
            _anyOf(validator, anyOf, instance, schema),
        )
    else:
        yield from handle_discriminator(validator, anyOf, instance, schema)


def oneOf(
    validator: Any,
    oneOf: list[Mapping[str, Any]],
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if "discriminator" not in schema:
        yield from cast(
            Iterator[ValidationError],
            _oneOf(validator, oneOf, instance, schema),
        )
    else:
        yield from handle_discriminator(validator, oneOf, instance, schema)


def allOf(
    validator: Any,
    allOf: list[Mapping[str, Any]],
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if "discriminator" not in schema:
        yield from cast(
            Iterator[ValidationError],
            _allOf(validator, allOf, instance, schema),
        )
    else:
        yield from handle_discriminator(validator, allOf, instance, schema)


def type(
    validator: Any,
    data_type: str,
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if instance is None:
        # nullable implementation based on OAS 3.0.3
        # * nullable is only meaningful if its value is true
        # * nullable: true is only meaningful in combination with a type
        #   assertion specified in the same Schema Object.
        # * nullable: true operates within a single Schema Object
        if schema.get("nullable") is True:
            return
        yield ValidationError("None for not nullable")

    if not validator.is_type(instance, data_type):
        data_repr = repr(data_type)
        yield ValidationError(f"{instance!r} is not of type {data_repr}")


def format(
    validator: Any,
    format: str,
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if instance is None:
        return

    if validator.format_checker is not None:
        try:
            validator.format_checker.check(instance, format)
        except FormatError as error:
            yield ValidationError(str(error), cause=error.cause)


def items(
    validator: Any,
    items: Mapping[str, Any],
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if not validator.is_type(instance, "array"):
        return

    for index, item in enumerate(instance):
        yield from validator.descend(item, items, path=index)


def required(
    validator: Any,
    required: list[str],
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if not validator.is_type(instance, "object"):
        return
    for property in required:
        if property not in instance:
            prop_schema = schema.get("properties", {}).get(property)
            if prop_schema:
                read_only = prop_schema.get("readOnly", False)
                write_only = prop_schema.get("writeOnly", False)
                if (
                    getattr(validator, "write", True)
                    and read_only
                    or getattr(validator, "read", True)
                    and write_only
                ):
                    continue
            yield ValidationError(f"{property!r} is a required property")


def read_required(
    validator: Any,
    required: list[str],
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if not validator.is_type(instance, "object"):
        return
    for property in required:
        if property not in instance:
            prop_schema = schema.get("properties", {}).get(property)
            if prop_schema:
                write_only = prop_schema.get("writeOnly", False)
                if getattr(validator, "read", True) and write_only:
                    continue
            yield ValidationError(f"{property!r} is a required property")


def write_required(
    validator: Any,
    required: list[str],
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if not validator.is_type(instance, "object"):
        return
    for property in required:
        if property not in instance:
            prop_schema = schema.get("properties", {}).get(property)
            if prop_schema:
                read_only = prop_schema.get("readOnly", False)
                if read_only:
                    continue
            yield ValidationError(f"{property!r} is a required property")


def additionalProperties(
    validator: Any,
    aP: Any,
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
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


def write_readOnly(
    validator: Any,
    ro: bool,
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if not ro:
        return
    yield ValidationError(f"Tried to write read-only property with {instance}")


def read_writeOnly(
    validator: Any,
    wo: bool,
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    if not wo:
        return
    yield ValidationError(f"Tried to read write-only property with {instance}")


def not_implemented(
    validator: Any,
    value: Any,
    instance: Any,
    schema: Mapping[str, Any],
) -> Iterator[ValidationError]:
    yield from ()
