import click
import os
from shutil import copyfile
from typing import Optional

from ymmsl.conversion.converter import DowngradeError
from ymmsl.document import Document
from ymmsl.io import load_as, save
import ymmsl.v0_1 as v0_1
import ymmsl.v0_2 as v0_2


_version_tag_to_type = {
        'v0.1': v0_1.PartialConfiguration,
        'v0.2': v0_2.Configuration,
        }


@click.group()
def ymmsl() -> None:
    """yMMSL command line interface

    This command provides various functions for handling ymmsl files.

    Use ymmsl <command> --help for help with individual commands.
    """
    pass


@ymmsl.command(short_help='Convert a yMMSL file to a newer version')
@click.argument(
        'input_file', default='-', type=click.Path(
            exists=True, file_okay=True, dir_okay=False, readable=True,
            resolve_path=False, allow_dash=True))
@click.argument(
        'output_file', required=False, type=click.Path(
            file_okay=True, dir_okay=True, writable=True, resolve_path=False,
            allow_dash=True))
@click.option(
        '-t', '--to', default='v0.2', help='Version to convert to, e.g. "v0.2".')
def convert(
        input_file: str, output_file: Optional[str], to: str) -> None:
    """Convert a yMMSL file to a later version

    When upgrading in place, and/or if an output file is specified and it exists, a
    backup of the original file will be created with an additional .bak extension,
    unless such a file already exists in which case it will be left unchanged.

    If no input or output file is specified, then this will read from stdin and write to
    stdout. To explicitly specify reading from stdin or writing to stdout, use - for the
    file name.

    Examples:

        Converting a file to the newest supported version:

            ymmsl convert model.ymmsl model_new.ymmsl

        Upgrading to an explicitly specified version:

            ymmsl convert --to v0.2 model.ymmsl model_new.ymmsl

        Converting in place (will create model.ymmsl.bak with the original content):

            ymmsl convert model.ymmsl

        Converting all ymmsl files in subdir/:

            find subdir -name '*.ymmsl' -exec ymmsl convert \\{\\} \\;

        Using standard input and standard output (will not back up model_new.ymmsl!):

            cat model.ymmsl | ymmsl convert >model_new.ymmsl

        Reading from stdin and writing to a file:

            cat model.ymmsl | ymmsl convert - model_new.ymmsl

        Reading from a file and writing to stdout (will not back up model_new.ymmsl!):

            ymmsl convert model.ymmsl - >model_new.ymmsl

    Note that converting in place using redirects, i.e.

        ymmsl convert model.ymmsl - >model.ymmsl

    won't work, because the shell will open the file to do the redirect, empty it, and
    then run ymmsl convert, which then fails because the input is empty.
    """
    if output_file is None:
        output_file = input_file

    if to not in _version_tag_to_type:
        click.echo(
                f'Invalid version {to} specified. Supported versions are v0.1 and v0.2',
                err=True)
        exit(1)

    try:
        with click.open_file(input_file) as input_stream:
            document: Document = load_as(_version_tag_to_type[to], input_stream)
    except DowngradeError:
        click.echo()
        click.echo(
                f'It seems that {input_file} is of a newer version than the target'
                f' version {to}.')
        click.echo()
        click.echo(
                'This tool can only upgrade files, not downgrade them, so that does'
                ' not work.')
        exit(1)

    if output_file != '-' and os.path.exists(output_file):
        backup_file = output_file + '.bak'
        if not os.path.exists(backup_file):
            copyfile(output_file, output_file + '.bak')

    with click.open_file(output_file, 'w') as output_stream:
        save(document, output_stream)
