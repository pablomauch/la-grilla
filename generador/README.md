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

## Banco v3 (cero repetición)

- Diccionario: `h1-h5`, `r1` (definiciones nuevas para palabras de la v1) y `n1-n10`. Unas 5400 palabras.
- `build3.py`: genera `games3.json`. Cada palabra, definición y autor/obra se usa una sola vez; los juegos se arman por turnos (tipo y nivel) hasta agotar el diccionario.
- Para una tanda nueva sin repetir: agregar palabras nuevas a un archivo `n11.txt` (y sumarlo en `build3.py`), y excluir las ya usadas.
