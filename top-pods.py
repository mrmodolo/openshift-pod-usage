#!/usr/bin/env python3

import openshift as oc
import re
import sys
import time
from prometheus_client import start_http_server, Gauge
from environs import Env
from datetime import datetime


# CPU units
# https://kubernetes.io/docs/tasks/configure-pod-container/assign-cpu-resource/
# Fractional values are allowed. A Container that requests
# 0.5 CPU is guaranteed half as much CPU as a Container that requests 1 CPU.
# You can use the suffix m to mean milli.
# For example 100m CPU, 100 milliCPU, and 0.1 CPU are all the same.
# Precision finer than 1m is not allowed.

# https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/
# Memory units
# The memory resource is measured in bytes.
# You can express memory as a plain integer or a fixed-point integer
# with one of these suffixes: E, P, T, G, M, K, Ei, Pi, Ti, Gi, Mi, Ki.
# For example, the following represent approximately the same value:
#
# 128974848, 129e6, 129M , 123Mi


SUFFIXES = {
    'E': 1024 << 110,
    'P': 1024 << 100,
    'T': 1024 << 90,
    'G': 1024 << 80,
    'M': 1024 << 70,
    'K': 1024 << 60,
    'Ei': 1024 << 50,
    'Pi': 1024 << 40,
    'Ti': 1024 << 30,
    'Gi': 1024 << 20,
    'Mi': 1024 << 10,
    'Ki': 1024 << 0,
}


# https://prometheus.io/docs/practices/naming/
LABELS = ['namespace', 'app', 'pod']

CPU = Gauge('k8s_pod_cpu_usage_cores', 'POD CPU Usage Cores', LABELS)

MEMORY = Gauge('k8s_pod_memory_usage_bytes', 'POD Memory Usage Bytes', LABELS)


def normalize_usage_cpu(value):
    """Retorna o valor de cpu em cores"""
    cpu = 0
    index = value.find('m')
    if index > 0:
        cpu = float(value[0:index])/1000.0
    else:
        cpu = float(value)
    return cpu


def normalize_usage_memory(value):
    """Retorna o valor de memória em bytes"""
    if value.isnumeric():  # nenhum sufixo ou , ou .
        return int(value)
    memory = 0
    match = re.search(r'(?P<number>\d+)(?P<suffixe>\D+)', value)
    if match:
        number = int(match.group('number'))
        suffixe = match.group('suffixe')
        memory = number * SUFFIXES[suffixe]
    return memory


def get_pod_metrics(pod):
    """Retorna a métrica do pod ou
    None caso não exista métrica
    """
    metric = oc.get_pod_metrics(pod, auto_raise=False)
    if isinstance(metric, oc.apiobject.APIObject):
        return metric
    return None


def get_container_usage(container):
    """Retorna um dicionário com os valores de
    cpu em cores e memória em bytes
    """
    cpu = normalize_usage_cpu(container['usage']['cpu'])
    memory = normalize_usage_memory(container['usage']['memory'])
    return {'cpu': cpu, 'memory': memory}


class ContainerUsage():
    """
    Uma estrutura simples!
    """
    __slots__ = ['app_name', 'pod_name', 'usage']

    def __init__(self, app_name='', pod_name='', usage={}):
        self.app_name = app_name
        self.pod_name = pod_name
        self.usage = usage

    def __str__(self):
        str_self = 'app: {}, pod: {}, usage: {}'
        return str_self.format(self.app_name, self.pod_name, self.usage)


def get_pod_containers_usage(project):
    """
    Retorna um iterador para cada container com
    métricas
    """
    with oc.project(project), oc.timeout(2*60):
        for pod_obj in oc.selector('pods').objects():
            metric = get_pod_metrics(pod_obj)
            pod_name = pod_obj.model.metadata.name
            if metric:
                containers = metric.model.containers
                for container in containers:
                    app_name = container['name']
                    usage = get_container_usage(container)
                    containerUsage = ContainerUsage(app_name,
                                                    pod_name, usage)
                    yield containerUsage
            else:
                msg = 'Nenhuma métrica para o pod {}'.format(pod_name)
                info_msg(msg)


def get_server(server):
    env = Env()
    server = env('OPENSHIFT_SERVER', server)
    return server


def get_token(token):
    env = Env()
    token = env('OPENSHIFT_TOKEN', token)
    return token


def get_wait_time_seconds(seconds=60*5):
    env = Env()
    seconds = env.int('WAIT_TIME_SECONDS', seconds)
    return seconds


def get_metrics_server_port(port=8000):
    env = Env()
    port = env.int('METRICS_SERVER_PORT', port)
    return port


def get_namespaces():
    env = Env()
    namespaces = env.list('NAMESPACES')
    return namespaces


def info_msg(msg):
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    sys.stdout.write('[{}] {}\n'.format(now, msg))


def err_msg(msg):
    now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    sys.stderr.write('[{}] {}\n'.format(now, msg))


def main():
    port = get_metrics_server_port()
    PROJECTS = get_namespaces()
    wait_time_seconds = get_wait_time_seconds()
    info_msg('Environment PROJECTS: {}'.format(PROJECTS))
    info_msg('Environment wait_time_seconds: {}'.format(wait_time_seconds))
    start_http_server(port)
    try:
        while True:
            for project in PROJECTS:
                info_msg('Project: {}'.format(project))
                for container in get_pod_containers_usage(project):
                    app = container.app_name
                    pod = container.pod_name
                    cpu = container.usage['cpu']
                    memory = container.usage['memory']
                    CPU.labels(namespace=project, app=app, pod=pod).set(cpu)
                    MEMORY.labels(namespace=project,
                                  app=app, pod=pod).set(memory)
                    msg = '{}'.format(container)
                    info_msg(msg)
            msg = 'Aguardando #{} segundos.'
            info_msg(msg.format(wait_time_seconds))
            time.sleep(wait_time_seconds)
    except oc.OpenShiftPythonException as ocException:
        err_msg(repr(ocException))
    except KeyboardInterrupt:
        err_msg('Saindo.')
        sys.exit()


if __name__ in '__main__':
    main()
