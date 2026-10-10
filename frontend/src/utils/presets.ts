import type { NavigationConfig } from '../types/navigation';

export interface PresetScenario {
  id: string;
  name: string;
  description: string;
  icon: string;
  config: NavigationConfig;
}

export const PRESET_SCENARIOS: PresetScenario[] = [
  {
    id: 'standard_warehouse',
    name: 'Warehouse Benchmark',
    description: 'Standard warehouse grid with dynamic crossing obstacles triggering online replanning.',
    icon: '🏭',
    config: {
      environment: {
        width: 20,
        height: 20,
        start: [1, 1],
        goal: [18, 18],
        static_obstacles: [
          [5, 5], [5, 6], [5, 7], [5, 8], [5, 9],
          [10, 10], [10, 11], [10, 12], [10, 13], [10, 14],
          [15, 5], [15, 6], [15, 7], [15, 8], [15, 9],
        ],
      },
      simulation: {
        max_steps: 100,
        dynamic_obstacles: [
          {
            id: 'dyn_forklift_1',
            initial_position: [4, 4],
            trajectory: [[4, 4], [4, 5], [4, 6], [4, 7], [4, 6], [4, 5]],
          },
          {
            id: 'dyn_patrol_2',
            initial_position: [15, 14],
            trajectory: [[15, 14], [14, 14], [13, 14], [12, 14], [13, 14], [14, 14]],
          },
        ],
      },
      planning: {
        allow_diagonal: false,
        heuristic: 'manhattan',
      },
      control: {
        step_size: 1,
        replan_on_block: true,
      },
    },
  },
  {
    id: 'narrow_chokepoint',
    name: 'Narrow Corridor Pinch Point',
    description: 'A wall forcing a single doorway that gets dynamically obstructed, forcing real-time detours.',
    icon: '🚪',
    config: {
      environment: {
        width: 20,
        height: 20,
        start: [2, 10],
        goal: [17, 10],
        static_obstacles: [
          [9, 0], [9, 1], [9, 2], [9, 3], [9, 4], [9, 5], [9, 6], [9, 7], [9, 8], [9, 9],
          [9, 11], [9, 12], [9, 13], [9, 14], [9, 15], [9, 16], [9, 17], [9, 18], [9, 19],
        ],
      },
      simulation: {
        max_steps: 100,
        dynamic_obstacles: [
          {
            id: 'door_shutter_1',
            initial_position: [9, 10],
            trajectory: [[9, 10], [9, 10], [9, 10], [9, 10], [9, 10], [8, 10], [7, 10]],
          },
        ],
      },
      planning: {
        allow_diagonal: true,
        heuristic: 'euclidean',
      },
      control: {
        step_size: 1,
        replan_on_block: true,
      },
    },
  },
  {
    id: 'dense_maze',
    name: 'Dense Labyrinth',
    description: 'Complex maze with dynamic guards patrolling corridors.',
    icon: '🧩',
    config: {
      environment: {
        width: 22,
        height: 22,
        start: [1, 1],
        goal: [20, 20],
        static_obstacles: [
          // Wall 1
          [3, 1], [3, 2], [3, 3], [3, 4], [3, 5], [3, 6], [3, 7], [3, 8], [3, 9], [3, 10],
          // Wall 2
          [7, 11], [7, 12], [7, 13], [7, 14], [7, 15], [7, 16], [7, 17], [7, 18], [7, 19], [7, 20],
          // Horizontal dividers
          [7, 5], [8, 5], [9, 5], [10, 5], [11, 5], [12, 5],
          [11, 10], [12, 10], [13, 10], [14, 10], [15, 10], [16, 10],
          [15, 15], [16, 15], [17, 15], [18, 15],
        ],
      },
      simulation: {
        max_steps: 150,
        dynamic_obstacles: [
          {
            id: 'sentinel_a',
            initial_position: [6, 8],
            trajectory: [[6, 8], [7, 8], [8, 8], [9, 8], [8, 8], [7, 8]],
          },
          {
            id: 'sentinel_b',
            initial_position: [14, 12],
            trajectory: [[14, 12], [14, 13], [14, 14], [14, 13]],
          },
        ],
      },
      planning: {
        allow_diagonal: true,
        heuristic: 'euclidean',
      },
      control: {
        step_size: 1,
        replan_on_block: true,
      },
    },
  },
  {
    id: 'crossing_interceptors',
    name: 'Crossing Interceptors',
    description: 'Multiple dynamic obstacles crossing paths perpendicularly to test safety & proactive rerouting.',
    icon: '⚡',
    config: {
      environment: {
        width: 20,
        height: 20,
        start: [1, 10],
        goal: [18, 10],
        static_obstacles: [
          [5, 4], [5, 16],
          [10, 4], [10, 16],
          [15, 4], [15, 16],
        ],
      },
      simulation: {
        max_steps: 80,
        dynamic_obstacles: [
          {
            id: 'interceptor_1',
            initial_position: [6, 1],
            trajectory: [[6, 1], [6, 4], [6, 7], [6, 10], [6, 13], [6, 16], [6, 19], [6, 16], [6, 13], [6, 10]],
          },
          {
            id: 'interceptor_2',
            initial_position: [12, 19],
            trajectory: [[12, 19], [12, 16], [12, 13], [12, 10], [12, 7], [12, 4], [12, 1], [12, 4], [12, 7], [12, 10]],
          },
        ],
      },
      planning: {
        allow_diagonal: false,
        heuristic: 'manhattan',
      },
      control: {
        step_size: 1,
        replan_on_block: true,
      },
    },
  },
];
