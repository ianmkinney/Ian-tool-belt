# Changelog

All notable changes to this project are documented in this file.

Release versions are managed by [release-please](https://github.com/googleapis/release-please) (see `.github/workflows/release.yml`); `belt.json` `version` bumps when the release PR merges.

## [0.4.0](https://github.com/ianmkinney/Ian-tool-belt/compare/v0.3.0...v0.4.0) (2026-10-16)


### Features

* add actionlint as a belt package and CI workflow lint ([c9eb2af](https://github.com/ianmkinney/Ian-tool-belt/commit/c9eb2afca55c15834e3531ac82bfe675ce9352b6))
* add app adoption kit and .tool-belt.json marker validation ([626ccfe](https://github.com/ianmkinney/Ian-tool-belt/commit/626ccfe580ac16f4e50548c0a5b744a3c1362996))
* add break room team board to the belt ([7eb861f](https://github.com/ianmkinney/Ian-tool-belt/commit/7eb861f4b865a17ad01030c16ac3c96c41d98c6c))
* add gitleaks secret scanning to the tool belt ([354478e](https://github.com/ianmkinney/Ian-tool-belt/commit/354478eeea5633b3de5619dfaf084f55dcdb5265))
* add shared versioning standard and app adoption kit ([de2e156](https://github.com/ianmkinney/Ian-tool-belt/commit/de2e1569fc6e3eb05036805f59bbf0f735cba487))
* add shellcheck-py as a belt package and CI shell lint ([4ca44cf](https://github.com/ianmkinney/Ian-tool-belt/commit/4ca44cfcf86bd83d34d6df4eeb390e5ddffefd3c))
* add weekly tool belt sync for adopted apps ([21ef1b4](https://github.com/ianmkinney/Ian-tool-belt/commit/21ef1b467b6e985e25aabcd5ae75a7c78754efca))
* blueprint GitHub Pages site for the tool belt ([#15](https://github.com/ianmkinney/Ian-tool-belt/issues/15)) ([388054c](https://github.com/ianmkinney/Ian-tool-belt/commit/388054ce6d23034d02ab33d35d4f958fecf015d7))
* break room shared board for agents ([f0266d4](https://github.com/ianmkinney/Ian-tool-belt/commit/f0266d43494cfa895fe70bda4b561d9b524b36f0))
* breakroom lobby notes, reactions and Bot of the Week ([d9b5300](https://github.com/ianmkinney/Ian-tool-belt/commit/d9b5300391adda9a0ddef850901f1f3f81b45624))
* breakroom lobby notes, reactions and Bot of the Week ([04c37a5](https://github.com/ianmkinney/Ian-tool-belt/commit/04c37a58874f59ebdaaf97c44094fa4bce643c28))
* fpr skill (fetch, pull, rebase) ([#23](https://github.com/ianmkinney/Ian-tool-belt/issues/23)) ([34aab26](https://github.com/ianmkinney/Ian-tool-belt/commit/34aab2609ea2fecc676193531963e045240f6037))
* generate adoption Cursor rules from the Cursor export instead of a duplicate rule ([c85a667](https://github.com/ianmkinney/Ian-tool-belt/commit/c85a667d161f551c60f844ff71ae19eb66114769))
* html-edit tool, brag, graphify, and archify ([#16](https://github.com/ianmkinney/Ian-tool-belt/issues/16)) ([6af8ab2](https://github.com/ianmkinney/Ian-tool-belt/commit/6af8ab2875fb3dfeb6a28c04d8630148c26cae04))
* pin llm 0.36 for local-ai shell prompts ([#24](https://github.com/ianmkinney/Ian-tool-belt/issues/24)) ([128f208](https://github.com/ianmkinney/Ian-tool-belt/commit/128f2082a94906b479545acc8614fc42a4628278))
* pin lychee 0.24.2 to check docs links ([#20](https://github.com/ianmkinney/Ian-tool-belt/issues/20)) ([d8f34ef](https://github.com/ianmkinney/Ian-tool-belt/commit/d8f34efc7c2c42bbbedadbb430b44d2780c5459d))
* pin ollmcp as a local Ollama MCP client ([81c66b2](https://github.com/ianmkinney/Ian-tool-belt/commit/81c66b2e0c80d7b6fa5dd1d7578308a2ddbbf0f8))
* tool proposal - act local GitHub Actions runner ([#19](https://github.com/ianmkinney/Ian-tool-belt/issues/19)) ([56ebfeb](https://github.com/ianmkinney/Ian-tool-belt/commit/56ebfebe273e50bdf05dd840925901e10d8d04a6))
* tool proposal - actionlint workflow checks ([4e8fc0a](https://github.com/ianmkinney/Ian-tool-belt/commit/4e8fc0a431e4ef94c8a271fb33bf4dd4a3f861df))
* tool proposal - gitleaks secret scanning ([f56a4c8](https://github.com/ianmkinney/Ian-tool-belt/commit/f56a4c8d514c771204f2f024fba1fee42091c548))
* tool proposal - markdownlint-cli2 Markdown linter ([#25](https://github.com/ianmkinney/Ian-tool-belt/issues/25)) ([731f166](https://github.com/ianmkinney/Ian-tool-belt/commit/731f166dde63f1696bfab018bf766f0c0e3c2631))
* tool proposal - ollmcp MCP client for local Ollama models ([3f78891](https://github.com/ianmkinney/Ian-tool-belt/commit/3f78891383ffdc495fdf37fbcaa8d94abb8021dd))
* tool proposal - OSV-Scanner dependency vulnerability scan ([#17](https://github.com/ianmkinney/Ian-tool-belt/issues/17)) ([e1301dc](https://github.com/ianmkinney/Ian-tool-belt/commit/e1301dc31bc89cb969eaf3f0b493863d97c4d2a8))
* tool proposal - pre-commit hooks for belt linters ([#18](https://github.com/ianmkinney/Ian-tool-belt/issues/18)) ([cd866e4](https://github.com/ianmkinney/Ian-tool-belt/commit/cd866e4d1b72d990e4fb5444402b40a63f05ecfe))
* tool proposal - ruff Python linter ([#22](https://github.com/ianmkinney/Ian-tool-belt/issues/22)) ([14f1d1b](https://github.com/ianmkinney/Ian-tool-belt/commit/14f1d1b4562546688c56f7388924ea201e40a8b6))
* tool proposal - shellcheck script linting ([21797f4](https://github.com/ianmkinney/Ian-tool-belt/commit/21797f4498246b3dea954813c3652cdf7e38d99c))
* tool proposal - typos spell checker ([#21](https://github.com/ianmkinney/Ian-tool-belt/issues/21)) ([b903880](https://github.com/ianmkinney/Ian-tool-belt/commit/b903880399757071d33f6c35bb05a50dbb4a8660))


### Bug Fixes

* pin app adoption workflows to belt release SHA ([ff1ce18](https://github.com/ianmkinney/Ian-tool-belt/commit/ff1ce189292dc22af056c35eeb934a358675d932))
* pin app adoption workflows to belt release SHA ([c47f693](https://github.com/ianmkinney/Ian-tool-belt/commit/c47f6936700e8d45e6ab8b4201bf149757eebd20))

## [Unreleased]

### Added

- Pin **pre-commit** 4.6.2 (MIT) with a shared `.pre-commit-config.yaml` that runs gitleaks, shellcheck-py, actionlint, zizmor and basic hygiene hooks at the same versions as CI, plus a `templates/pre-commit/` copy path and a `pre-commit.yml` workflow.
