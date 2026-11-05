# Visor Gran Salón Ferretero 2026

Trazabilidad de captura vs cuota por distribuidor del GSF 2026 (5–7 nov, Corferias). Trade Marketing Pintuco.

- `index.html`: el visor (interactivo, lee los CSV de `data/` y se refresca cada 5 minutos).
- `.github/workflows/actualizar.yml`: GitHub Actions baja la captura del DataLake a los :15 de cada hora y publica `data/captura.csv` si cambió.
- El link del DataLake va en el secret `DATALAKE_URL` (Settings → Secrets and variables → Actions). No se publica cédula, teléfono, dirección ni NIT.
