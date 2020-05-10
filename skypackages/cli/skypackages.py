import click
from pathlib import Path

from skypackages.ui.skypackages import SkyPackagesGui
from skypackages.ui.fomod import FomodInstallerGui

import sys
print(sys.argv)


@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    pass


@cli.command('gui')
@click.argument('packages_folder')
@click.argument('api_key')
def gui(packages_folder, api_key):
    skypackages_gui = SkyPackagesGui(
        Path(packages_folder).resolve(), api_key)
    skypackages_gui.run()


@cli.command('fomod')
@click.argument('fomod_root')
def fomod(fomod_root):
    fomod_installer_gui = FomodInstallerGui(fomod_root)
    fomod_installer_gui.run()
