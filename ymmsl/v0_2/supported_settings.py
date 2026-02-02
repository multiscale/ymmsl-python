from collections.abc import MutableMapping
from enum import Enum
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple, Union, cast

import yaml
import yatiml

from ymmsl.v0_2.identity import Identifier


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
        """
        In YAML, [int] and such are arrays of string, so the standard recognition of
        an enum fails because it wants a string. We can simply skip it though, since
        there are no places where either a SettingType or something else can be
        given.
        """
        pass

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        def to_str(node: yatiml.Node) -> str:
            """Convert a sequence node to a string

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
            """Convert a type name to a sequence node

            This takes a type name like STR or LIST_FLOAT and converts it to a yaml
            node that renders to the corresponding value str or [float]. Recursively
            removes LIST_ and adds a yaml.SequenceNode that's set to render to []
            rather than a multiline sequence with dashes, and finally inserts the
            lowercased remaining part.
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


class SupportedSetting:
    """Supported setting for an implementation.

    Attributes:

    name: Name of the setting
    typ: Type of the setting
    description: Description of what this sets, allowed values, etc.
    """
    def __init__(
            self, name: Union[str, Identifier], typ: Union[str, SettingType],
            description: str) -> None:
        """Create a SupportedSetting.

        Args:
            name: Name of the setting, must be a valid Identifier
            typ: Type of the setting's value
            description: Description of the setting
        """
        if isinstance(name, str):
            name = Identifier(name)
        self.name = name

        if isinstance(typ, str):
            typ = SettingType(typ)
        self.typ = typ

        self.description = description

    def __eq__(self, other: Any) -> bool:
        """Returns whether the objects are equal, by value."""
        if not isinstance(other, SupportedSetting):
            return NotImplemented
        return (
                self.name == other.name and self.typ == other.typ and
                self.description == other.description)

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        """Override recognition

        In YAML, [int] and such are arrays of string, so the standard recognition of
        an enum fails because it wants a string. We can mostly skip it though, since
        there are no places where either a SupportedSetting or something else can be
        given.
        """
        node.require_mapping()

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        """Rename to avoid the Python keyword"""
        if node.is_mapping():
            if node.has_attribute('type'):
                node.rename_attribute('type', 'typ')

    def _yatiml_init(
            self, name: Identifier, typ: Optional[SettingType] = None,
            description: Optional[Union[str, List[str], List[List[str]]]] = None
            ) -> None:
        """
        Yeah, sorry. I wanted nice syntax for the users and couldn't find a cleaner
        way.

        This supports the following combinations:

        - description is a list and type is None, which is produced by
              SupportedSettings._yatiml_savorize if the user types

            setting_name: [int]

        - description is a string and type is None, for YAML that looks like

           setting_name: str

          or

           setting_name: str With a description

          In this case we split the description into a type and a description, if any.

        - description is None and type is not None, for YAML that looks like

           setting_name:
             type: str

        Unofficially, these will also work:

           setting_name:
             description: [[float]]

        and

           setting_name:
             description: '[float] With a description'

        Note that this final one has to be quoted, because to YAML the opening square
        bracket makes this a sequence, and those aren't allowed to have anything after
        the corresponding closing square bracket.
        """
        def list_to_setting_type(
                description: Union[List[str], List[List[str]]]) -> SettingType:
            """convert ['something'] or [['something']] to a SettingType"""
            if len(description) == 0:
                raise ValueError(f'Invalid setting type [] for "{name}"')

            if isinstance(description[0], str):
                return SettingType(f'[{description[0]}]')
            else:
                if len(description[0]) == 0:
                    raise ValueError(f'Invalid setting type [[]] for "{name}"')
                return SettingType(f'[[{description[0][0]}]]')

        if isinstance(description, list):
            # description contains only a type, a funny one
            if typ is not None:
                raise ValueError(
                        f'The description of "{name}" gives a type, rather than a'
                        ' description')

            typ = list_to_setting_type(description)
            description = ''

        elif isinstance(description, str):
            if typ is None:
                # description must contain a type, and perhaps a description
                if (
                        description is None or
                        isinstance(description, str) and description.strip() == ''):
                    raise ValueError(
                            f'Neither a type nor a description was given for "{name}"')

                pieces = description.split(maxsplit=1)
                try:
                    typ = SettingType(pieces[0])
                    description = pieces[1] if len(pieces) > 1 else ''
                except KeyError:
                    raise ValueError(
                            'If type is not given, then description must start with'
                            f' the setting\'s type, which is not the case for "{name}"')
            # else typ is the type and description the description, so nothing to do
        else:
            # description is None, which is okay as long as we have a type
            if typ is None:
                raise ValueError(
                        f'Neither a type nor a description was given for "{name}"')
            description = ''

        SupportedSetting.__init__(self, name, typ, description)

    def _yatiml_attributes(self) -> Dict:
        """Create output data for YAML serialisation."""
        if self.description.strip() == '':
            # Put type into the description field so that
            # SupportedSettings._yatiml_sweeten maps this to name: type
            return {
                    'name': self.name,
                    'description': self.typ}

        # If the description is short enough, put it on a single line too
        short = len(self.name) + len(self.description) < 72
        if short and '\n' not in self.description:
            desc = self.typ.value
            if self.description:
                desc += f' {self.description}'
            return {
                    'name': self.name,
                    'description': desc}

        # For long or multiline descriptions, use type: and description: subkeys
        return {
                'name': self.name,
                'type': self.typ,
                'description': self.description}

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        """If the description is multiple lines, format it block style"""
        desc_node = node.get_attribute('description')
        if desc_node.is_scalar(str):
            if '\n' in cast(str, desc_node.get_value()):
                cast(yaml.ScalarNode, desc_node.yaml_node).style = '|'


