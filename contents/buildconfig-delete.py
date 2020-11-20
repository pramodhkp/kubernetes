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


def main():
    common.connect()

    data = {"namespace": os.environ.get('RD_CONFIG_NAMESPACE'), "name": os.environ.get('RD_CONFIG_NAME')}

    k8s_client = config.new_client_from_config()
    openshift_client = DynamicClient(k8s_client)

    try:
        v1_bc = openshift_client.resources.get(api_version='build.openshift.io/v1', kind='BuildConfig')

        resp = v1_bc.delete(name=data["name"], namespace=data["namespace"])
        print(common.parseJson(resp.metadata))
    except ApiException as e:
        log.error("Exception error creating: %s\n" % e)
        sys.exit(1)


if __name__ == '__main__':
    main()
