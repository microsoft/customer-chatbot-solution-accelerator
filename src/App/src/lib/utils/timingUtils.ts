export const debounce = <T extends (...args: any[]) => void>(fn: T, delayMs = 250) => {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn(...args);
    }, delayMs);
  };
};

export const throttle = <T extends (...args: any[]) => void>(fn: T, intervalMs = 250) => {
  let isThrottled = false;
  let trailingArgs: Parameters<T> | null = null;

  const runTrailing = () => {
    if (!trailingArgs) {
      isThrottled = false;
      return;
    }

    const args = trailingArgs;
    trailingArgs = null;
    fn(...args);
    setTimeout(runTrailing, intervalMs);
  };

  return (...args: Parameters<T>) => {
    if (isThrottled) {
      trailingArgs = args;
      return;
    }

    fn(...args);
    isThrottled = true;
    setTimeout(runTrailing, intervalMs);
  };
};