class SupportedSettings(MutableMapping):
    """Supported settings for an Implementation.

    This allows describing which settings are supported, by name and type.

    In YAML, this object is represented by a dict/mapping:

    .. code-block:: yaml

        mode: str Which mode to use when calculating
        accuracy:
          type: str
          description: |
            Accuracy of calculations

            Possible values:

            - low: Not very accurate, but fast. Good for testing.
            - medium: Slower and more accurate. Good for most use.
            - hight: Slowest, but very accurate. Good for reference runs.
        D: '[[float]] Diffusion kernel'
        D2: [[float]]


    Note the use of a text block to enable a longer description, and note that
    description of D needs to be quoted to avoid it being invalid YAML. If there is only
    the type, then the quotes can be omitted.
    """
    def __init__(
            self,
            supported_settings: Union[
                Mapping[str, str], List[SupportedSetting], None] = None
            ) -> None:
        """Create a SupportedSettings object.

        If given, the argument must be a dictionary mapping strings to strings as in the
        YAML representation above, or a list of SupportedSetting objects.

        This will make a deep copy of the argument.

        Args:
            supported_settings: Description of the supported settings.
        """
        self._store: Dict[Identifier, SupportedSetting] = dict()

        if supported_settings is not None:
            if isinstance(supported_settings, list):
                for setting in supported_settings:
                    self._store[setting.name] = setting
            else:
                for name, arg in supported_settings.items():
                    name_ref = Identifier(name)
                    self._store[name_ref] = self._to_supported_setting(name_ref, arg)

    def __eq__(self, other: Any) -> bool:
        """Returns whether keys, values and descriptions are identical.

        The comparison ignores the order of the supported settings.
        """
        if not isinstance(other, SupportedSettings):
            return NotImplemented
        return self._store == other._store

    def __str__(self) -> str:
        """Represent as a string, omitting the descriptions."""
        return ', '.join([f'{s.name}: {s.typ}' for s in self._store.values()])

    def __getitem__(self, key: Union[str, Identifier]) -> SupportedSetting:
        """Returns a supported setting, implements supported_settings[name]."""
        if isinstance(key, str):
            key = Identifier(key)
        return self._store[key]

    def __setitem__(
            self, key: Union[str, Identifier], value: Union[str, SupportedSetting]
            ) -> None:
        """Sets a value, implements supported_settings[name] = typ, desc."""
        if isinstance(key, str):
            key = Identifier(key)
        if isinstance(value, str):
            value = self._to_supported_setting(key, value)
        self._store[key] = value

    def __delitem__(self, key: Union[str, Identifier]) -> None:
        """Deletes a value, implements del(supported_settings[name])."""
        if isinstance(key, str):
            key = Identifier(key)
        del self._store[key]

    def __iter__(self) -> Iterator[Tuple[Identifier, SupportedSetting]]:
        """Iterate through the settings' key, supported_setting pairs."""
        for key, value in self._store.items():
            yield key, value

    def __len__(self) -> int:
        """Returns the number of settings."""
        return len(self._store)

    def copy(self) -> 'SupportedSettings':
        """Makes a shallow copy of these supported settings and returns it."""
        new_settings = SupportedSettings()
        new_settings._store = self._store.copy()
        return new_settings

    def _to_supported_setting(self, name: Identifier, arg: str) -> SupportedSetting:
        """Parse a string into a SupportedSetting."""
        pieces = arg.split(maxsplit=1)
        if len(pieces) == 0:
            raise RuntimeError(f'Empty description for setting {name}')

        return SupportedSetting(
                name, SettingType(pieces[0]), '' if len(pieces) == 1 else pieces[1])

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        pass

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        # Nest the input inside of a new mapping with a supported_settings key
        sup_set = node.yaml_node
        node.make_mapping()
        node.set_attribute('supported_settings', sup_set)
        # And then convert it to a list of SupportedSetting mappings
        # SupportedSettings can take a type for description, see its _yatiml_init
        node.map_attribute_to_seq('supported_settings', 'name', 'description')

    def _yatiml_init(
            self, supported_settings: Optional[List[SupportedSetting]] = None
            ) -> None:
        # Take that list of supported settings and initialise the object
        SupportedSettings.__init__(self, supported_settings)

    def _yatiml_attributes(self) -> Dict:
        # Put everything into a mapping under the supported_settings key,
        # so that we can use seq_attribute_to_map below.
        return {
                'supported_settings': list(self._store.values())}

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.seq_attribute_to_map('supported_settings', 'name', 'description')
        # use the created map directly again
        node.yaml_node.value = node.yaml_node.value[0][1].value
