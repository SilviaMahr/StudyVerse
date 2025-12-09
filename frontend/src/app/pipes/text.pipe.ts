import {Pipe, PipeTransform} from '@angular/core';

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
