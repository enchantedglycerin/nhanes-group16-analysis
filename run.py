"""Reproduce the Group 16 analyses and, optionally, the complete reports."""
import argparse
import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
INPUTS = {
    'NHANES_BME_student - NHANES_BME_student.csv':
        'ee2bd4d6bccb4860967fbb1cf7d4af510a5ebfddd4911fe6d0cd155738cd8c09',
    'NHANES_BME_codebook - NHANES_BME_codebook.csv':
        '1653074b1b5c721ce74511da21fe658c0ff62caa000ed980f1ee051af911920b',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis-only', action='store_true',
                        help='Run statistical analysis and numerical validation only.')
    args = parser.parse_args()
    if sys.version_info < (3, 11) or sys.flags.optimize:
        raise SystemExit('Use Python 3.11 or later, without -O: validation requires assertions.')
    for name, expected in INPUTS.items():
        path = ROOT / 'data' / name
        if not path.is_file():
            raise SystemExit(f'Missing input: data/{name}. See data/README.md.')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f'Input hash mismatch: {name}. Use the unchanged supplied CSV.')
    modules = ['numpy', 'mpmath']
    steps = ['analyze.py', 'verify_analysis.py']
    if not args.analysis_only:
        modules += ['wx', 'pymupdf', 'PIL']
        if shutil.which('node') is None:
            raise SystemExit('Install Node.js with Intl.Segmenter support to build Thai reports.')
        font_dir = Path(os.environ.get('THAI_FONT_DIR', 'C:/Windows/Fonts'))
        if not all((font_dir / name).is_file() for name in ['tahoma.ttf', 'tahomabd.ttf']):
            raise SystemExit('Tahoma fonts are required. Set THAI_FONT_DIR to their directory.')
        steps += ['make_figures.py', 'build_reports.py', 'check_reports.py', 'package_reports.py']
    missing = [module for module in modules if importlib.util.find_spec(module) is None]
    if missing:
        requirement = 'requirements-analysis.txt' if args.analysis_only else 'requirements.txt'
        raise SystemExit(f'Missing packages: {", ".join(missing)}. Install {requirement}.')
    (ROOT / 'outputs').mkdir(exist_ok=True)
    for step in steps:
        print(f'Running tools/{step}', flush=True)
        result = subprocess.run([sys.executable, str(ROOT / 'tools' / step)], cwd=ROOT,
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        (ROOT / 'outputs' / (Path(step).stem + '.log')).write_text(
            result.stdout + result.stderr, encoding='utf-8')
        if result.stdout:
            print(result.stdout, end='', flush=True)
        if result.returncode:
            print(result.stderr, file=sys.stderr, flush=True)
            raise SystemExit(result.returncode)
    print('Analysis and numerical validation complete.' if args.analysis_only
          else 'Reports, validation outputs and ZIP are ready.', flush=True)


if __name__ == '__main__':
    main()
