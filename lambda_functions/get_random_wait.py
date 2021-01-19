from random import randint


def handler(event, context):
    wait = randint(60, 300)
    return wait
