# AI-Powered Multi-Robot Coordination in Dynamic Environments

Source: professor's brief.

## Goal
Coordinate a team of robots in a dynamic, obstacle-filled environment to deliver packages, avoid collisions
and re-route when obstacles or new tasks appear.

## Requirements
1. Multi-agent reinforcement learning so robots cooperate (Multi-Agent Deep Q-Learning or PPO).
2. Online path planning with dynamic obstacle updates (A* or RRT*).
3. Priority handling to resolve task conflicts dynamically.
4. Simulated environment with changing conditions (moving obstacles, new tasks).
5. Task allocation with a market-based (auction) algorithm using priority and robot availability.

## Input
Environment map (with dynamic obstacles), initial robot positions and tasks (delivery locations),
reward structure (task completion rewards, penalties for collisions/inefficiency).

## Output
Simulated execution of the robots completing their tasks.

## Metrics
Task completion time, collisions avoided, overall efficiency.

## Challenges
Reward design balancing efficiency, safety and collaboration; high-dimensional states; real-time changes;
scaling to larger teams and environments.

## VSI starter
`src/generator.py` creates grid maps with static and moving obstacles, robots and delivery tasks.
