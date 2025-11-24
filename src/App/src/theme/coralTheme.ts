import { 
  Theme,
  createLightTheme,
  createDarkTheme,
  BrandVariants,
  themeToTokensObject
} from '@fluentui/react-components';

// Brand colors matching the Figma design
const coralBrand: BrandVariants = {
  10: "#020305",
  20: "#111318",
  30: "#16202D",
  40: "#1B2C42",
  50: "#213A57",
  60: "#26486C",
  70: "#2B5681",
  80: "#306496",
  90: "#3572AB",
  100: "#3A80C0",
  110: "#4F8BC4",
  120: "#6496C8",
  130: "#79A1CC",
  140: "#8EACD0",
  150: "#A3B7D4",
  160: "#B8C2D8"
};

// Create light theme
export const coralLightTheme: Theme = {
  ...createLightTheme(coralBrand),
};

// Create dark theme with custom overrides for the Figma design
export const coralDarkTheme: Theme = {
  ...createDarkTheme(coralBrand),
  // Override specific colors to match Figma dark theme
  colorNeutralBackground1: "#1a1a1a",
  colorNeutralBackground2: "#262626",
  colorNeutralBackground3: "#333333",
  colorNeutralForeground1: "#ffffff",
  colorNeutralForeground2: "#e6e6e6",
  colorNeutralForeground3: "#cccccc",
  colorBrandBackground: "#3A80C0",
  colorBrandForeground1: "#ffffff",
  colorBrandForeground2: "#e6e6e6",
};

// Theme tokens for CSS custom properties
export const lightThemeTokens = themeToTokensObject(coralLightTheme);
export const darkThemeTokens = themeToTokensObject(coralDarkTheme);

// CSS custom properties for easy theme switching
export const createThemeStyles = (theme: Theme) => {
  const tokens = themeToTokensObject(theme);
  return Object.entries(tokens).reduce((acc, [key, value]) => {
    acc[`--${key}`] = value;
    return acc;
  }, {} as Record<string, string>);
};
