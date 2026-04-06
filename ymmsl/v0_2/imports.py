from enum import Enum
from pathlib import Path
from typing import cast, Tuple

import yatiml

from ymmsl.v0_2.identity import Identifier, Reference


class ImportKind(Enum):
    """Describes the kind of object to import.

    Currently only IMPLEMENTATION is supported, which is used to import either a program
    or a model. In the future other things will be importable as well.
    """
    IMPLEMENTATION = 1

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.is_scalar(str):
            val = cast(str, node.get_value())
            node.set_value(val.upper())

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        val = node.get_value()
        if isinstance(val, str):
            node.set_value(val.lower())


class ImportStatement:
    """Represents a yMMSL import statement.

    These are of the form

    from <a.b.c> import <kind> <name>

    where a.b.c is the import path, corresponding to a relative filesystem path of
    a/b/c.ymmsl, kind is 'implementation', and name is the name of a model or program.
    Once imported, that model or program can then be referred to by its name in places
    where an implementation is required.

    Attributes:
        module: a.b.c module to import from
        kind: Kind of object to import, currently always 'implementation'
        name: Name of the object to import from it
    """
    def __init__(self, module: str, kind: str, name: str) -> None:
        """Create an ImportStatement

        Args:
            module: Module to import from, of the form a.b.c
            kind: Kind of object to import
            name: Name of the object to import
        """
        path_parts = module.split('.')
        for path_part in path_parts:
            Identifier(path_part)

        self.module = Reference(module)

        try:
            self.kind = ImportKind[kind.upper()]
        except KeyError:
            raise ValueError(
                    f'{kind} is not a valid kind of object to import. Try'
                    ' "implementation" instead to import a program or a model.')

        self.name = Identifier(name)

    def module_path(self) -> Path:
        """Return a relative path of the file to import from.

        This returns a path a/b/c.ymmsl for module a.b.c.
        """
        return Path('/'.join(map(str, self.module)) + '.ymmsl')

    def full_name(self) -> Reference:
        """Return the full name of the imported object.

        This returns a reference a.b.c.p for a statement import p from a.b.c.
        """
        return self.module + self.name

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_scalar(str)

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        text = str(node.get_value())
        module, kind, name = cls._parse_string_representation(text)

        node.make_mapping()
        node.set_attribute('module', module)
        node.set_attribute('kind', kind)
        node.set_attribute('name', name)

    @classmethod
    def _yatiml_sweeten(self, node: yatiml.Node) -> None:
        module = node.get_attribute('module').get_value()
        kind = node.get_attribute('kind').get_value()
        name = node.get_attribute('name').get_value()
        node.set_value(f'from {module} import {kind} {name}')

    @classmethod
    def _parse_string_representation(cls, text: str) -> Tuple[str, str, str]:
        help_text = 'Import statements should look like "from a.b.c import <kind> d"'

        parts = text.split()

        if len(parts) > 0 and parts[0] != 'from':
            raise RuntimeError(
                    f'Import statement "{text}" does not start with "from".\n' +
                    help_text)

        if len(parts) > 1:
            module = parts[1]

        if len(parts) > 2 and parts[2] != 'import':
            raise RuntimeError(
                    f'Import statement "{text}" does not have "import" part.\n' +
                    help_text)

        if len(parts) > 3:
            kind = parts[3]
        else:
            raise RuntimeError(
                    f'Import statement "{text}" does not specify which kind of thing'
                    ' to import.\n' + help_text)

        if len(parts) > 4:
            name = parts[4]
        else:
            raise RuntimeError(
                    f'Import statement "{text}" does not specify the name of the thing'
                    ' to import.\n' + help_text)

        if len(parts) > 5:
            raise RuntimeError(
                    f'Extra text found at end of import statement "{text}".\n' +
                    help_text)

        return module, kind, name
