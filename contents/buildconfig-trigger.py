#!/usr/bin/env python -u
import logging
import sys
import os
import common
import json
import requests


logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger('openshift-buildconfig-create')


def _trigger_build(namespace, name):
    headers = {
        'Authorization': 'Bearer ' + os.environ.get('RD_CONFIG_TOKEN'),
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    data = '''
        {
        "kind":"BuildRequest","apiVersion":"build.openshift.io/v1",
        "metadata":
            {
                "name":"%s",
                "creationTimestamp":null
            },
            "triggeredBy":[{"message":"Manually triggered"}],
            "dockerStrategyOptions":{},
            "sourceStrategyOptions":{}
        }
    ''' % name

    url = os.environ.get('RD_CONFIG_URL') + "/apis/build.openshift.io/v1/namespaces/{}/buildconfigs/{}/instantiate".format(namespace, name)
    if url is not None:
        try:
            response = requests.post(url=url, json=json.loads(data), headers=headers, verify=False)
            print(common.parseJson(response.text))
        except requests.HTTPError as e:
            log.error("Exception while triggering build: %s\n" % e)
            sys.exit(1)


def main():
    common.connect()

    data = {"namespace": os.environ.get('RD_CONFIG_NAMESPACE'), "name": os.environ.get('RD_CONFIG_NAME')}
    disable_build = os.environ.get('RD_CONFIG_DISABLEBUILD')

    if disable_build != "false":
        sys.exit(0)

    _trigger_build(data["namespace"], data["name"])


if __name__ == '__main__':
    main()
