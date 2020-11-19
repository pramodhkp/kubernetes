#!/usr/bin/env python -u
import logging
import sys
import os
import yaml
import common
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from openshift.dynamic import DynamicClient


logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format='%(levelname)s: %(name)s: %(message)s')
log = logging.getLogger('openshift-buildconfig-create')


def main():
    common.connect()

    data = {}
    data["yaml"] = os.environ.get('RD_CONFIG_YAML')
    data["namespace"] = os.environ.get('RD_CONFIG_NAMESPACE')

    try:
        dep = yaml.safe_load(data["yaml"])
        k8s_client = config.new_client_from_config()
        openshift_client = DynamicClient(k8s_client)
        v1_bc = openshift_client.resources.get(api_version='build.openshift.io/v1', kind='BuildConfig')

        resp = v1_bc.create(body=dep, namespace=data["namespace"])
    except ApiException as e:
        log.error("Exception error creating: %s\n" % e)
        sys.exit(1)

    print(common.parseJson(resp.metadata))


if __name__ == '__main__':
    main()
