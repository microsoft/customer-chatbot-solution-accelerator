import { DependencyList, RefObject, useEffect } from 'react';

export const useAutoScroll = (
  targetRef: RefObject<HTMLElement | null>,
  deps: DependencyList,
  behavior: ScrollBehavior = 'smooth',
) => {
  useEffect(() => {
    targetRef.current?.scrollIntoView({ behavior });
  }, deps);
};
