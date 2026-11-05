"""Baja el consolidado de vendedores del GSF 2026 desde el datalake y genera
data/captura.csv limpio para el visor: hora de Bogotá, números como números,
línea y negocio de la maestra, sin cédula, teléfono, dirección ni NIT."""
import csv, io, json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(RAIZ, 'data')
url = re.sub(r'\s+', '', os.environ.get('DATALAKE_URL') or '')  # quita espacios o saltos de línea pegados por error
if not url:
    sys.exit('Falta el secret DATALAKE_URL')

with urllib.request.urlopen(url, timeout=60) as r:
    texto = r.read().decode('utf-8-sig')

maestra = {}
with open(os.path.join(DATA, 'maestra_productos.csv'), encoding='utf-8') as f:
    for m in csv.DictReader(f):
        maestra[m['sku'].strip()] = m

NEGOCIO = {'DECORATIVO': 'Decorativo', 'CONSTRUCCION': 'Construcción', 'HERRAMIENTAS PARA PINTAR': 'Herramientas'}
num = lambda s: int(float(re.sub(r'[^0-9.]', '', (s or '').replace(',', '')) or 0))

filas, total_fuente, ids = [], 0, {}  # ids: NIT -> código anónimo, el NIT no se publica
for r in csv.DictReader(io.StringIO(texto), delimiter=';'):
    if not (r.get('fecha_pedido') or '').strip():
        continue
    total_fuente += num(r['precio_total'])
    bog = datetime.strptime(r['fecha_pedido'].strip()[:19], '%Y-%m-%d %H:%M:%S') - timedelta(hours=5)
    sku = r['sku_producto'].strip()
    m = maestra.get(sku, {})
    negocio = 'Señalización' if m.get('familia') == 'SENALIZACION' else NEGOCIO.get(m.get('grupo', ''), 'Sin negocio')
    filas.append({
        'fecha_hora': bog.strftime('%Y-%m-%d %H:%M:%S'),
        'dia': bog.strftime('%Y-%m-%d'),
        'hora': bog.hour,
        'distribuidor': r['razon_social'].strip(),
        'vendedor': r['vendedor_nombre'].strip().title(),
        'cliente': r['nombre_cliente'].strip(),
        'cliente_id': ids.setdefault(re.sub(r'\D', '', r['nit_cliente']), 'C%03d' % (len(ids) + 1)),
        'ciudad': r['ciudad_cliente'].strip().title(),
        'sku': sku,
        'producto': re.sub(r'^\d+-', '', r['nombre_producto'].strip()),
        'marca': m.get('linea') or 'SIN LÍNEA EN MAESTRA',
        'negocio': negocio,
        'cantidad': num(r['cantidad_producto']),
        'valor': num(r['precio_total']),
    })

assert sum(f['valor'] for f in filas) == total_fuente, 'La suma no cuadra con la fuente'
campos = list(filas[0].keys()) if filas else ['fecha_hora']
with open(os.path.join(DATA, 'captura.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=campos)
    w.writeheader(); w.writerows(filas)

meta = {
    'lineas': len(filas),
    'valor': total_fuente,
    'ultimo_pedido': max((f['fecha_hora'] for f in filas), default=''),
    'revisado': datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=-5))).strftime('%Y-%m-%d %H:%M'),
}
with open(os.path.join(DATA, 'meta.json'), 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False)
print(meta)
