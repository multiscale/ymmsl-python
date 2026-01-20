from collections.abc import MutableMapping
from enum import Enum
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple, Union, cast

import yaml
import yatiml

from ymmsl.v0_2.identity import Reference


class SettingType(Enum):
    STR = 'str'
    INT = 'int'
    FLOAT = 'float'
    BOOL = 'bool'
    LIST_INT = '[int]'
    LIST_FLOAT = '[float]'
    LIST_LIST_FLOAT = '[[float]]'

    def __str__(self) -> str:
        return self.value

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        """Skip type checking

        In YAML, [int] and such are arrays of string, so the standard recognition of an
        enum fails because it wants a string.
        """
        pass

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        def to_str(node: yatiml.Node) -> str:
            """Convert the parsed YAML node to the capitalised name of the type.

            If the user types [float], then YAML interprets that as a sequence
            containing a single string 'float'. So we get a sequence here, and convert
            it back to the name of the SettingType by prepending LIST_ for each nested
            sequence.
            """
            if node.is_scalar(str):
                return cast(str, node.get_value()).upper()
            elif node.is_sequence():
                items = node.seq_items()
                if len(items) != 1:
                    raise yatiml.SeasoningError('Invalid setting type')
                return 'LIST_' + to_str(items[0])
            raise yatiml.SeasoningError('Invalid setting type')

        node.set_value(to_str(node))

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        def to_node(typ: str, start_mark: yaml.Mark, end_mark: yaml.Mark) -> yaml.Node:
            """Convert the type name to a yaml Node.

            This takes a type name like STR or LIST_FLOAT and converts it to a yaml node
            that renders to the corresponding value str or [float]. Recursively removes
            LIST_ and adds a yaml.SequenceNode that's set to render to [] rather than a
            multiline sequence with dashes, and finally inserts the lowercased remaining
            part.
            """
            if not typ.startswith('LIST_'):
                return yaml.ScalarNode(
                        'tag:yaml.org,2002:str', typ.lower(), start_mark, end_mark)
            else:
                subnode = to_node(typ[5:], start_mark, end_mark)
                seq = yaml.SequenceNode(
                        'tag:yaml.org,2002:seq', [subnode], start_mark, end_mark)
                seq.flow_style = True
                return seq

        val = cast(str, node.get_value())
        node.yaml_node = to_node(
                val, node.yaml_node.start_mark, node.yaml_node.end_mark)


class SupportedSettings(MutableMapping):
    """Supported settings for an Implementation.

    This allows describing which settings are supported, by name and type.
    """
    def __init__(
            self,
            supported_settings: Optional[Mapping[str, Union[str, SettingType]]] = None
            ) -> None:
        """Create a SupportedSettings object.

        If given, the argument must be a dictionary mapping strings to strings or
        SettingTypes, where the keys are valid References and the values are either
        SettingType objects, or strings describing a valid SettingType by value, e.g.
        'str' or '[float]'.

        This will make a deep copy of the argument.

        Args:
            supported_settings: Description of the supported settings.
        """
        self._store: Dict[Reference, SettingType] = dict()

        if supported_settings is not None:
            for name, typ in supported_settings.items():
                if isinstance(typ, str):
                    typ = SettingType(typ)
                self[name] = typ

    def __eq__(self, other: Any) -> bool:
        """Returns whether keys and values are identical.

        The comparison ignores the order of the supported settings.
        """
        if not isinstance(other, SupportedSettings):
            return NotImplemented
        return self._store == other._store

    def __str__(self) -> str:
        """Represent as a string."""
        return str(self.as_ordered_dict())

    def __getitem__(self, key: Union[str, Reference]) -> SettingType:
        """Returns an item, implements supported_settings[name]."""
        if isinstance(key, str):
            key = Reference(key)
        return self._store[key]

    def __setitem__(
            self, key: Union[str, Reference], value: Union[str, SettingType]) -> None:
        """Sets a value, implements supported_settings[name] = value."""
        if isinstance(key, str):
            key = Reference(key)
        if isinstance(value, str):
            value = SettingType(value)
        self._store[key] = value

    def __delitem__(self, key: Union[str, Reference]) -> None:
        """Deletes a value, implements del(supported_settings[name])."""
        if isinstance(key, str):
            key = Reference(key)
        del self._store[key]

    def __iter__(self) -> Iterator[Tuple[Reference, SettingType]]:
        """Iterate through the settings' key, value pairs."""
        for key, value in self._store.items():
            yield key, value

    def __len__(self) -> int:
        """Returns the number of settings."""
        return len(self._store)

    def ordered_items(self) -> List[Tuple[Reference, SettingType]]:
        """Return supported settings as a list of tuples."""
        result = list()
        for key, value in self._store.items():
            result.append((key, value))
        return result

    def copy(self) -> 'SupportedSettings':
        """Makes a shallow copy of these supported settings and returns it."""
        new_settings = SupportedSettings()
        new_settings._store = self._store.copy()
        return new_settings

    def as_ordered_dict(self) -> Dict[str, str]:
        """Represent as a dictionary of plain built-in types.

        Returns: A dictionary that uses only built-in types, containing
            the supported settings.
        """
        return {str(key): str(value) for key, value in self._store.items()}

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # Skip checking key and value types, because some values or arrays in YAML
        # This is patched up by the SettingType savorization, so it'll work
        node.require_mapping()

    def _yatiml_init(
            self, supported_settings: Optional[Mapping[str, SettingType]] = None
            ) -> None:
        # This overrides __init__ for yatiml, to avoid the ambiguity between str and
        # SettingType.
        SupportedSettings.__init__(self, supported_settings)

    def _yatiml_attributes(self) -> Dict:
        return self._store

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        # wrap the existing mapping into a new mapping with attribute supported_settings
        setting_types = node.yaml_node
        node.make_mapping()
        node.set_attribute('supported_settings', setting_types)
