// Fixed 2.1.296 fixture notice, from T-078 08c/screen-after-theme-01.
// This is emitted text after removing controls, not a reconstructed screenshot.
// Change only after a new notice has been read back and explicitly approved.
export const SECURITY_NOTICE_TEXT = `Security notes:
1. Claude can make mistakes.
   You'rresponsibleforClaud's actions and should always
review them, especially when running code.

2. Due to promptinjectionrisks,onlyuseitwithcodeyoutrust
Learn more: https://code.claude.com/docs/en/security

Press Enter to continue…`;

// Parse control syntax only. Do not classify content by words or patterns.
// Unsupported or incomplete escapes cannot authorize a key.
export function noticeText(raw: Uint8Array): string | undefined {
  const value=new TextDecoder("utf-8",{fatal:true,ignoreBOM:true}).decode(raw);
  let result="";
  for(let i=0;i<value.length;i++){
    const code=value.charCodeAt(i);
    if(code===27){
      i++;
      if(value[i]==="["){
        i++;
        while(i<value.length && value.charCodeAt(i)>=0x30 && value.charCodeAt(i)<=0x3f)i++;
        while(i<value.length && value.charCodeAt(i)>=0x20 && value.charCodeAt(i)<=0x2f)i++;
        if(i>=value.length || value.charCodeAt(i)<0x40 || value.charCodeAt(i)>0x7e)return undefined;
      }else{
        // The observed stream uses charset selection ESC ( B and ESC 7/8.
        while(i<value.length && value.charCodeAt(i)>=0x20 && value.charCodeAt(i)<=0x2f)i++;
        if(i>=value.length || value.charCodeAt(i)<0x30 || value.charCodeAt(i)>0x7e)return undefined;
        // Control strings are not present in this approved notice.
        if(["P","X","]","^","_"].includes(value[i]!))return undefined;
      }
    }else if(code===13){result+="\n";if(value.charCodeAt(i+1)===10)i++;}
    else if(code===10)result+="\n";
    else if(code>=0x80 && code<=0x9f)return undefined;
    else if(code>=32 && code!==127)result+=value[i];
  }
  // Remove only blank framing lines; retain every printable character and inner space.
  let first=0,last=result.length;
  while(result[first]==="\n")first++;
  while(last>first && result[last-1]==="\n")last--;
  return result.slice(first,last);
}
