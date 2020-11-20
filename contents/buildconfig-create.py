#!/usr/bin/env python -u
import logging
import sys
import os
import yaml
import common
import json
import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient


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

    data = {"yaml": os.environ.get('RD_CONFIG_YAML'), "namespace": os.environ.get('RD_CONFIG_NAMESPACE'), "name": os.environ.get('RD_CONFIG_NAME')}

    k8s_client = config.new_client_from_config()
    openshift_client = DynamicClient(k8s_client)

    try:
        dep = yaml.safe_load(data["yaml"])
        v1_bc = openshift_client.resources.get(api_version='build.openshift.io/v1', kind='BuildConfig')

        resp = v1_bc.create(body=dep, namespace=data["namespace"])
        print(common.parseJson(resp.metadata))
    except ApiException as e:
        if e.status == 409:
            log.warning("Build config already exists.")
            _trigger_build(data["namespace"], data["name"])
        else:
            log.error("Exception error creating: %s\n" % e)
            sys.exit(1)



if __name__ == '__main__':
    main()
