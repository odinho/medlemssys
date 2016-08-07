import os

from logan.runner import run_app

import medlemssys.config.settings.defaults


def generate_settings():
    """
    This command is run when ``default_path`` doesn't exist, or ``init`` is
    run and returns a string representing the default data to put into their
    settings file.
    """
    dir = os.path.dirname(medlemssys.config.settings.defaults.__file__)
    settings = open(os.path.join(dir, 'defaults.py')).read()
    return settings


def main():
    run_app(
        project='medlemssys',
        default_config_path='medlemssys_conf.py',
        default_settings='medlemssys.config.settings.defaults',
        settings_initializer=generate_settings,
        settings_envvar='MEDLEMSSYS_CONF',
    )


if __name__ == '__main__':
    main()
