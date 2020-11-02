import pathlib
from unittest.mock import MagicMock
from unittest.mock import patch

from pytest import mark

import lobotomy


def test_cli_add():
    """Should execute the command as expected."""
    result = lobotomy.run_cli(['add', 'lambda.create_function', '-'])
    assert result.code == 'ECHOED'


@mark.parametrize('file_format', ['yaml', 'toml', 'json'])
def test_cli_add_formats(file_format: str):
    """Should execute the command as expected."""
    result = lobotomy.run_cli([
        'add', 'sts.get_caller_identity', '-',
        f'--format={file_format}',
    ])
    assert result.code == 'ECHOED'


@mark.parametrize('file_format', ['yaml', 'toml', 'json'])
@patch('lobotomy._fio.write')
@patch('lobotomy._fio.read')
def test_cli_add_path(
        fio_read: MagicMock,
        fio_write: MagicMock,
        file_format: str,
):
    """Should write updated call to the config file."""
    fio_read.return_value = {}
    name = f'example.{file_format}'
    fake_path = pathlib.Path(__file__).parent.joinpath(name).absolute()
    result = lobotomy.run_cli([
        'add', 'sts.get_caller_identity', str(fake_path),
    ])
    assert result.code == 'ADDED'
    fio_read.assert_called_once()
    fio_write.assert_called_once()


@patch('lobotomy._fio.write')
@patch('lobotomy._fio.read')
def test_cli_add_append(fio_read: MagicMock, fio_write: MagicMock):
    """Should write updated call to the config file."""
    fio_read.return_value = {
        'clients': {
            'sts': {
                'get_caller_identity': {'UserId': 'foo'}
            }
        }
    }
    fake_path = pathlib.Path(__file__).parent.joinpath('foo.yaml').absolute()
    result = lobotomy.run_cli([
        'add', 'sts.get_caller_identity', str(fake_path),
    ])
    assert result.code == 'ADDED'
    fio_read.assert_called_once()
    fio_write.assert_called_once()

    configs = fio_write.call_args.args[1]
    assert isinstance(configs['clients']['sts']['get_caller_identity'], list)
    assert len(configs['clients']['sts']['get_caller_identity']) == 2


@patch('lobotomy._fio.write')
@patch('lobotomy._fio.read')
def test_cli_add_append_again(fio_read: MagicMock, fio_write: MagicMock):
    """Should write updated call to the config file."""
    fio_read.return_value = {
        'clients': {
            'sts': {
                'get_caller_identity': [{'UserId': 'foo'}, {'UserId': 'foo'}],
            }
        }
    }
    fake_path = pathlib.Path(__file__).parent.joinpath('bar.json').absolute()
    result = lobotomy.run_cli([
        'add', 'sts.get_caller_identity', str(fake_path),
    ])
    assert result.code == 'ADDED'
    fio_read.assert_called_once()
    fio_write.assert_called_once()

    configs = fio_write.call_args.args[1]
    assert isinstance(configs['clients']['sts']['get_caller_identity'], list)
    assert len(configs['clients']['sts']['get_caller_identity']) == 3
