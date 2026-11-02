export class TransitionTimers {
  private pending = new Set<ReturnType<typeof setTimeout>>();

  schedule(callback: () => void, delay: number) {
    const timer = setTimeout(() => {
      this.pending.delete(timer);
      callback();
    }, delay);
    this.pending.add(timer);
    return timer;
  }

  cancel() {
    for (const timer of this.pending) clearTimeout(timer);
    this.pending.clear();
  }
}
