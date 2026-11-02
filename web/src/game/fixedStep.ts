export const SIMULATION_STEP = 1 / 60;

export class FixedStepClock {
  private accumulator = 0;

  reset() { this.accumulator = 0; }

  advance(elapsed: number, step: (dt: number) => void) {
    // Bound catch-up work after stalls; never feed a variable step to combat.
    this.accumulator += Math.max(0, Math.min(elapsed, 0.25));
    while (this.accumulator + 1e-10 >= SIMULATION_STEP) {
      this.accumulator -= SIMULATION_STEP;
      step(SIMULATION_STEP);
    }
  }
}
