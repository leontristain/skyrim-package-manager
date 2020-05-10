import click

from skypackages.ui.fomod import FomodInstallerGui


@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    pass


@cli.command('gui')
@click.argument('fomod_root')
def gui(fomod_root):
    fomod_installer_gui = FomodInstallerGui(fomod_root)
    fomod_installer_gui.run()
