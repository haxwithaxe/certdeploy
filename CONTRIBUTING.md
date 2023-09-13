# Contributing

Welcome to `certdeploy` contributor's guide.

This document focuses on getting any potential contributor familiarized with
the development processes, but [other kinds of contributions] are also appreciated.

If you are new to using [git] or have never collaborated in a project previously,
please have a look at [contribution-guide.org]. Other resources are also
listed in the excellent [guide created by FreeCodeCamp] [^contrib1].

Please notice, all users and contributors are expected to be **open,
considerate, reasonable, and respectful**. When in doubt,
[Python Software Foundation's Code of Conduct] is a good reference in terms of
behavior guidelines.

## Issue Reports

If you experience bugs or general issues with `certdeploy`, please have a look
on the [issue tracker].
If you don't see anything useful there, please feel free to fire an issue report.

:::{tip}
Please don't forget to include the closed issues in your search.
Sometimes a solution was already reported, and the problem is considered
**solved**.
:::

New issue reports should include information about your environment
(e.g., operating system, Python version, docker image version) and steps to
reproduce the problem. Please try also to simplify the reproduction steps to a
very minimal example that still illustrates the problem you are facing. By
removing other factors, you help us to identify the root cause of the issue.

## Documentation Improvements

You can help improve `certdeploy` docs by making them more readable and coherent, or
by adding missing information and correcting mistakes.

`certdeploy` documentation uses [Sphinx] as its main documentation compiler.
This means that the docs are kept in the same repository as the project code, and
that any documentation update is done in the same way was a code contribution.

`certdeploy` documentation is written with [MyST] markdown. In any README.md
the goal is to remain as close to GitHub markdown so that they can be read
cleanly directly on GitHub. Doc-strings are handled slightly differently than
\*.md files. Just follow the existing patterns in the documentation unless your
changes are specifically (and only) changing patterns globally.

Some extra rules for the README.md and other .md files:
- Variable and dictionary key names, and inline commands and code get single back ticks.
- Literal values, variable values including numbers get double back ticks.
- Anywhere a default value from the code is redeclared add an html comment like the following ``<!--DEFAULT FROM CODE- certdeploy.where_ever.the.value.lives -->`` at the end of the line to make it easier to audit the docs for defaults that need updating.

:::{tip}
   Please notice that the [GitHub web interface] provides a quick way of
   propose changes in `certdeploy`'s files. While this mechanism can
   be tricky for normal code contributions, it works perfectly fine for
   contributing to the docs, and can be quite handy.

   If you are interested in trying this method out, please navigate to
   the `docs` folder in the source [repository], find which file you
   would like to propose changes and click in the little pencil icon at the
   top, to open [GitHub's code editor]. Once you finish editing the file,
   please write a message in the form at the bottom of the page describing
   which changes have you made and what are the motivations behind them and
   submit your proposal.
:::

When working on documentation changes in your local machine, you can
compile them using [tox] :

```
tox -e docs
```

and use Python's built-in web server for a preview in your web browser
(`http://localhost:8000`):

```
python3 -m http.server --directory 'docs/_build/html'
```

## Code Contributions

All code must:
* Conform to [Google's python style guide] with a few exceptions. Look at the
   existing code for a lead on those changes. Bellow are some of them.
   * Always prefer single quotes except around doc-strings or inside single
      quotes.
   * Use `Arguments:` instead of `Args:` in doc-strings.
   * No trailing commas except in single item tuples.
   * Type hinting must be used unless conforming to an interface that
      doesn't use it.
      * returning `None`, `self`, or `cls` hints are not needed.
         * Remember to not include type info in `Arguments:` unless the code
            isn't type hinted. For example:


               Arguments:
                  foo: The correct way if using type hinting.

               Arguments:
                  foo (int): The correct way if not using type hinting.


* Pass the pre-commit linting or `tox -e lint` (same thing).
* Pass the unit tests (`tox -e default`).
* Pass the docker tests (`tox -e dockerbuild && tox -e dockertest`).

New features must:
* Include unit tests or integration tests covering both success and failure modes.
* Include corresponding documentation changes.

Changes must:
* Include updated tests where they exist already.

All code should:
* Have accompanying unit or integration tests. It's not required. The project
   isn't starting with 100% coverage so it's not going to ruin anything.

Notes on testing:
* The tests are split into tests for the code and tests for the docker containers. There will be some ``deselected`` tests. Don't worry about that. They all get run eventually throughout the testing process.

Notes on writing tests:
* Tests fixtures that return plain `callable`s should use the `typing.Callable` with as much of the detail as is relevant to how it's being used. Arguments are less important than return values in general on the test side. For example:

   ```
   def test_foo_does_bar(dummy_foo_factory: Callable[[important_config, ...], DummyFoo]):
      ...
   ```

   `dummy_foo_factory` could take a dozen more arguments but `important_config` is all the test uses and `DummyFoo` is what the test interacts with. This is just to make IDEs happier.

### Submit an issue

Before you work on any non-trivial code contribution it's best to first create
a report in the [issue tracker] to start a discussion on the subject.
This often provides additional considerations and avoids unnecessary work.

### Create an environment

Before you start coding, we recommend creating an isolated [virtual environment]
to avoid any problems with your installed Python packages.
This can easily be done via either [virtualenv]:

```
virtualenv <PATH TO VENV>
source <PATH TO VENV>/bin/activate
```

or [Miniconda]:

```
conda create -n certdeploy python=3 six virtualenv pytest pytest-cov
conda activate certdeploy
```

### Clone the repository

1. Create an user account on GitHub if you do not already have one.

2. Fork the project [repository]: click on the *Fork* button near the top of the
   page. This creates a copy of the code under your account on GitHub.

3. Clone this copy to your local disk:

   ```
   git clone git@github.com:YourLogin/certdeploy.git
   cd certdeploy
   ```

4. You should run:

   ```
   pip install -U pip setuptools -e .
   ```

   to be able to import the package under development in the Python REPL.

5. Install [pre-commit]:

   ```
   pip install pre-commit
   pre-commit install
   ```

   `certdeploy` comes with a lot of hooks configured to automatically help the
   developer to check the code being written.

6. Install docker and initialize a swarm node if you don't already have those.
   The integration tests require a docker swarm node. The steps to accomplish
   those is beyond the scope of this document.


### Implement your changes

1. Create a branch to hold your changes:

   ```
   git checkout -b my-feature
   ```

   and start making changes. Never work on the main branch!

2. Start your work on this branch. Don't forget to add [docstrings] to new
   functions, modules and classes, especially if they are part of public APIs.

3. Add yourself to the list of contributors in `AUTHORS.rst`.

4. When you’re done editing, do:

   ```
   git add <MODIFIED FILES>
   git commit
   ```

   to record your changes in [git].

   Please make sure to see the validation messages from [pre-commit] and fix
   any eventual issues.
   This should automatically use [flake8]/[black] to check/fix the code style
   in a way that is compatible with the project.

   :::{important}
   Don't forget to add unit tests and documentation in case your
   contribution adds an additional feature and is not just a bugfix.

   Moreover, writing a [descriptive commit message] is highly recommended.
   In case of doubt, you can check the commit history with:

   ```
   git log --graph --decorate --pretty=oneline --abbrev-commit --all
   ```

   to look for recurring communication patterns.
   :::

5. Please check that your changes don't break any unit or integration tests with:

   ```
   tox
   ```
   Or if you have made changes to anything in `docker/client` or `docker/server`

   ```
   tox -e lint && tox -e default && tox -e dockerbuild && tox -e dockertest
   ```

   (after having installed [tox] with `pip install tox` or `pipx`).

   You can also use [tox] to run several other pre-configured tasks in the
   repository. Try `tox -av` to see a list of the available checks.

   The pytest tests are split into tests that test the code and tests that test
   the docker images. There will be "skipped" tests unless calling pytest
   directly.


### Submit your contribution

1. If everything works fine, push your local branch to the remote server with:

   ```
   git push -u origin my-feature
   ```

2. Go to the web page of your fork and click "Create pull request"
   to send your changes for review.


### Troubleshooting

The following tips can be used when facing problems to build or test the
package:

1. Make sure to fetch all the tags from the upstream [repository].
   The command `git describe --abbrev=0 --tags` should return the version you
   are expecting. If you are trying to run CI scripts in a fork repository,
   make sure to push all the tags.
   You can also try to remove all the egg files or the complete egg folder, i.e.,
   `.eggs`, as well as the `*.egg-info` folders in the `src` folder or
   potentially in the root of your project.

2. Sometimes [tox] misses out when new dependencies are added, especially to
   `setup.cfg` and `docs/requirements.txt`. If you find any problems with
   missing dependencies when running a command with [tox], try to recreate the
   `tox` environment using the `-r` flag. For example, instead of:

   ```
   tox -e docs
   ```

   Try running:

   ```
   tox -r -e docs
   ```

3. Make sure to have a reliable [tox] installation that uses the correct
   Python version (e.g., 3.7+). When in doubt you can run:

   ```
   tox --version
   # OR
   which tox
   ```

   If you have trouble and are seeing weird errors upon running [tox], you can
   also try to create a dedicated [virtual environment] with a [tox] binary
   freshly installed. For example:

   ```
   virtualenv .venv
   source .venv/bin/activate
   .venv/bin/pip install tox
   .venv/bin/tox -e all
   ```

4. [Pytest can drop you] in an interactive session in the case an error occurs.
   In order to do that you need to pass a `--pdb` option (for example by
   running `tox -- -k <NAME OF THE FALLING TEST> --pdb`).
   You can also setup breakpoints manually instead of using the `--pdb` option.

## Maintainer tasks

### Releases

If you are part of the group of maintainers and have correct user permissions
on [PyPI], the following steps can be used to release a new version for
`certdeploy`:

1. Make sure all unit and integration tests are successful.
2. Tag the current commit on the main branch with a release tag, e.g., `v1.2.3`.
3. Push the new tag to the upstream [repository],
   e.g., `git push upstream v1.2.3`
4. Clean up the `dist` and `build` folders with `tox -e clean`
   (or `rm -rf dist build`)
   to avoid confusion with old builds and Sphinx docs.
5. Run `tox -e build` and check that the files in `dist` have
   the correct version (no `.dirty` or [git] hash) according to the [git] tag.
   Also check the sizes of the distributions, if they are too big (e.g., >
   500KB), unwanted clutter may have been accidentally included.
6. Run `tox -e publish -- --repository pypi` and check that everything was
   uploaded to [PyPI] correctly.

[^contrib1]: Even though, these resources focus on open source projects and
    communities, the general ideas behind collaborating with other developers
    to collectively create software are general and can be applied to all sorts
    of environments, including private companies and proprietary code bases.


[black]: https://pypi.org/project/black/
[contribution-guide.org]: http://www.contribution-guide.org/
[creating a pr]: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request
[descriptive commit message]: https://chris.beams.io/posts/git-commit
[docstrings]: https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html
[first-contributions tutorial]: https://github.com/firstcontributions/first-contributions
[flake8]: https://flake8.pycqa.org/en/stable/
[git]: https://git-scm.com
[github web interface]: https://docs.github.com/en/github/managing-files-in-a-repository/managing-files-on-github/editing-files-in-your-repository
[github's code editor]: https://docs.github.com/en/github/managing-files-in-a-repository/managing-files-on-github/editing-files-in-your-repository
[github's fork and pull request workflow]: https://guides.github.com/activities/forking/
[google's python style guide]: https://google.github.io/styleguide/pyguide.html
[guide created by freecodecamp]: https://github.com/freecodecamp/how-to-contribute-to-open-source
[miniconda]: https://docs.conda.io/en/latest/miniconda.html
[myst]: https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html
[other kinds of contributions]: https://opensource.guide/how-to-contribute
[pre-commit]: https://pre-commit.com/
[pypi]: https://pypi.org/
[pyscaffold's contributor's guide]: https://pyscaffold.org/en/stable/contributing.html
[pytest can drop you]: https://docs.pytest.org/en/stable/how-to/failures.html
[python software foundation's code of conduct]: https://www.python.org/psf/conduct/
[sphinx]: https://www.sphinx-doc.org/en/master/
[tox]: https://tox.readthedocs.io/en/stable/
[virtual environment]: https://realpython.com/python-virtual-environments-a-primer/
[virtualenv]: https://virtualenv.pypa.io/en/stable/

[repository]: https://github.com/haxwithaxe/certdeploy
[issue tracker]: https://github.com/haxwithaxe/certdeploy/issues
