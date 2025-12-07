While answering the user's prompt, any paragraph/action that you'll write/perform to the user due to specific instructions mentioned here should be explicitly stated in the chat before the start of the paragraph/action, so the user is aware of it. Example: "Based on your custom instructions, ...".

Whenever I end my prompt with this string: "!s", then save that prompt exactly as it is to this file: docs\\lld\\dev_prompts_for_coding_ansari_whatsapp.md (search for it if you can't find it). 

If I send a short prompt only with flags including this "!s", then save the prompt that I sent just before this one. 

When saving my prompts to this file: docs\\lld\\dev_prompts_for_coding_ansari_whatsapp.md, take into consideration these style-guides: (1) If I'm opening up a new discussion/idea/task-category, then create a new `# Chat {NUMBER} - {MAIN TOPIC THAT YOU INFER}` header then under that `## Message 1`, then append the prompt under that. (2) Else (i.e., same conversation topic), then append it under a `## Message {NUMBER}` header.
