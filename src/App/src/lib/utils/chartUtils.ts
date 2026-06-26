export interface ParsedChartContent {
  title: string;
  points: Array<{ label: string; value: number }>;
}

export const parseChartContent = (content: string): ParsedChartContent | null => {
  try {
    const parsed = JSON.parse(content);
    if (!parsed || !Array.isArray(parsed.points)) {
      return null;
    }

    return {
      title: parsed.title || 'Chart',
      points: parsed.points,
    };
  } catch {
    return null;
  }
};
