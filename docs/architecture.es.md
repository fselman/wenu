# Arquitectura de Wenu

## Introducción

Este documento describe los principios arquitectónicos de Wenu.

Su propósito no es describir cada clase o método, sino explicar las decisiones de diseño que dan forma al proyecto. La implementación podrá evolucionar con el tiempo, mientras que los principios aquí descritos deberían permanecer estables.

---

# Propósito

Wenu es una biblioteca de Python para la creación de cartas astronómicas.

Su objetivo principal es apoyar la comunicación de la astronomía mediante la educación, la divulgación científica, la publicación de material astronómico y la observación guiada del cielo.

La biblioteca está diseñada para producir cartas estáticas con calidad editorial y no para funcionar como un programa planetario interactivo.

---

# Principios de Diseño

Varios principios guían el desarrollo de Wenu.

## El cielo es lo primero

Los cálculos astronómicos deben ser independientes de la forma en que el cielo es representado.

Una misma escena celeste debe poder visualizarse mediante distintas proyecciones o sistemas de representación sin modificar el modelo astronómico.

## Separación de responsabilidades

Los distintos aspectos del problema se representan mediante componentes diferentes.

La astronomía, la geometría, las proyecciones y la representación gráfica deben mantenerse lo más independientes posible.

## Reproducibilidad

Una carta debe ser reproducible.

Dados el mismo observador, instante, opciones y datos de entrada, Wenu debe producir siempre la misma carta.

## Extensibilidad

La arquitectura debe facilitar la incorporación de

- nuevos objetos astronómicos
- nuevas estructuras celestes
- nuevas proyecciones
- nuevos estilos de representación

sin requerir modificaciones importantes del código existente.

---

# Modelo Conceptual

Wenu distingue cuatro niveles conceptuales.

## Observador

El observador define

- ubicación
- instante de observación
- sistemas de referencia

Todos los cálculos dependientes del observador se originan aquí.

---

## Objetos Astronómicos

Los objetos astronómicos representan entidades físicas.

Por ejemplo

- estrellas

Versiones futuras podrán incorporar

- planetas
- objetos de cielo profundo
- cometas
- asteroides

---

## Estructuras Celestes

Las estructuras celestes describen la geometría de la esfera celeste.

Por ejemplo

- líneas de constelaciones
- límites de constelaciones
- rejillas de coordenadas
- puntos de referencia celestes

A diferencia de los objetos astronómicos, estas estructuras no representan entidades físicas.

---

## Proyección

Las clases de proyección transforman coordenadas celestes en coordenadas planas.

La proyección no debe conocer qué objeto está representando.

Su única responsabilidad es transformar coordenadas.

---

## Representación Gráfica

La representación gráfica produce la salida visual.

No debe realizar cálculos astronómicos.

---

# Sistemas de Coordenadas

Wenu admite múltiples sistemas de coordenadas celestes.

Entre ellos

- horizontales
- ecuatoriales
- eclípticas
- galácticas

Nuevos sistemas podrán incorporarse sin modificar la arquitectura general.

---

# Datos

Los catálogos astronómicos se consideran recursos externos.

Siempre que sea posible, el software debe mantenerse independiente de un catálogo específico.

Actualmente se incluye soporte para el catálogo Hipparcos.

En el futuro podrán incorporarse otros catálogos.

---

# Desarrollo Futuro

La arquitectura está diseñada para permitir la incorporación de

- nuevas proyecciones
- isófotas de la Vía Láctea
- catálogos de cielo profundo
- múltiples sistemas de representación
- nuevos objetos astronómicos

sin cambios importantes en la arquitectura del sistema.
