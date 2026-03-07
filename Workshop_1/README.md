# Food Waste Redistribution Platform
*Connecting cafeterias & restaurants with community for surplus food redistribution*
## Overview

The **Food Waste Redistribution Platform** is a geolocation-centered web application designed to reduce food waste, inicially in Bogotá, Colombia. The platform connects food donors such as university cafeterias and restaurants with recipients, prioritizing verified charitable organizations before allowing access to general users.

The system focuses on improving food redistribution efficiency through geographic visualization and a priority-based access system.

Users interact with an interactive map where food donations appear as location pins. Recipients can discover, filter, and claim available food near them.


# System Purpose

The main purpose of the platform is to **reduce food waste while increasing social impact** by prioritizing food redistribution to verified charities before opening access to general users.

The system also allows tracking impact metrics such as:

- kilograms of food redistributed
- percentage of food delivered to charities
- number of active users and donations


# Objectives

## General Objective

Develop a geolocation-based web platform that facilitates the redistribution of surplus food while prioritizing charitable organizations.

## Specific Objectives

- Implement a backend capable of handling donation registration and priority logic.
- Develop a REST API to connect frontend and backend services.
- Create an interactive map interface to display nearby food donations.
- Implement geospatial queries for efficient location-based discovery.
- Track and measure the social impact of redistributed food.
- Deploy the system using cloud services.

# Stakeholders

The system involves several stakeholders:

### Donors
- University cafeterias
- Restaurants
- Food service staff

### Priority Recipients
- Verified charitable organizations
- Community kitchens
- Student organizations

### General Recipients
- University students
- Local community members

### Trusted Collectors
Users who frequently collect donations responsibly and receive trust badges.

### Platform Administrators
Project developers and university partners responsible for maintaining the system.

### External Stakeholders
- Universities
- Local authorities
- Social organizations interested in food redistribution.


# Necessities and Functional Requirements

The system must:

1. Allow donors to create food donation posts.
2. Allow donors to include information such as:
   - food type
   - quantity
   - expiration time
   - location
   - photos.
3. Display donations on an interactive map using geolocation.
4. Allow recipients to search for nearby donations.
5. Implement a **priority access system** where charities have early access.
6. Allow users to claim available food donations.
7. Generate pickup confirmations (for example QR codes).
8. Send notifications when food becomes available.
9. Allow administrators to verify charity organizations.
10. Provide an impact dashboard showing redistributed food statistics.


# Operating Environment

### Geographic Context
The system is designed to operate primarily in **Bogotá**, focusing on university areas and nearby restaurants.

### Connectivity
The platform requires internet connectivity but may use **PWA caching** to improve user experience during intermittent connections.

### Regulatory Context
The system must respect Colombian data protection laws, including **Law 1581 of 2012**, especially regarding user geolocation data.

### Risks

- GPS accuracy issues
- Low user adoption
- API usage limits
- Privacy concerns

# Academic Context

This project is developed as part of the **Systems Analysis course** at **Universidad Distrital Francisco José de Caldas**, Bogotá, Colombia.

The project focuses on applying concepts of:

- system analysis
- software architecture
- web development
- geospatial systems
- project collaboration
