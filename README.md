# Blockchain
We dont have a name for our blockchain or coin yet.


# Linux

## Install dependencies
```
$ sudo apt-get update
$ sudo apt-get install -y make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl git direnv
```

## Setup direnv
Setting up direnv will allow the python deps to be configured when entering
and exiting specific folders in the repo.

Add
```
eval "$(direnv hook bash)"
```
to the end of `~/.bashrc` file


## Configure and initialize python environment

### Clone Pyenv
```
$ git clone https://github.com/pyenv/pyenv.git ~/.pyenv
```

### Add PYENV envvar to .bash_profile
```
$ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
$ echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
```
### Add pyenv init to shell
```
$ echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n  eval "$(pyenv init -)"\nfi' >> ~/.bash_profile
```

### Restart shell
If using WSL the following won't work. Close and reopen the WSL window instead.
```
$ exec "$SHELL"
```

### Install proper python versions
```
$ pyenv install 2.7.15 # WSL only
$ pyenv install 3.8.5
```

The `.python-version` file will make sure that, when inside this repo, you are using 2.7.15
for `python` and 3.8.5 for `python3` as long as you have configured everything laid out above.


# Install pre-commit hooks

Installing the pre-commit hooks will run a series of linters and run the tests so that the changes are
tested nicely before they get either to `master` or in a PR.

```
make install-pre-commit
```

# Running the blockchain!
To run and interact with the blockchain, see [BLOCKCHAIN.md](https://github.com/mikelaferriere/TBN-chainandcoin/blob/master/docs/BLOCKCHAIN.md)
