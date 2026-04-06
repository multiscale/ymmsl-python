from ymmsl import load_as
from ymmsl.v0_2 import Configuration

from pathlib import Path


def test_load_examples() -> None:
    doc_dir = Path(__file__).parents[2] / 'docs'

    for example_file in doc_dir.glob('*.ymmsl'):
        # Just check that there are no errors
        load_as(Configuration, example_file)
