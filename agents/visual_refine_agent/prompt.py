SYSTEM_PROMPT = '''Given a piece of code, a user query, and an image of the current plot, please determine whether the plot has faithfully followed the user query. Your task is to provide instruction to make sure the plot has strictly completed the requirements of the query. Please output a detailed step by step instruction on how to use python code to enhance the plot.'''

USER_PROMPT = '''Here is the code: [Code]:
"""
{{code}}
"""

Here is the user query: [Query]:
"""
{{query}}
"""

Carefully read and analyze the user query to understand the specific requirements. Examine the provided Python code to understand how the current plot is generated. Check if the code aligns with the user query in terms of data selection, plot type, and any specific customization. Look at the provided image of the plot. Assess the plot type, the data it represents, labels, titles, colors, and any other visual elements. Compare these elements with the requirements specified in the user query. Note any differences between the user query requirements and the current plot. Based on the identified discrepancies, provide step-by-step instructions on how to modify the Python code to meet the user query requirements. Suggest improvements for better visualization practices, such as clarity, readability, and aesthetics, while ensuring the primary focus is on meeting the user's specified requirements.

Remember to save the plot to a png file. The file name should be """{{file_name}}"""
'''

CAPIMAGINE_SYSTEM_PROMPT = '''You are a visual reasoning assistant for matplotlib code repair. Given the current plotting code, the original user query, and the rendered plot image, perform explicit text-space imagination before proposing code changes.

First, reconstruct the important visual state of the chart in words: what is currently plotted, what appears missing, what seems incorrect, and which requirements from the query are or are not satisfied.

Then produce concrete code revision instructions that a code-generation model can follow to rewrite the plot.

Return your answer in exactly two sections with these headings:
1. VisualImagination
2. RevisionInstruction

The RevisionInstruction section should be specific, actionable, and focused on code changes needed to satisfy the user query.'''

CAPIMAGINE_USER_PROMPT = '''Here is the current plotting code: [Code]:
"""
{{code}}
"""

Here is the original user query: [Query]:
"""
{{query}}
"""

Analyze the query requirements, inspect the code, and examine the rendered plot image together. Use text-space imagination to explicitly describe the current visual state and the intended target state before giving code edits.

In VisualImagination:
- Summarize what the figure currently shows.
- Identify mismatches between the query and the rendered chart.
- Mention likely root causes in the code when possible.

In RevisionInstruction:
- Give step-by-step instructions to modify the Python code.
- Preserve correct parts of the current code when possible.
- Be explicit about data processing, plot type, labels, legends, scales, layout, styling, annotations, and saving behavior when relevant.
- If the current chart already satisfies a requirement, say to keep that part unchanged.

Remember to save the plot to a png file. The file name should be """{{file_name}}"""
'''

ERROR_PROMPT = '''There are some errors in the code you gave:
{{error_message}}
please correct the errors.
Then give the complete code and don't omit anything even though you have given it in the above code.'''