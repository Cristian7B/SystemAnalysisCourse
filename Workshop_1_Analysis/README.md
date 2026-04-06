# Food Waste Reduction Mobile Application
*Connecting cafeterias & restaurants with community for surplus food redistribution*

## Overview

A geolocation-centered mobile application designed to reduce food waste in Bogotá, Colombia. The platform connects food donors (university cafeterias and restaurants) with recipients, prioritizing verified charitable organizations before allowing access to general users.

Recipients interact with an interactive map where food donations appear as location pins, allowing them to discover, filter, and claim available food nearby.

## Purpose

Reduce food waste while maximizing social impact by redistributing surplus food, prioritizing verified charities over general users.

**Key tracked metrics:**
- Kilograms of food redistributed
- Percentage of food delivered to charities
- Number of active users and donations

## Objectives

**General:** Develop a geolocation-based platform that facilitates surplus food redistribution while prioritizing charitable organizations.

**Specific:**
- Implement a backend capable of handling donation registration and priority logic
- Develop a REST API connecting frontend and backend services
- Create an interactive map interface to display nearby food donations
- Implement geospatial queries for efficient location-based discovery
- Track and measure the social impact of redistributed food
- Deploy the system using cloud services

## Stakeholders

| Role | Examples |
|------|----------|
| Donors | University cafeterias, restaurants, food service staff |
| Priority Recipients | Verified charities, community kitchens, student organizations |
| General Recipients | University students, local community members |
| Administrators | Project developers, university partners |
| External | Universities, local authorities, social organizations |

## Functional Requirements

1. Donors can create food posts with type, quantity, expiration time, location, and photos
2. Donations are displayed on an interactive map via geolocation
3. Recipients can search for nearby donations
4. Priority access system gives charities early access before general users
5. Users can claim available donations and receive pickup confirmations
6. Push notifications sent when food becomes available
7. Administrators can verify charitable organizations
8. Impact dashboard displays redistribution statistics

## Operating Environment

- **Geography:** Bogotá, Colombia — university areas and nearby restaurants
- **Connectivity:** Requires internet; PWA caching for intermittent connections
- **Regulation:** Compliant with Colombian data protection Law 1581 of 2012

**Known risks:** GPS accuracy, low user adoption, API rate limits, privacy concerns

## Academic Context

Developed for the **Systems Analysis course** at **Universidad Distrital Francisco José de Caldas**, applying concepts of system analysis, software architecture, web development, and geospatial systems.

## Related Files
- `Workshop_1.pdf`: Full report detailing the activity that was carried out.