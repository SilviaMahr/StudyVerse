import {Pipe, PipeTransform} from '@angular/core';

/**
 * Transforms raw text output (e.g., from an LLM) into renderable HTML.
 * Parses Markdown-style syntax for bold text (**...**) and bullet points (*),
 * and converts newlines to <br> tags.
 */
@Pipe({
    name: 'formatedText',
    standalone: true
  })
export class TextPipe implements PipeTransform {
  transform(value: string): string {
    if (!value) return value;

    let formattedText = value;


    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');

    formattedText = formattedText.replace(/^\*\s+/gm, '<br>&bull; ');

    formattedText = formattedText.replace(/\n/g, '<br>');

    return formattedText;
  }
}
