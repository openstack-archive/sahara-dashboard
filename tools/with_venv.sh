#!/bin/bash
TOOLS_PATH=${TOOLS_PATH:-$(dirname $0)}
VENV_PATH=${VENV_PATH:-${TOOLS_PATH}}
VENV_DIR=${VENV_NAME:-/../.venv}
TOOLS=${TOOLS_PATH}
VENV=${VENV:-${VENV_PATH}/${VENV_DIR}}
# tools/tox_install.sh looks for VIRTUAL_ENV evrythign else looks for VENV
# so for now make them the same.
VIRTUAL_ENV=${VENV:-${VENV_PATH}/${VENV_DIR}}
. ${VENV}/bin/activate && "$@"
