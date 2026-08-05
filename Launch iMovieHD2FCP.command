#!/bin/zsh
set -e
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  echo "The .venv environment is missing."
  echo "Run the installation instructions first."
  read -k 1 "?Press any key to close..."
  exit 1
fi
source .venv/bin/activate
exec imoviehd2fcp-app
