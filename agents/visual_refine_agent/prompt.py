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

def build_capimagine_system_prompt(explicit_imagination=True):
    if explicit_imagination:
        return '''You are a visual reasoning assistant for matplotlib code repair. Given the current plotting code, the original user query, and the rendered plot image, perform explicit text-space imagination before proposing code changes.

First, reconstruct the important visual state of the chart in words: what is currently plotted, what appears missing, what seems incorrect, and which requirements from the query are or are not satisfied.

Then produce concrete code revision instructions that a code-generation model can follow to rewrite the plot.

Return your answer in exactly two sections with these headings:
1. VisualImagination
2. RevisionInstruction

The RevisionInstruction section should be specific, actionable, and focused on code changes needed to satisfy the user query.'''
    return '''You are a visual reasoning assistant for matplotlib code repair. Given the current plotting code, the original user query, and the rendered plot image, analyze the current chart and propose concrete code changes that a code-generation model can follow to rewrite the plot.

Return your answer in exactly one section with this heading:
1. RevisionInstruction

The RevisionInstruction section should be specific, actionable, and focused on code changes needed to satisfy the user query.'''


def build_capimagine_user_prompt(
    *,
    explicit_imagination=True,
    include_root_cause=True,
    include_revision_checklist=True,
    include_preserve_correct_parts=True,
):
    prompt = '''Here is the current plotting code: [Code]:
"""
{{code}}
"""

Here is the original user query: [Query]:
"""
{{query}}
"""

Analyze the query requirements, inspect the code, and examine the rendered plot image together.'''
    if explicit_imagination:
        prompt += '''

Use text-space imagination to explicitly describe the current visual state and the intended target state before giving code edits.

In VisualImagination:
- Summarize what the figure currently shows.
- Identify mismatches between the query and the rendered chart.'''
        if include_root_cause:
            prompt += '''
- Mention likely root causes in the code when possible.'''
    else:
        prompt += '''

Directly produce revision guidance grounded in the rendered chart and the original query.'''

    prompt += '''

In RevisionInstruction:
- Give step-by-step instructions to modify the Python code.
'''
    if include_preserve_correct_parts:
        prompt += '''- Preserve correct parts of the current code when possible.
'''
    if include_revision_checklist:
        prompt += '''- Be explicit about data processing, plot type, labels, legends, scales, layout, styling, annotations, and saving behavior when relevant.
'''
    if include_preserve_correct_parts:
        prompt += '''- If the current chart already satisfies a requirement, say to keep that part unchanged.
'''

    prompt += '''

Remember to save the plot to a png file. The file name should be """{{file_name}}"""
'''
    return prompt


CAPIMAGINE_SYSTEM_PROMPT = build_capimagine_system_prompt(explicit_imagination=True)
CAPIMAGINE_USER_PROMPT = build_capimagine_user_prompt(
    explicit_imagination=True,
    include_root_cause=True,
    include_revision_checklist=True,
    include_preserve_correct_parts=True,
)
CAP_FULL_SYSTEM_PROMPT = CAPIMAGINE_SYSTEM_PROMPT
CAP_FULL_USER_PROMPT = CAPIMAGINE_USER_PROMPT
CAP_NO_IMAGINATION_SYSTEM_PROMPT = build_capimagine_system_prompt(explicit_imagination=False)
CAP_NO_IMAGINATION_USER_PROMPT = build_capimagine_user_prompt(
    explicit_imagination=False,
    include_root_cause=True,
    include_revision_checklist=True,
    include_preserve_correct_parts=True,
)
CAP_NO_ROOT_CAUSE_SYSTEM_PROMPT = CAPIMAGINE_SYSTEM_PROMPT
CAP_NO_ROOT_CAUSE_USER_PROMPT = build_capimagine_user_prompt(
    explicit_imagination=True,
    include_root_cause=False,
    include_revision_checklist=True,
    include_preserve_correct_parts=True,
)
CAP_NO_REVISION_CHECKLIST_SYSTEM_PROMPT = CAPIMAGINE_SYSTEM_PROMPT
CAP_NO_REVISION_CHECKLIST_USER_PROMPT = build_capimagine_user_prompt(
    explicit_imagination=True,
    include_root_cause=True,
    include_revision_checklist=False,
    include_preserve_correct_parts=True,
)
CAP_NO_PRESERVE_CORRECT_PARTS_SYSTEM_PROMPT = CAPIMAGINE_SYSTEM_PROMPT
CAP_NO_PRESERVE_CORRECT_PARTS_USER_PROMPT = build_capimagine_user_prompt(
    explicit_imagination=True,
    include_root_cause=True,
    include_revision_checklist=True,
    include_preserve_correct_parts=False,
)

ERROR_PROMPT = '''There are some errors in the code you gave:
{{error_message}}
please correct the errors.
Then give the complete code and don't omit anything even though you have given it in the above code.'''