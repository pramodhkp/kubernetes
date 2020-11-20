#!/usr/bin/env python -u
import logging
import sys
import common
import time

from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes import watch
from openshift.dynamic import DynamicClient


from os import environ

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(levelname)s: %(name)s: %(message)s"
)
log = logging.getLogger("openshift-wait-build")


def wait():
    try:
        name = environ.get("RD_CONFIG_NAME")
        namespace = environ.get("RD_CONFIG_NAMESPACE")
        retries = int(environ.get("RD_CONFIG_RETRIES"))
        sleep = float(environ.get("RD_CONFIG_SLEEP"))
        show_log = environ.get("RD_CONFIG_SHOW_LOG") == "true"

        # Poll for completion if retries
        retries_count = 0
        completed = False


        while True:

            common.connect()

            core_v1 = client.CoreV1Api()

            label_selector = "buildconfig={}".format(name)
            k8s_client = config.new_client_from_config()
            openshift_client = DynamicClient(k8s_client)

            v1_bc = openshift_client.resources.get(api_version='build.openshift.io/v1', kind='Build')
            build_list = v1_bc.get(namespace=namespace, label_selector=label_selector)

            latest_build = build_list.items[-1]
            log.debug(latest_build)

            retries_count = retries_count + 1
            if retries_count > retries:
                log.error("Number of retries exceeded")
                completed = True

            if latest_build['status']['phase'] == 'Failed':
                completed = True

            if latest_build['status']['completionTimestamp']:
                completed = True

            if show_log:
                log.debug("Searching for pod associated with build")

                schedule_start_time = time.time()
                schedule_timeout = 600
                while True:
                    try:
                        v1_pods = openshift_client.resources.get(api_version='v1', kind='Pod')
                        label_selector = "openshift.io/build.name={}".format(latest_build['metadata']['name'])
                        log.debug(label_selector)
                        pod_list = v1_pods.get(namespace=namespace, label_selector=label_selector)
                        log.debug(pod_list)
                        pod_name = pod_list.items[-1]['metadata']['name']
                        break
                    except IndexError as IndexEx:
                        log.info("Still Waiting for build pod to be scheduled")
                        time.sleep(2)
                        if schedule_timeout and time.time() - schedule_start_time > schedule_timeout:  # pragma: no cover
                            raise TimeoutError

                log.info("Fetching logs from pod: {0}".format(pod_name))

                log.info("========================== build pod log start ==========================")
                start_time = time.time()
                timeout = 300
                while True:
                    try:
                        core_v1.read_namespaced_pod_log(name=pod_name,
                                                        namespace=namespace)
                        break
                    except ApiException as ex:
                        log.warning("Pod is not ready, status: {}".format(ex.status))
                        if ex.status == 200:
                            break
                        else:
                            log.info("waiting for log")
                            time.sleep(15)
                            if timeout and time.time() - start_time > timeout:  # pragma: no cover
                                raise TimeoutError

                w = watch.Watch()
                for line in w.stream(core_v1.read_namespaced_pod_log,
                                     name=pod_name,
                                     namespace=namespace):
                    print(line)

                log.info("=========================== job log end ===========================")

            if completed:
                break

            log.info("Waiting for job completion")
            show_log = False
            time.sleep(sleep)

        if latest_build['status']['phase'] == "Complete":
            log.info("Build succeeded")
            sys.exit(0)
        else:
            log.info("Build failed")
            sys.exit(1)

    except ApiException as e:
        log.error("Exception waiting for build: %s\n" % e)
        sys.exit(1)


def main():
    if environ.get("RD_CONFIG_DEBUG") == "true":
        log.setLevel(logging.DEBUG)
        log.debug("Log level configured for DEBUG")

    common.connect()
    wait()


if __name__ == "__main__":
    main()
