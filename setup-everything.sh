#! /bin/bash

dist-make geth all install-packages
dist-make geth all install-rust
dist-make geth all setup-data-pods --engine=home-runner
