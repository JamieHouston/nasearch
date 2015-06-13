#!/usr/bin/env python

import argparse
import os

DEFAULT_SECRET_FILE = 'scripts/secrets'
TEMPLATE_MAPPINGS = {
    os.path.join('templates', 'settings.py.template'):
    os.path.join('nadb', 'settings.py'),
    os.path.join('templates', 'settings_dev.py.template'):
    os.path.join('nadb', 'settings_dev.py')}
EXPECTED_SECRETS = set(['PROD_SECRET_KEY', 'PROD_DB_USER', 'PROD_DB_PASSWORD',
                        'DEV_SECRET_KEY', 'DEV_DB_USER', 'DEV_DB_PASSWORD'])


def template_file(template, to_file, keys):
    with open(template, 'r') as f:
        contents = ''.join(f.readlines())
        for k, v in keys.items():
            contents = contents.replace('<{}>'.format(k), v)
    with open(to_file, 'w') as f:
        f.write(contents)


def template_files(keys):
    for template, to_file in TEMPLATE_MAPPINGS.items():
        assert os.path.exists(template)
        template_file(template, to_file, keys)
        print("generating '{}' from '{}'".format(to_file, template))


def parse_keys_from_file(filename):
    keys = {}
    with open(filename) as f:
        for line in f:
            assert '=' in line
            key, val = line.split('=', 1)
            keys[key] = val.strip()
    return keys


def validate_secrets_file(filename):
    if not os.path.isfile(filename):
        print('error: {} not found'.format(filename))
        return False
    try:
        keys = parse_keys_from_file(filename)
    except Exception as e:
        print('error parsing secrets file\n')
        raise e
    if not all(k in keys.keys() for k in EXPECTED_SECRETS):
        print('error: expected to find {} in secrets file\n'
              .format([k for k in EXPECTED_SECRETS
                       if k not in keys.keys()]))
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description='configuration options for nadb')
    parser.add_argument('--secret', '-s',
                        help='file containing template '
                        'mappings for config files')
    args = parser.parse_args()
    keys_file = args.secret or DEFAULT_SECRET_FILE
    if not validate_secrets_file(keys_file):
        return
    keys = parse_keys_from_file(keys_file)
    assert set(keys.keys()) == EXPECTED_SECRETS
    template_files(keys)
    print('configuration complete')


if __name__ == '__main__':
    main()
