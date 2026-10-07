"""Package the verified reports, current source code and exact input CSVs."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPORTS = {
    'variant_1_sedentary_pulse': 'Group16_01_Sedentary_Time_and_Pulse',
    'variant_2_age_sex_haemoglobin': 'Group16_02_Age_Sex_and_Haemoglobin',
    'variant_3_arm_body_weight': 'Group16_03_Arm_Circumference_and_Body_Weight',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    numerical = json.loads((ROOT / 'outputs/numerical_validation.json').read_text(encoding='utf-8'))
    documents = json.loads((ROOT / 'outputs/report_validation.json').read_text(encoding='utf-8'))
    figures = json.loads((ROOT / 'outputs/figure_checks.json').read_text(encoding='utf-8'))
    assert numerical['passed'] == 51
    assert [r['variant'] for r in numerical['reports']] == list(REPORTS)
    assert [r['variant'] for r in documents] == list(REPORTS)
    assert [r['variant'] for r in figures] == list(REPORTS)
    sources = json.loads((ROOT / 'source_files.json').read_text(encoding='utf-8'))
    files = [ROOT / name for name in sources]
    dest = ROOT / 'deliverables/group16'
    dest.mkdir(parents=True, exist_ok=True)
    for index, (name, base) in enumerate(REPORTS.items()):
        folder = ROOT / 'reports/group16' / name
        report = documents[index]
        assert report['group_number'] == 16 and report['document_status'] == 'final'
        assert report['no_placeholders'] and report['no_build_instructions_in_report']
        assert digest(folder / 'results.json') == report['result_sha256'] == numerical['reports'][index]['result_sha256']
        for extension in ['pdf', 'docx']:
            target = dest / f'{base}.{extension}'
            shutil.copy2(folder / f'report.{extension}', target)
            assert digest(target) == digest(folder / f'report.{extension}')
            files.append(target)
        files.extend(p for p in folder.rglob('*') if p.is_file() and not p.name.startswith('preview_'))
    for name in ['NHANES_BME_student - NHANES_BME_student.csv', 'NHANES_BME_codebook - NHANES_BME_codebook.csv']:
        files.append(ROOT / 'data' / name)
    for name in ['numerical_validation.json', 'report_validation.json', 'figure_checks.json']:
        files.append(ROOT / 'outputs' / name)
    reproduction = ROOT / 'outputs/reproduction_validation.json'
    if reproduction.exists():
        files.append(reproduction)
    files = sorted(set(files))
    assert all(p.is_file() and p.resolve().is_relative_to(ROOT.resolve()) for p in files)
    manifest = {p.relative_to(ROOT).as_posix(): digest(p) for p in files}
    archive = ROOT / 'NHANES_Group16_Final_Reports.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, path.relative_to(ROOT).as_posix())
        z.writestr('SHA256_manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and len(z.namelist()) == len(manifest) + 1
        assert all(hashlib.sha256(z.read(name)).hexdigest() == expected for name, expected in manifest.items())
        assert not any('/.git/' in name or '__pycache__' in name or name.endswith('.log') for name in z.namelist())
    result = {'archive': archive.name, 'bytes': archive.stat().st_size, 'files': len(manifest) + 1,
              'sha256': digest(archive), 'all_archive_hashes_verified': True,
              'deliverables': [p.relative_to(ROOT).as_posix() for p in sorted(dest.iterdir())]}
    (ROOT / 'outputs/package_validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
