#!/bin/bash
export A2A_OPERATOR_CREDENTIAL=/private/tmp/t190/operator.json
exec node /Users/luckye/Documents/Code/a2a/workbench/src/gates/cli.ts --state /private/tmp/t190/state "$@"
