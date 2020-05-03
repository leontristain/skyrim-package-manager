# Use Cases

This will be the primary tool for authors and users of skybuild recipes to manage the overall packages folder.

To start, you would point the UI to the path of a packages folder.

## Packages Folder

The packages folder is a gigantic folder of tarballs downloaded from the internet. Every file you download from the Nexus, from Loverslab, from various blogs, etc..., as well as packages you have built yourself, will go into here.

Every file downloaded will be added here and appended to its filename a hash of the file, to ensure uniqueness. Every file downloaded will also update an index file so that other things using the packages folder can query metadata quickly. It more or less operates the same way as the conda-build source cache.

All files of the packages folder will be renamed into the exact hash, and a "view" folder will be created via symlinks for user browsing.

Separate from the main contents of the packages folder will be 2 other folders, an aliases folder and a source folder.

### The Alias Folder

Skybuild recipes need to refer to tarballs with short string ids (such as `nemesis-pcea` or `ussep`). Each tarball downloaded into the packages folder is identified by its content hash, therefore as you add tarballs into the packages folder, you need to additionally provide it an alias. The aliases are saved into the aliases folder. Initially we will only have an `aliases.yaml`, but over time we may create a layered scheme if the need comes up.

One alias can be associated with multiple package tarballs.

### The Sources Folder

Package tarballs can come from any number of sources. The biggest being NexusMods, for which we have an API with rich metadata. Other sources may include LoversLab (the adult content mod site), various personal blogs of mod creators, patreon links users may have access to, releases of SKSE and ENB, etc...

A "source" is defined as metadata information for where a tarball can be downloaded from, and is stored as separate metadata. Other than NexusMods API which allow us to store rich metadata, customly-downloaded tarballs may require the user to manually enter download URLs and any instructive notes.

A single tarball may be downloadable from multiple sources. When the user adds sources, if the tarball has the same content, it is deduplicated and the two sources informations will be attached to the same hash. The sources folder includes the original file names and can be used to rebuild the view from the packages folder.

## The `skypackages` Tool

The `skypackages` tool can be used to download packages into the packages folder.

### Workflow from Nexus

When you browse mods on Nexus, at any point you want to include a mod, the entry point will be copying over the nexus mods URL. So you would copy:

    https://www.nexusmods.com/skyrimspecialedition/mods/31667?tab=posts

... and then paste it into Nexus URL field, and hit enter. The moment you do,
skypackages will parse out the mod string and the mod ID, and use them to query nexus for mod details, available files, etc... and populate them on the UI.

At that point, the user can browse the mod page within the app, and choose the file to download. The app will automatically download the file to the packages folder and update all necessary metadata.

When you choose the file to download, depending on whether you have an alias selected on the left, the buttons "Download and Add As New" and "Download and Add Into" will be available. You can also "Diff With Existing" to get a file tree diff between the existing tarball and the new tarball you are adding.

### Workflow from Custom Tarball

A separate tab allows you to point to a custom folder where you may select tarballs. It may be good to point this to your downloads folder.

Once a tarball is downloaded, you can refresh to see it in the list, then you can select it, and enter any metadata information manually, before importing it into your packages database.

Part of the metadata involves entering an download URL. Once entered, WebEngine view will preview you the location of that URL.

When you choose the file to download, depending on whether you have an alias selected on the left, the buttons "Download and Add As New" and "Download and Add Into" will be available. You can also "Diff With Existing" to get a file tree diff between the existing tarball and the new tarball you are adding.

### Browsing Existing Aliases

The overall list of aliases for tarballs are displayed on the left, they can be sorted alphabetically, sorted by tarball timestamps, or sorted by alias creation timestamp. In both cases they can be sorted in ascending or descending order.

Aliases can also be filtered via a search field.

When an alias is selected, the list of packages it is associated with is displayed in a smaller list box below (by file name). Each file name can then be selected to display its available sources, which will show up on the right.

The file names box can be used to diff across two packages by content.

### Scope of Tool

Overall, the `skypackages` tool is purely the management of packages, sources, and aliases. The aliases forms the interface between the package and the recipe. Essentially, the recipe will specify things by alias name, assuming the alias points to the expected tarball to be used.

This means the recipe will need to ship with its own alias-to-tarball mapping. In fact, someone distributing the recipe will want to ship not just alias-to-tarball mapping, but also the expected sources. The skybuild API will allow for extracting only the subset of metadata that a recipe uses, from the packages folder data.

Likewise, the skypackages API will allow metadata overrides from a recipe provider in its configuration.
