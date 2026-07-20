# Wenu Architecture

## Introduction

This document describes the architectural principles behind Wenu.

The purpose of this document is not to describe every class or method, but to explain the design decisions that shape the project. Individual implementations may evolve over time, while the principles described here are intended to remain stable.

---

# Purpose

Wenu is a Python library for creating astronomical charts.

Its primary goal is to support astronomy communication through education, public outreach, publishing, and guided observation of the night sky.

The library is designed to produce publication-quality static charts rather than interactive planetarium software.

---

# Design Principles

Several principles guide the design of Wenu.

## The sky comes first

Astronomical calculations should be independent of how the sky is displayed.

The same celestial scene should be representable using different projections and rendering backends without changing the astronomical model.

## Separation of responsibilities

Different aspects of the problem are represented by different components.

Astronomy, geometry, projections, and rendering should remain as independent as possible.

## Reproducibility

A chart should be reproducible.

Given the same observer, time, options, and data, Wenu should always produce the same chart.

## Extensibility

The architecture should make it straightforward to add

- new astronomical objects
- new celestial structures
- new projections
- new rendering styles

without modifying existing code unnecessarily.

---

# Conceptual Model

Wenu distinguishes four conceptual layers.

## Observer

The observer defines

- location
- time
- reference frames

All observer-dependent calculations originate here.

---

## Astronomical Objects

Astronomical objects represent physical entities.

Examples include

- stars

Future versions may include

- planets
- deep-sky objects
- comets
- asteroids

---

## Celestial Structures

Celestial structures describe the geometry of the celestial sphere.

Examples include

- constellation lines
- constellation boundaries
- coordinate grids
- celestial reference points

Unlike astronomical objects, these structures are not physical entities.

---

## Projection

Projection classes transform celestial coordinates into planar coordinates.

The projection should not know what it is drawing.

It should only transform coordinates.

---

## Rendering

Rendering is responsible for producing graphical output.

Rendering should not perform astronomical calculations.

---

# Coordinate Systems

Wenu supports multiple celestial coordinate systems.

These include

- horizontal coordinates
- equatorial coordinates
- ecliptic coordinates
- Galactic coordinates

Future coordinate systems may be incorporated without changing the overall architecture.

---

# Data

Astronomical catalogues are treated as external data resources.

The software should remain independent of any particular catalogue whenever practical.

Current support includes the Hipparcos catalogue.

Additional catalogues may be incorporated in future releases.

---

# Future Directions

The architecture is intended to support future capabilities including

- additional projections
- Milky Way isophotes
- deep-sky catalogues
- multiple rendering backends
- additional celestial objects

without major architectural changes.
