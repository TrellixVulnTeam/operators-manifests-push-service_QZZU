#
# Copyright (C) 2019 Red Hat, Inc
# see the LICENSE file for license
#

from io import BytesIO

import requests
import pytest

from omps import constants


def test_push_zipfile(
        client, valid_manifests_archive, endpoint_push_zipfile,
        mocked_quay_io, mocked_op_courier_push, auth_header):
    """Test REST API for pushing operators form zipfile"""
    with open(valid_manifests_archive, 'rb') as f:
        data = {
            'file': (f, f.name),
        }
        rv = client.post(
            endpoint_push_zipfile.url_path,
            headers=auth_header,
            data=data,
            content_type='multipart/form-data',
        )

    assert rv.status_code == 200, rv.get_json()
    expected = {
        'organization': endpoint_push_zipfile.org,
        'repo': endpoint_push_zipfile.repo,
        'version': endpoint_push_zipfile.version or constants.DEFAULT_RELEASE_VERSION,
        'extracted_files': ['empty.yml'],
    }
    assert rv.get_json() == expected


@pytest.mark.parametrize('filename', (
    'test.json',  # test invalid extension
    'test.zip',  # test invalid content
))
def test_push_zipfile_invalid_file(
        client, filename, endpoint_push_zipfile,
        mocked_quay_io, auth_header):
    """Test if proper error is returned when no zip file is being attached"""
    data = {
        'file': (BytesIO(b'randombytes'), filename),
    }
    rv = client.post(
        endpoint_push_zipfile.url_path,
        data=data,
        headers=auth_header,
        content_type='multipart/form-data',
    )

    assert rv.status_code == 400, rv.get_json()
    rv_json = rv.get_json()
    assert rv_json['status'] == 400
    assert rv_json['error'] == 'OMPSUploadedFileError'


def test_push_zipfile_no_file(
        client, endpoint_push_zipfile, mocked_quay_io, auth_header):
    """Test if proper error is returned when no file is being attached"""
    rv = client.post(endpoint_push_zipfile.url_path, headers=auth_header)
    assert rv.status_code == 400, rv.get_json()
    rv_json = rv.get_json()
    assert rv_json['status'] == 400
    assert rv_json['error'] == 'OMPSExpectedFileError'


def test_push_zipfile_unauthorized(client, endpoint_push_zipfile):
    """Test if api properly refuses unauthorized requests"""
    rv = client.post(endpoint_push_zipfile.url_path)
    assert rv.status_code == requests.codes.forbidden, rv.get_json()
    rv_json = rv.get_json()
    assert rv_json['status'] == requests.codes.forbidden
    assert rv_json['error'] == 'OMPSAuthorizationHeaderRequired'


def test_push_koji_nvr(client):
    """Test REST API for pushing operators form koji by NVR"""
    rv = client.post('/v1/organization-X/repo-Y/koji/nvr-Z')
    assert rv.status_code == 200
    expected = {
        'organization': 'organization-X',
        'repo': 'repo-Y',
        'nvr': 'nvr-Z',
        'msg': 'Not Implemented. Testing only'
    }
    assert rv.get_json() == expected


ZIP_ENDPOINT_NOVER = '/v1/organization-X/repo-Y/zipfile'


@pytest.mark.parametrize('endpoint', [
    ZIP_ENDPOINT_NOVER,
    '/v1/organization-X/repo-Y/zipfile/1.0.1',
    '/v1/organization-X/repo-Y/koji/nvr-Z',
])
@pytest.mark.parametrize('method', [
    'GET', 'PATCH' 'PUT', 'HEAD', 'DELETE', 'TRACE',
])
def test_method_not_allowed(client, endpoint, method):
    """Specified endpoints currently support only POST method, test if other
    HTTP methods returns proper error code

    Method OPTIONS is excluded from testing due its special meaning
    """
    if (endpoint, method) == (ZIP_ENDPOINT_NOVER, 'DELETE'):
        # accepted, collides with [DELETE] /org/repo/version
        return

    rv = client.open(endpoint, method=method)
    assert rv.status_code == 405


@pytest.mark.parametrize('endpoint', [
    '/',
    '/v1'
    '/v1/organization-X/repo-Y/koji/',
    '/v1/organization-X/repo-Y/zipfile/version-Z/extra-something',
])
def test_404_for_mistyped_entrypoints(client, endpoint):
    """Test if HTTP 404 is returned for unexpected endpoints"""
    rv = client.post(endpoint)
    assert rv.status_code == 404
    rv_json = rv.get_json()
    assert rv_json['error'] == 'NotFound'
    assert rv_json['status'] == 404