# Generador del banco de juegos

- `words*.txt`: diccionario `PALABRA|definición|dificultad` (1 a 3).
- `authors.py`: autores y obras para las claringrillas.
- `build.py`: genera `games.json` (`python3 build.py 60`, 60 juegos por dificultad).
- `app_template.html`: la app; `__DATA__` se reemplaza por el contenido de `games.json`.

## Banco v2 (difícil)

- `h1.txt` a `h5.txt`: diccionario difícil `PALABRA|definición|nivel` (1 Difícil, 2 Muy difícil, 3 Experto; 9 = descartada). Se escribe con tildes para separar bien las sílabas.
- `authors2.py`: autores y obras con tildes.
- `build2.py`: genera `games2.json` (`python3 build2.py 60`). Usa `gridlib.py` para armar las grillas.
- Para publicar: reemplazar `__DATA__` en `app_template.html` con `games2.json`, subir `VERSION` en la app y en `sw.js`.
