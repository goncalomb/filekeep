# filekeep

Verify integrity and track file changes.

## Setup

Start using right now:

```bash
pipx install git+https://github.com/goncalomb/filekeep.git
filekeep -h
```

### Other commands using `pipx`

```bash
# install
pipx install git+https://github.com/goncalomb/filekeep.git

# install for development (editable)
git clone https://github.com/goncalomb/filekeep.git
pipx install -e ./filekeep

# uninstall
pipx uninstall filekeep
```

### Other commands using `uv`

```bash
# install (on a venv)
uv venv
uv pip install git+https://github.com/goncalomb/filekeep.git
source .venv/bin/activate

# install for development
git clone https://github.com/goncalomb/filekeep.git
cd filekeep
uv sync
source .venv/bin/activate
```

## License

filekeep is released under the terms of the MIT License. See [LICENSE.txt](LICENSE.txt) for details.
