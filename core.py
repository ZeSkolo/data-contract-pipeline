import csv, io, json, sqlite3, hashlib, re, math
from pathlib import Path

def validate(csv_text, contract):
    if not isinstance(csv_text, str) or len(csv_text.encode()) > 500000:
        raise ValueError('CSV is limited to 500 KB')
    if not isinstance(contract, dict) or not 1 <= len(contract) <= 30 or any((not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,40}', k) for k in contract)):
        raise ValueError('Provide 1–30 simple column names')
    for spec in contract.values():
        if spec.get('type') not in ['str', 'int', 'float']:
            raise ValueError('Contract types: str, int, float')
    reader = csv.DictReader(io.StringIO(csv_text))
    fields = reader.fieldnames
    if not fields or len(set(fields)) != len(fields) or set(fields) != set(contract):
        raise ValueError('CSV header must match the contract exactly')
    good = []
    bad = []
    seen = {k: set() for k, s in contract.items() if s.get('unique')}
    for line, row in enumerate(reader, 2):
        if line > 10001:
            raise ValueError('CSV is limited to 10000 data rows')
        result = {}
        errors = []
        if None in row or any((v is None for v in row.values())):
            errors.append('Malformed CSV row width')
        for key, spec in contract.items():
            raw = (row.get(key) or '').strip()
            if not raw:
                if spec.get('required'):
                    errors.append(key + ': required')
                result[key] = None
                continue
            try:
                val = {'str': str, 'int': int, 'float': float}[spec['type']](raw)
                if isinstance(val, float) and (not math.isfinite(val)):
                    raise ValueError('nonfinite')
                if 'min' in spec and val < spec['min']:
                    raise ValueError('below minimum')
                if 'max' in spec and val > spec['max']:
                    raise ValueError('above maximum')
                if 'allowed' in spec and val not in spec['allowed']:
                    raise ValueError('not allowed')
                if key in seen and val in seen[key]:
                    raise ValueError('duplicate')
                result[key] = val
            except (ValueError, TypeError):
                errors.append(key + ': invalid ' + spec['type'] + ' or constraint violation')
        if errors:
            bad.append({'line': line, 'errors': errors, 'row': row})
        else:
            good.append(result)
            for key in seen:
                if result[key] is not None:
                    seen[key].add(result[key])
    return (good, bad)

def run(p, db_path=None):
    text = p.get('csv', '')
    contract = p.get('contract', {})
    good, bad = validate(text, contract)
    canonical = json.dumps(contract, sort_keys=True)
    batch = hashlib.sha256((text + '\x00' + canonical).encode()).hexdigest()
    path = db_path or ':memory:'
    if path != ':memory:':
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path, timeout=10)
    try:
        c.executescript('CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY,contract TEXT,accepted INTEGER,rejected INTEGER); CREATE TABLE IF NOT EXISTS records(batch TEXT,row_number INTEGER,payload TEXT,PRIMARY KEY(batch,row_number)); CREATE TABLE IF NOT EXISTS quarantine(batch TEXT,row_number INTEGER,payload TEXT,PRIMARY KEY(batch,row_number));')
        exists = c.execute('SELECT 1 FROM batches WHERE id=?', (batch,)).fetchone()
        if not exists:
            with c:
                c.execute('INSERT INTO batches VALUES(?,?,?,?)', (batch, canonical, len(good), len(bad)))
                c.executemany('INSERT INTO records VALUES(?,?,?)', [(batch, i, json.dumps(r)) for i, r in enumerate(good)])
                c.executemany('INSERT INTO quarantine VALUES(?,?,?)', [(batch, r['line'], json.dumps(r)) for r in bad])
        count = c.execute('SELECT COUNT(*) FROM records WHERE batch=?', (batch,)).fetchone()[0]
        return {'batch_id': batch, 'already_ingested': bool(exists), 'accepted': len(good), 'rejected': len(bad), 'stored_rows': count, 'valid_preview': good[:5], 'quarantine': bad[:20]}
    finally:
        c.close()
