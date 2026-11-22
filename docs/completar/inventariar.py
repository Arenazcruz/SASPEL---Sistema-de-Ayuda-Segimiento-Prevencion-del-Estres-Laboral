"""Inventario estático reproducible. No importa/ejecuta el proyecto de referencia.

Solo fuentes en directorios explícitos; nunca .env, bases, uploads ni dependencias.
Uso: python docs/completar/inventariar.py [ruta SASPE-UF]
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = Path(sys.argv[1] if len(sys.argv)>1 else r'C:\laragon\www\Original\SASPE-UF')


def inventory(root, directories, suffixes):
    records=[]
    for directory in directories:
        folder=root/directory
        for path in sorted(folder.rglob('*')):
            if not path.is_file() or path.suffix not in suffixes or any(p in {'node_modules','__pycache__','.git','vendor'} for p in path.parts):
                continue
            raw=path.read_bytes()
            content=raw.decode('utf-8-sig', errors='replace')
            record={'path':path.relative_to(root).as_posix(), 'lines':len(content.splitlines()),
                    'sha256':hashlib.sha256(raw).hexdigest()}
            symbols=[]
            for line,text in enumerate(content.splitlines(),1):
                match=re.search(r'\b(?:class|def|function)\s+(\w+)',text)
                if match: symbols.append({'name':match.group(1),'line':line})
            if symbols:record['symbols']=symbols
            if path.suffix=='.php':
                record['tables']=sorted(set(re.findall(r"(?:table\(|\$table\s*=)\s*['\"]([^'\"]+)", content)))
                record['relationships']=sorted(set(re.findall(r'\b(belongsTo|hasMany|hasOne|belongsToMany)\(',content)))
                record['views']=sorted(set(re.findall(r"(?:view|loadView)\(['\"]([^'\"]+)",content)))
            records.append(record)
    return records


def main():
    data={'reference_root':str(REFERENCE), 'method':'Listado/hashes/símbolos estáticos; no prueba ejecución ni cobertura semántica total.',
          'reference':inventory(REFERENCE,['app','routes','config','resources','database/migrations','database/seeders','tests','bootstrap'],{'.php','.js','.css'}),
          'saspel':inventory(ROOT,['backend/src','backend/config','backend/tests','frontend/src','frontend/e2e'],{'.py','.ts','.html','.scss','.cjs'})}
    target=Path(__file__).with_name('inventario.json')
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({name:len(data[name]) for name in ['reference','saspel']}))


if __name__=='__main__':main()
