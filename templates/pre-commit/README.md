# Pre-commit template

Copy the belt's shared hook config into an app repo when you want local checks before `git commit`. Hooks are **opt-in**: copying this file does not install anything until you run `pre-commit install`.

From your app repository (with a checkout of Ian-tool-belt available):

```sh
cp path/to/Ian-tool-belt/templates/pre-commit/.pre-commit-config.yaml .
python3 -m pip install 'pre-commit==4.6.2'
pre-commit install
```

Use the `pre-commit` package version from `belt.json` (`packages` entry `pre-commit`). After install, hooks run on each commit; run everything on demand with:

```sh
pre-commit run --all-files
```

To remove: `pre-commit uninstall`, delete `.pre-commit-config.yaml`, and drop the `pre-commit` package from `belt.json` if you added one for documentation.
