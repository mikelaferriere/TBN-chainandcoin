# dSSN
Ambitious digital identification system


# Linux

## Configure direnv
Installing direnv will allow the python deps to be configured when entering
and exiting specific folders in the repo.

## Install direnv
```
$ sudo apt-get install direnv
```

## Setup direnv
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
```
$ exec "$SHELL"
```

### Install proper python version
```
$ pyenv install 3.8.5
```

The `.python-version` file will make sure that, when inside this repo, you are using 3.8.5
as long as you have configured everything laid out above.
