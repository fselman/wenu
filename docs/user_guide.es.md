# Guía de Usuario de Wenu

## Introducción

Bienvenido a Wenu.

Esta guía presenta los conceptos básicos necesarios para crear cartas astronómicas con Wenu. Está dirigida a educadores, astrónomos aficionados, divulgadores científicos y cualquier persona interesada en producir cartas del cielo con calidad editorial.

El software se encuentra en desarrollo activo, por lo que esta guía crecerá junto con el proyecto.

---

# Instalación

Clonar el repositorio

```bash
git clone https://github.com/<usuario>/wenu.git
```

Instalar Wenu

```bash
pip install -e .
```

---

# Flujo Básico de Trabajo

Crear una carta con Wenu requiere cuatro pasos sencillos.

1. Crear un observador.
2. Crear una esfera celeste.
3. Agregar las capas astronómicas.
4. Dibujar la carta.

La mayoría de los ejemplos siguen esta misma secuencia.

---

# Ejemplo

```python
from wenu import Observer
from wenu.sky import CelestialSphere
from wenu import StereographicProjection

observer = Observer(...)

sky = CelestialSphere(observer)

sky.add_stars()
sky.add_constellations()

projection = StereographicProjection(...)

sky.draw(projection)
```

(La API puede evolucionar durante el desarrollo del proyecto.)

---

# Componentes Principales

Las clases más importantes son

- Observer
- CelestialSphere
- Stars
- Constellations
- Projection

En conjunto definen qué parte del cielo se observa, cómo se representa y cómo se dibuja.

---

# Aprendiendo Wenu

La mejor forma de aprender Wenu es estudiar los ejemplos incluidos con el proyecto.

Cada ejemplo muestra una tarea específica, como

- dibujar estrellas
- dibujar líneas de constelaciones
- representar rejillas de coordenadas
- construir un planisferio

---

# Limitaciones Actuales

Wenu se encuentra en desarrollo activo.

Algunas partes de la API pueden cambiar antes de la primera versión estable.

---

# Próximos Pasos

Las próximas versiones de esta guía incluirán

- sistemas de coordenadas
- proyecciones
- estilos de dibujo
- etiquetas
- capas personalizadas
- creación de cartas astronómicas
