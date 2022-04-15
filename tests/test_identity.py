from ymmsl import Identifier, Reference

import pytest
import yatiml


def test_create_identifier() -> None:
    part = Identifier('testing')
    assert str(part) == 'testing'

    part = Identifier('CapiTaLs')
    assert str(part) == 'CapiTaLs'

    part = Identifier('under_score')
    assert str(part) == 'under_score'

    part = Identifier('_underscore')
    assert str(part) == '_underscore'

    part = Identifier('digits123')
    assert str(part) == 'digits123'

    with pytest.raises(ValueError):
        Identifier('1initialdigit')

    with pytest.raises(ValueError):
        Identifier('test.period')

    with pytest.raises(ValueError):
        Identifier('test-hyphen')

    with pytest.raises(ValueError):
        Identifier('test space')

    with pytest.raises(ValueError):
        Identifier('test/slash')


def test_compare_identifier() -> None:
    assert Identifier('test') == Identifier('test')
    assert Identifier('test1') != Identifier('test2')

    assert Identifier('test') == 'test'
    assert 'test' == Identifier('test')     # pylint: disable=C0122
    assert Identifier('test') != 'test2'
    assert 'test2' != Identifier('test')    # pylint: disable=C0122


def test_identifier_dict_key() -> None:
    test_dict = {Identifier('test'): 1}
    assert test_dict[Identifier('test')] == 1


def test_create_reference() -> None:
    test_ref = Reference('_testing')
    assert str(test_ref) == '_testing'
    assert len(test_ref) == 1
    assert isinstance(test_ref[0], Identifier)
    assert str(test_ref[0]) == '_testing'

    with pytest.raises(ValueError):
        Reference('1test')

    test_ref = Reference('test.testing')
    assert len(test_ref) == 2
    assert isinstance(test_ref[0], Identifier)
    assert str(test_ref[0]) == 'test'
    assert isinstance(test_ref[1], Identifier)
    assert str(test_ref[1]) == 'testing'
    assert str(test_ref) == 'test.testing'

    test_ref = Reference('test[12]')
    assert len(test_ref) == 2
    assert isinstance(test_ref[0], Identifier)
    assert str(test_ref[0]) == 'test'
    assert isinstance(test_ref[1], int)
    assert test_ref[1] == 12
    assert str(test_ref) == 'test[12]'

    test_ref = Reference('test[12].testing.ok.index[3][5]')
    assert len(test_ref) == 7
    assert isinstance(test_ref[0], Identifier)
    assert str(test_ref[0]) == 'test'
    assert isinstance(test_ref[1], int)
    assert test_ref[1] == 12
    assert isinstance(test_ref[2], Identifier)
    assert str(test_ref[2]) == 'testing'
    assert isinstance(test_ref[3], Identifier)
    assert str(test_ref[3]) == 'ok'
    assert isinstance(test_ref[4], Identifier)
    assert str(test_ref[4]) == 'index'
    assert isinstance(test_ref[5], int)
    assert test_ref[5] == 3
    assert isinstance(test_ref[6], int)
    assert test_ref[6] == 5
    assert str(test_ref) == 'test[12].testing.ok.index[3][5]'

    with pytest.raises(ValueError):
        Reference([4])

    with pytest.raises(ValueError):
        Reference([3, Identifier('test')])

    with pytest.raises(ValueError):
        Reference('ua",.u8[')

    with pytest.raises(ValueError):
        Reference('test[4')

    with pytest.raises(ValueError):
        Reference('test4]')

    with pytest.raises(ValueError):
        Reference('test[_t]')

    with pytest.raises(ValueError):
        Reference('testing_{3}')

    with pytest.raises(ValueError):
        Reference('test.(x)')

    with pytest.raises(ValueError):
        Reference('[3]test')

    with pytest.raises(ValueError):
        Reference('[4].test')


def test_reference_slicing() -> None:
    test_ref = Reference('test[12].testing.ok.index[3][5]')

    assert test_ref[0] == 'test'
    assert test_ref[1] == 12
    assert test_ref[3] == 'ok'
    assert test_ref[:3] == 'test[12].testing'
    assert test_ref[2:] == 'testing.ok.index[3][5]'

    with pytest.raises(RuntimeError):
        test_ref[0] = 'test2'

    with pytest.raises(ValueError):
        test_ref[1:]    # pylint: disable=pointless-statement


def test_reference_dict_key() -> None:
    test_dict = {Reference('test[4]'): 1}
    assert test_dict[Reference('test[4]')] == 1


def test_reference_equivalence() -> None:
    assert Reference('test.test[3]') == Reference('test.test[3]')
    assert Reference('test.test[3]') != Reference('test1.test[3]')

    assert Reference('test.test[3]') == 'test.test[3]'
    assert Reference('test.test[3]') != 'test1.test[3]'
    assert 'test.test[3]' == Reference('test.test[3]')  # pylint: disable=C0122
    assert 'test1.test[3]' != Reference(
            'test.test[3]')     # pylint: disable=C0122


def test_reference_concatenation() -> None:
    assert Reference('test') + Reference('test2') == 'test.test2'
    assert Reference('test') + Identifier('test2') == 'test.test2'
    assert Reference('test') + 5 == 'test[5]'
    assert Reference('test') + [Identifier('test2'), 5] == 'test.test2[5]'

    assert Reference('test[5]') + Reference('test2[3]') == 'test[5].test2[3]'
    assert Reference('test[5]') + Identifier('test2') == 'test[5].test2'
    assert Reference('test[5]') + 3 == 'test[5][3]'
    assert (Reference('test[5]') + [3, Identifier('test2')] ==
            'test[5][3].test2')


def test_reference_without_trailing_ints() -> None:
    Ref = Reference
    assert Ref('a.b.c[1][2]').without_trailing_ints() == Ref('a.b.c')
    assert Ref('a[1].b.c').without_trailing_ints() == Ref('a[1].b.c')
    assert Ref('a.b.c').without_trailing_ints() == Ref('a.b.c')
    assert Ref('a[1].b.c[2]').without_trailing_ints() == Ref('a[1].b.c')


def test_reference_io() -> None:
    load_reference = yatiml.load_function(Reference, Identifier)

    text = 'test[12]'
    doc = load_reference(text)
    assert str(doc[0]) == 'test'
    assert doc[1] == 12

    dump_reference = yatiml.dumps_function(Identifier, Reference)

    doc = Reference('test[12].testing.ok.index[3][5]')
    text = dump_reference(doc)
    assert text == 'test[12].testing.ok.index[3][5]\n...\n'
