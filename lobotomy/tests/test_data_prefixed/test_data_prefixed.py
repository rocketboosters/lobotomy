import pathlib

import boto3

import lobotomy as lbm

path = pathlib.Path(__file__).parent.joinpath('example.yaml').absolute()


@lbm.Patch(path=path, prefix='lobotomy')
def test_data_string_prefix(*args):
    """Should execute as expected with a string prefix."""
    session = boto3.Session()
    client = session.client('sts')
    assert client.get_caller_identity()['UserId'] == 'SOMEUSERIDSTRING'


@lbm.Patch(path=path, prefix=['lobotomy', 'foo'])
def test_data_list_prefix(*args):
    """Should execute as expected given list prefix."""
    session = boto3.Session()
    client = session.client('sts')
    assert client.get_caller_identity()['UserId'] == 'OTHERIDSTRING'
