import click

from skypackages.ui.gui import SkyPackagesGui


@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    pass


@cli.command('gui')
@click.argument('packages_folder')
@click.argument('api_key')
def gui(packages_folder, api_key):
    skypackages_gui = SkyPackagesGui(packages_folder, api_key)
    skypackages_gui.run()
