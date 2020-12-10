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
log = logging.getLogger('kubernetes-model-source')


def main():

    if os.environ.get('RD_CONFIG_DEBUG') == 'true':
        log.setLevel(logging.DEBUG)
        log.debug("Log level configured for DEBUG")

    data = {}

    data["type"] = os.environ.get('RD_CONFIG_TYPE')
    data["yaml"] = os.environ.get('RD_CONFIG_YAML')
    data["name"] = os.environ.get('RD_CONFIG_NAME')
    data["namespace"] = os.environ.get('RD_CONFIG_NAMESPACE')

    common.connect()

    try:
        if data["type"] == "ConfigMap":
            api_instance = client.CoreV1Api()
            dep = yaml.safe_load(data["yaml"])
            resp = api_instance.patch_namespaced_config_map(
                name=data["name"],
                namespace=data["namespace"],
                body=dep,
                pretty="true")

            print(common.parseJson(resp.metadata))
    except ApiException as e:
        log.error("Exception error creating: %s\n" % e)
        sys.exit(1)


if __name__ == '__main__':
    main()
