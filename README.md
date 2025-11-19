# mcps

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

```
brew install uv
```

```
uv add --group notebook \
  jupyterlab \
  notebook \
  jupyter-server \
  ipykernel \
  ipython \
  ipywidgets \
  nbdime \
  jupyterlab-git \
  jupyterlab-github \
  jupyterlab-lsp \
  python-lsp-server[all] \
  jupyterlab-code-formatter \
  jupyter-ai \
  jupytext \
  nbconvert \
  papermill \
  jupysql
```

```
uv add --group test \
  pytest \
  pytest-sugar \
  pytest-emoji \
  pytest-html \
  pytest-icdiff \
  pytest-instafail \
  pytest-timeout \
  pytest-benchmark \
  pytest-cov \
  pytest-mock \
  pytest-xdist \
  hypothesis \
  pytest-randomly \
  syrupy \
  pytest-asyncio \
  allure-pytest
```