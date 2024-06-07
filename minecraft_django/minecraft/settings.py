# minecraft_django/settings.py

import environ

env = environ.Env()
environ.Env.read_env()

NAMESPACE = env('NAMESPACE', default='default')
STATEFULSET_NAME = env('STATEFULSET_NAME', default='minecraft-server')
CONTAINER_NAME = env('CONTAINER_NAME', default='minecraft-server')
