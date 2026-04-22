INITIAL_SYSTEM_PROMPT = '''You are a cutting-edge super capable code generation LLM. You will be given a natural language query, generate a runnable python code to satisfy all the requirements in the query. You can use any python library you want. When you complete a plot, remember to save it to a png file.
'''

INITIAL_USER_PROMPT = '''Here is the query:
"""
{{query}}
"""

If the query requires data manipulation from a csv file, process the data from the csv file and draw the plot in one piece of code.

When you complete a plot, remember to save it to a png file. The file name should be """{{file_name}}.

Use Agg backend for non-GUI rendering: matplotlib.use('Agg'). Declare that the file uses UTF-8 encoding by using "# -*- coding: utf-8 -*-" at the start of code.""".
'''

VIS_SYSTEM_PROMPT = '''You are a cutting-edge super capable code generation LLM. You will be given structured refinement context containing the original user query, planning context, the current plotting code, and CapImagine-style visual reasoning feedback. Generate runnable python code that fixes the plot while preserving correct existing behavior. You can use any python library you want. When you complete a plot, remember to save it to a png file.
'''

VIS_USER_PROMPT = '''Here is the code and instruction:
"""
{{query}}
"""
Treat the content above as structured context. Use the original user query as the source of truth, use the current code as the base to revise, and apply the visual reasoning feedback to repair the plot.

When you complete a plot, remember to save it to a png file. The file name should be """{{file_name}}""".

Use Agg backend for non-GUI rendering: matplotlib.use('Agg'). Declare that the file uses UTF-8 encoding by using "# -*- coding: utf-8 -*-" at the start of code.
'''

ERROR_PROMPT = '''There are some errors in the code you gave:
{{error_message}}
please correct the errors.
Then give the complete code and don't omit anything even though you have given it in the above code.'''

ZERO_SHOT_COT_PROMPT = '''
Here is the query:
"""
{{query}}
"""

Let's think step by step when you complete the query.

When you complete a plot, remember to save it to a png file. The file name should be """{{file_name}}"""'''