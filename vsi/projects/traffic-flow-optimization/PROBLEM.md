# Traffic Flow Optimization in a City Grid Using Dijkstra and A*

Source: professor's brief.

## Goal
A city is a weighted grid: nodes are intersections, edges are roads whose weights are traffic delays.
Find the fastest route between intersections, considering real-time traffic updates and congestion.

## Requirements
1. Implement Dijkstra and A* for pathfinding.
2. Account for traffic updates by adjusting edge weights dynamically.

## Algorithm
Dijkstra for static pathfinding; A* for dynamic situations, with heuristic adjustments based on traffic data.

## Input
City grid with intersections and roads; dynamic congestion data.

## Output
Shortest route and estimated travel time under real-time traffic.

## Suggested analysis (to score well)
Correctness of Dijkstra/A* (admissible heuristic), complexity O((V+E) log V), nodes expanded by each,
effect of congestion updates, scaling with grid size.

## VSI starter
`src/generator.py` builds city grids with travel delays and random congestion updates.
