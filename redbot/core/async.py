"""
Manages the setup for task handling.
"""
import os

from celery import Celery

from redbot.core.models import modules
from redbot.core.utils import get_core_setting, get_random_attack, safe_load_config
from redbot.settings import REDIS_HOST, BEAT_INTERVAL

if not modules:
    safe_load_config()
celery = Celery(include=modules, backend='redis://' + os.getenv('REDIS_HOST', REDIS_HOST),
                broker='redis://' + os.getenv('REDIS_HOST', REDIS_HOST))
celery.conf.update(
    task_soft_time_limit=int(get_core_setting('task_timeout') or 120),
    task_time_limit=int(get_core_setting('task_timeout') or 120) + 60
)


@celery.task
def run_jobs() -> None:
    """
    Chooses a random attack and executes it.
    """
    attack = get_random_attack()
    if get_core_setting('enable_attacks'):
        attack.run_attack()


@celery.on_after_configure.connect
def set_up_periodic_tasks(sender: Celery, **kwargs) -> None:
    """
    Configured scheduled tasks. Both discovery and attack jobs run every 10 seconds, but further code may choose
    whether or not to execute something at this point. This method shouldn't be called except by Celery itself.

    :param sender: Celery instance
    :param kwargs: Optional values
    """
    if not modules:
        safe_load_config()
    sender.add_periodic_task(BEAT_INTERVAL, run_jobs.s(), name='Launch attacks')
    from redbot.modules.discovery import do_discovery
    sender.add_periodic_task(BEAT_INTERVAL, do_discovery.s(), queue='discovery', name='Launch discovery')
