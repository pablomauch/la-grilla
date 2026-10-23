# Generador del banco de juegos

- `words*.txt`: diccionario `PALABRA|definición|dificultad` (1 a 3).
- `authors.py`: autores y obras para las claringrillas.
- `build.py`: genera `games.json` (`python3 build.py 60`, 60 juegos por dificultad).
- `app_template.html`: la app; `__DATA__` se reemplaza por el contenido de `games.json`.
