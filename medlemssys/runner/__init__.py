import os

from logan.runner import run_app

import config.settings.production


def generate_settings():
    """
    This command is run when ``default_path`` doesn't exist, or ``init`` is
    run and returns a string representing the default data to put into their
    settings file.
    """
    dir = os.path.dirname(config.settings.production.__file__)
    settings = open(os.path.join(dir, 'production.py')).read()
    return settings


def main():
    run_app(
        project='medlemssys',
        default_config_path='medlemssys_conf.py',
        default_settings='config.settings.production',
        settings_initializer=generate_settings,
        settings_envvar='MEDLEMSSYS_CONF',
    )


if __name__ == '__main__':
    main()
