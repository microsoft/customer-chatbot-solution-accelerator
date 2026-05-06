/**
 * Text cleaning utilities for TTS — strips markdown, URLs, and code before speaking.
 */

/** Strip markdown formatting, URLs, and code blocks from text for natural speech. */
export const cleanTextForSpeech = (text: string): string => {
  return text
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')   // [text](url) → text
    .replace(/https?:\/\/[^\s)]+/g, '')          // bare URLs
    .replace(/\*\*([^*]+)\*\*/g, '$1')            // **bold** → bold
    .replace(/\*([^*]+)\*/g, '$1')                // *italic* → italic
    .replace(/#{1,6}\s*/g, '')                     // ### headings
    .replace(/```[\s\S]*?```/g, '')               // code blocks
    .replace(/`([^`]+)`/g, '$1')                   // inline code
    .replace(/\n{2,}/g, '. ')                      // double newlines → pause
    .replace(/\s{2,}/g, ' ')                       // collapse whitespace
    .trim();
};