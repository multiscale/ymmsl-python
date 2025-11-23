from typing import Callable, cast, Dict, Type, TypeVar

from ymmsl.conversion.convert_v0_1_to_v0_2 import convert_v0_1_to_v0_2
from ymmsl.document import Document
import ymmsl.v0_1 as v0_1
import ymmsl.v0_2 as v0_2


class DowngradeError(RuntimeError):
    pass


_config_types = {v0_1.PartialConfiguration, v0_1.Configuration, v0_2.Configuration}


_converters: Dict[Type[Document], Callable] = {
        v0_1.PartialConfiguration: convert_v0_1_to_v0_2,
        v0_1.Configuration: convert_v0_1_to_v0_2}


T = TypeVar('T', bound=Document)


def convert_to(to_type: Type[T], document: Document) -> T:
    """Convert a ymmsl document to a newer version, if needed.

    This takes a desired configuration type and a document, and returns the document
    converted to the given type. Only upgrades are possible, e.g. v0_1.Configuration to
    v0_2.Configuration, version downgrading is not supported.

    Currently supported values for `to_type` are `ymmsl.v0_1.PartialConfiguration`
    and `ymmsl.v0_2.Configuration`. Only the final one makes sense at the moment,
    there's no point in converting from v0.1 to v0.1.

    Note that this function cannot convert from a `v0_1.PartialConfiguration` to a
    `v0_1.Configuration`. See :meth:`ymmsl.v0_1.PartialConfiguration.as_configuration`
    for that.

    Args:
        to_type: The type to convert to
        document: A ymmsl document to convert, of version lower or equal to the given
                one.

    Returns:
        A new ymmsl document of the given type.

    Raises:
        ValueError: If the desired type is not a supported one
        TypeError: If the document is not a ymmsl.v0_1.PartialConfiguration or
                ymmsl.v0_2.Configuration.
        DowngradeError: If the given document is of a newer version than the one given.
    """
    cur_type = type(document)

    if cur_type not in _config_types:
        raise TypeError(f'Unsupported document type {cur_type}')

    if to_type not in _config_types:
        raise ValueError(f'Unsupported to_type {to_type}')

    while cur_type != to_type:
        if cur_type not in _converters:
            raise DowngradeError(
                'The requested version is not supported. Are you trying to downgrade?')

        document = _converters[cur_type](document)
        cur_type = type(document)

    return cast(T, document)
