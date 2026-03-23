# Abstracción de Puntos Clave

**Food Waste Reduction Platform**
**Autor:** Nicolás Rodríguez

---

## 1. Problema y Contexto

El proyecto aborda el alto nivel de desperdicio de alimentos en Colombia, especialmente en entornos urbanos donde cafeterías y restaurantes generan excedentes diarios. La falta de coordinación y el corto tiempo de vida útil de los alimentos dificultan su redistribución eficiente.

La solución propuesta consiste en una plataforma digital que conecta oferentes (restaurantes y cafeterías) con demandantes (estudiantes, comunidad y fundaciones), facilitando la redistribución en tiempo real.

---

## 2. Definición del Sistema

El sistema es una aplicación móvil orientada a la redistribución de excedentes alimentarios bajo las siguientes condiciones:

* Radio geográfico limitado a 3 km
* Operación en tiempo real
* Ventanas temporales estrictas (mismo día)
* Coordinación digital (sin transporte ni pagos)

---

## 3. Componentes Principales

El sistema se estructura en tres componentes clave:

* **Frontend:** Aplicación móvil para interacción de usuarios
* **Backend:** Gestión de lógica del sistema y datos
* **Motor de Matching:** Algoritmo de asignación basado en proximidad, prioridad y disponibilidad

---

## 4. Modelo Funcional (IPO)

### Entradas

* Información del excedente (tipo, cantidad, expiración)
* Datos de geolocalización
* Perfiles y preferencias de usuarios

### Procesos

* Publicación de excedentes
* Matching automático
* Notificación y aceptación
* Seguimiento y confirmación

### Salidas

* Redistribución efectiva de alimentos
* Métricas de impacto (kg recuperados, tasas de éxito)

---

## 5. Stakeholders

* **Usuarios:** estudiantes, comunidad, fundaciones
* **Proveedores:** restaurantes y cafeterías
* **Administradores:** gestión y monitoreo del sistema
* **Actores externos:** instituciones, autoridades, infraestructura tecnológica

---

## 6. Hallazgos Clave (Workshop 1)

* Alta dependencia de la geolocalización
* Sensibilidad a usuarios que no recogen (no-shows)
* Problemas de concurrencia en horas pico
* Riesgo de inequidad por proximidad
* Comportamientos emergentes (coordinación externa)

---

## 7. Requisitos de Diseño (Workshop 2)

* Matching en menos de 2 segundos
* Recuperación ≥ 80% del excedente
* Tasa de recogida ≥ 85%
* Notificaciones en menos de 5 segundos
* Soporte para múltiples usuarios concurrentes

---

## 8. Arquitectura del Sistema

* **Frontend:** React Native
* **Backend:** NestJS
* **Base de datos:** PostgreSQL + PostGIS
* **Caché y concurrencia:** Redis

Arquitectura modular con separación de responsabilidades y soporte para procesamiento en tiempo real.

---

## 9. Estrategia de Implementación

El desarrollo se divide en tres fases:

1. Infraestructura básica
2. Motor de matching y coordinación
3. Analítica, monitoreo y validación

---

## 10. Gestión de Riesgos

### Sensibilidades críticas

* Alta demanda simultánea
* Fallas en geolocalización

### Comportamientos emergentes

* Redes externas de usuarios
* Deserción de proveedores

### Dinámicas caóticas

* Cascadas por no-shows
* Saturación por notificaciones

**Soluciones:**

* Notificaciones escalonadas
* Reasignación automática
* Sistema de reputación

---

## 11. Monitoreo y KPIs

* Tasa de recuperación de alimentos
* Tiempo de respuesta del sistema
* Tasa de recogida exitosa
* Capacidad de concurrencia

---

## 12. Conclusión

La plataforma integra análisis y diseño para ofrecer una solución tecnológica viable al desperdicio de alimentos. Mediante el uso de geolocalización, algoritmos de asignación y monitoreo en tiempo real, se logra mejorar la eficiencia de redistribución y generar impacto social y ambiental positivo.

---
