import click

from skypackages.ui.gui import SkyPackagesGui


@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    pass


@cli.command('gui')
@click.argument('packages_folder')
def gui(packages_folder):
    skypackages_gui = SkyPackagesGui(packages_folder)
    skypackages_gui.run()
