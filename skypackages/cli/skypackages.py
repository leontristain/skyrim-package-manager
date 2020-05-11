import click
from pathlib import Path

from skypackages.ui.skypackages import SkyPackagesGui
from skypackages.ui.fomod import FomodInstallerGui


@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    pass


@cli.command('gui')
@click.argument('packages_folder')
@click.argument('api_key')
@click.option('--aliases-folder')
def gui(packages_folder, api_key, aliases_folder):
    skypackages_gui = SkyPackagesGui(
        Path(packages_folder).resolve(), api_key, aliases_folder=aliases_folder)
    skypackages_gui.run()


@cli.command('fomod')
@click.argument('fomod_root')
def fomod(fomod_root):
    fomod_installer_gui = FomodInstallerGui(fomod_root)
    fomod_installer_gui.run()
