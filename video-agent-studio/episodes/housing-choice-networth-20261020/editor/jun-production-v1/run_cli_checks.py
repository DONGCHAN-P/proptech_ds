"""Pinned 0.8.181 checker, using the existing verified implementation."""
import importlib.util, os, sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;EP=HERE.parents[1]
spec=importlib.util.spec_from_file_location('frozen_checks',EP/'editor/private-production-v3/run_cli_checks.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
old.HERE=HERE;old.OUT=EP/'outputs/jun-production-v1'
os.environ['DO_NOT_TRACK']='1'
if __name__=='__main__':sys.exit(old.main())
