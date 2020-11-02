import copy
import datetime
import boto3

import lobotomy as lbm

data = {
    'clients': {
        'sts': {'get_caller_identity': {'UserId': 'SOMEUSERIDSTRING'}},
        's3': {
            'get_object': {
                'Body': 'hello world.',
                'LastModified': '2020-01-01T12:23:34Z',
            },
        },
    }
}


def test_data():
    """Should execute as expected given the data object."""
    lobotomy = lbm.Lobotomy(copy.deepcopy(data))
    session = lobotomy()

    client = session.client('sts')
    assert client.get_caller_identity()['UserId'] == 'SOMEUSERIDSTRING'


@lbm.Patch(copy.deepcopy(data))
def test_data_patched(*args):
    """Should execute as expected given the data object."""
    session = boto3.Session()
    client = session.client('sts')
    assert client.get_caller_identity()['UserId'] == 'SOMEUSERIDSTRING'


@lbm.Patch(copy.deepcopy(data))
def test_data_streaming_body(*args):
    """Should execute as expected given the data object."""
    session = boto3.Session()
    client = session.client('s3')

    response = client.get_object(Key='foo', Bucket='bar')
    assert response['Body'].read() == b'hello world.'


@lbm.Patch(copy.deepcopy(data))
def test_data_timestamp_casting(*args):
    """Should cast the last modified value to a timestamp."""
    session = boto3.Session()
    client = session.client('s3')

    response = client.get_object(Key='foo', Bucket='bar')
    last_modified = datetime.datetime(
        2020, 1, 1, 12, 23, 34, tzinfo=datetime.timezone.utc,
    )
    assert response['LastModified'] == last_modified
