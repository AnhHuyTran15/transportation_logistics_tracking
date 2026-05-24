# Transportation & Logistics Tracking Analytics Platform

Enterprise-scale logistics analytics project focused on shipment tracking, operational diagnostics, ETA prediction, supplier performance evaluation, and transportation efficiency analysis using GPS logistics data.

This project combines logistics operations analysis, machine learning, and analytics engineering to identify the real operational causes behind poor delivery performance rather than relying on simple KPI reporting.

---

# Business Problem

The transportation operation showed severe delivery performance issues:

- Only ~38.5% of shipments were delivered on time
- Average delivery delay was comparable to actual transportation time
- GPS tracking data quality was inconsistent
- Long-haul shipment performance was highly unstable
- Supplier performance varied significantly across route types

The project aims to diagnose operational bottlenecks and generate actionable logistics recommendations using analytics and machine learning.

---

# Business Objectives

- Improve on-time delivery performance
- Identify operational causes of shipment delays
- Detect supplier capability mismatches
- Analyze long-haul transportation efficiency
- Support logistics KPI governance
- Build ETA prediction models
- Detect shipment risk and route anomalies
- Create scalable logistics analytics workflows

---

# Key Operational Insights

## 1. Distance Alone Does Not Explain Delays

Initial analysis showed a correlation between transportation distance and delivery delays. However, deeper diagnostics revealed that delays were also heavily influenced by:

- Vehicle type constraints
- Loading and unloading wait time
- Route complexity
- Supplier specialization
- Operational idle time
- Long-haul transportation handling

The project therefore focuses on operational causation rather than naive KPI correlation.

---

## 2. Supplier Performance Must Be Segmented

Supplier performance cannot be evaluated using overall averages alone.

The analysis recommends evaluating suppliers based on:
- Route type
- Distance segment
- Vehicle specialization
- Shipment complexity
- Delay severity
- Transportation cost efficiency

This avoids unfairly penalizing suppliers operating more difficult long-haul or containerized routes.

---

## 3. Waiting Time Is a Major Bottleneck

Shipment delays were often driven more by:
- dispatch waiting,
- warehouse handling,
- loading/unloading processes

than by actual vehicle movement.

This significantly changes how ETA and logistics KPIs should be interpreted.

---

# Dataset Overview

The project uses a transportation and logistics tracking dataset containing:

- GPS shipment tracking data
- Vehicle movement information
- ETA timestamps
- Supplier and customer details
- Transportation distance metrics
- Shipment lifecycle records

### Core Fields

- BookingID
- Shipment Type
- Vehicle Registration
- Origin / Destination
- GPS Coordinates
- Planned ETA
- Actual ETA
- Transportation Distance
- Vehicle Type
- Driver Information
- Supplier / Customer
- Trip Start / End Time

---

# Project Architecture

```text
Excel Dataset
      ↓
Data Cleaning Pipeline
      ↓
Feature Engineering
      ↓
Operational Analytics
      ↓
Machine Learning Models
      ↓
Dashboard & KPI Layer
      ↓
Business Recommendations
