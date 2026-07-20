# Wenu

**Idioma:** [English](README.md) | Español

---

# Wenu

**Wenu** es una biblioteca de Python de código abierto para la creación de cartas astronómicas bellas, precisas y personalizables.

Fue desarrollada para apoyar la comunicación de la astronomía mediante la educación, la divulgación científica, la publicación de material astronómico y la observación guiada del cielo. Sus aplicaciones incluyen guías de observación, planisferios, material educativo, libros, artículos, presentaciones y cursos de astronomía.

A diferencia de los programas planetario interactivos, Wenu está orientada a la creación de cartas estáticas cuyo aspecto puede controlarse completamente y reproducirse de manera consistente.

*Wenu* significa **cielo** en mapudungun, la lengua del pueblo mapuche del sur de Sudamérica.

---

## Características

La versión actual incluye

- cálculos del cielo dependientes del observador
- proyección estereográfica
- cartas de cielo completo y de regiones específicas
- catálogo estelar Hipparcos
- líneas de constelaciones
- límites oficiales de las constelaciones de la IAU
- rejillas de coordenadas ecuatoriales, eclípticas y galácticas
- puntos de referencia celestes
- estilos de dibujo personalizables
- composición por capas
- representación gráfica mediante Matplotlib

---

## Filosofía de Diseño

Wenu se basa en tres ideas sencillas.

- **El cielo es lo primero.** Los cálculos astronómicos deben ser independientes de la forma en que el cielo se representa.

- **Las cartas deben tener calidad editorial.** Cada elemento de una carta debe contribuir a una comunicación clara y eficaz.

- **La reproducibilidad es importante.** Un mismo programa debe producir siempre la misma carta.

Este diseño permite crear desde un planisferio sencillo hasta cartas detalladas de constelaciones individuales, manteniendo una interfaz de programación consistente.

---

## Arquitectura

El paquete está organizado en un pequeño número de componentes principales.

### Observer

Representa el lugar y el instante de observación y realiza los cálculos astronómicos dependientes del observador.

### CelestialSphere

Representa el cielo que será dibujado. Administra estrellas, constelaciones, rejillas de coordenadas, límites y otras estructuras celestes.

### Projection

Las clases de proyección transforman coordenadas celestes en coordenadas planas aptas para su representación gráfica.

La implementación actual proporciona una proyección estereográfica adecuada tanto para planisferios como para cartas regionales.

### Rendering

La representación gráfica se realiza mediante Matplotlib, permitiendo exportar cartas con calidad de publicación.

---

## Instalación

Clonar el repositorio

```bash
git clone https://github.com/<usuario>/wenu.git
```

Instalar el paquete

```bash
pip install -e .
```

---

## Dependencias

Actualmente Wenu depende de

- Astropy
- Skyfield
- Matplotlib
- NumPy
- Pandas

---

## Estado del Proyecto

Wenu se encuentra en desarrollo activo.

Aunque su arquitectura principal está estabilizándose, la API pública todavía puede cambiar antes de la primera versión oficial.

---

## Hoja de Ruta

Entre los desarrollos previstos se incluyen

- nuevas proyecciones cartográficas
- colores estelares
- isófotas de la Vía Láctea
- catálogos de objetos de cielo profundo
- nuevas opciones de representación gráfica
- pruebas automáticas
- ampliación de la documentación

---

## Documentación

La documentación adicional se encuentra en el directorio `docs/`.

---

## Atribución de Datos

La información sobre los catálogos astronómicos y otros conjuntos de datos utilizados por Wenu se encuentra en `DATA_ATTRIBUTION.md`.

---

## Licencia

La licencia será especificada antes de la primera versión pública.

---

## Agradecimientos

Wenu se apoya en el extraordinario trabajo de la comunidad de software astronómico de código abierto, en particular de los desarrolladores de Astropy, Skyfield y Matplotlib, así como en los catálogos astronómicos puestos a disposición de la comunidad científica.
