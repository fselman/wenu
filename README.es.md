# Wenu

**Idioma:** [English](README.md) | Español

---

# Wenu

**Wenu** es una biblioteca de Python de código abierto para la creación de cartas astronómicas bellas, precisas y personalizables.

Fue desarrollada para apoyar la comunicación de la astronomía mediante la educación, la divulgación científica, la publicación de material astronómico y la observación guiada del cielo. Sus aplicaciones incluyen guías de observación, planisferios, material educativo, libros, artículos, presentaciones y cursos de astronomía.

A diferencia de los programas planetario interactivos, Wenu está orientada a la creación de cartas estáticas cuyo aspecto puede controlarse completamente y reproducirse de manera consistente.

*Wenu* significa **cielo** en mapudungun, la lengua del pueblo mapuche del sur de Sudamérica.

## Estado del proyecto

**Wenu** se encuentra actualmente en una etapa activa de diseño y desarrollo.
La arquitectura v0.5 está implementada: tipos de carta, estilos, modos de
salida, políticas de detalle y leyendas se resuelven mediante un único flujo
de composición y exportación.

Este repositorio es temporalmente público con el único propósito de facilitar
la revisión de la arquitectura, la discusión técnica y la colaboración durante
el desarrollo del proyecto.

**Wenu no constituye aún una versión de código abierto (Open Source).**

Todos los derechos sobre el software y su documentación están reservados por
el titular de los derechos de autor.  No se concede autorización para usar, copiar, modificar, redisistribuir o crear obras derivadas sin la autorización previa y por escrito del titular de los derechos de autor.

Una vez finalizado el desarrollo del software y del material educativo asociado,
el proyecto podrá ser publicado bajo una licencia de código abierto apropiada.

Para más información, consulte el archivo **LICENSE**.

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
- estilos atlas y cartoon
- modos de impresión/papel y presentación
- políticas de detalle locales a cada exportación
- leyendas integradas de objetos, magnitudes estelares y contexto
- cartas regionales, de cielo completo, circumpolares y binoculares
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

## Arquitectura v0.5

La carta se describe mediante elecciones independientes:

- el tipo de carta controla la proyección, el encuadre y el límite;
- el estilo (`atlas` o `cartoon`) controla la apariencia;
- el modo (`print`/`paper` o `presentation`) adapta el medio de salida;
- la política de detalle controla la selección astronómica;
- la política de leyendas controla los elementos informativos.

Todas las combinaciones utilizan la misma geometría, proyección, preparación
y representación gráfica.

---

## Documentación

La documentación adicional se encuentra en el directorio `docs/`. La
referencia vigente es `docs/developer/implementation_reference.md`; la
arquitectura implementada se describe en
`docs/developer/target_architecture_v0.5.md`.

---

## Atribución de Datos

La información sobre los catálogos astronómicos y otros conjuntos de datos utilizados por Wenu se encuentra en `DATA_ATTRIBUTION.md`.

---

## Licencia

La licencia será especificada antes de la primera versión pública.

---

## Agradecimientos

Wenu se apoya en el extraordinario trabajo de la comunidad de software astronómico de código abierto, en particular de los desarrolladores de Astropy, Skyfield y Matplotlib, así como en los catálogos astronómicos puestos a disposición de la comunidad científica.
