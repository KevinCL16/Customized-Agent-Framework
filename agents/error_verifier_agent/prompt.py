DEPRECATE_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Determine whether the code has any errors in its data analysis process
2. Determine which **error type** from the list below is in the provided code. 
3. **Explain** the error, including:
   - **Explanation**: Explain why this is an error and what issues it may cause.
   - **Expected Outcome**: Explain how this error will affect the data analysis results, such as misleading outcomes, degraded performance, or incorrect interpretations.

### List of Common Error Types:
1. **Algorithm Choice Mismatch**: Using a regression algorithm for classification tasks or a classification algorithm for regression tasks.
2. **Evaluation Metric Mismatch**: Using inappropriate metrics to evaluate model performance.
3. **Handling Categorical Features Incorrectly**: Misusing or incorrectly encoding categorical features.
4. **Data Normalization Issue**: Not normalizing numerical features before using algorithms that are sensitive to feature scales.
5. **Random State Consistency**: Not setting a consistent `random_state`, resulting in non-reproducible results.
6. **Incorrect Interpretation of Output**: Misinterpreting the output of a regression model for classification or not converting outputs to an appropriate form.
7. **Data Leakage**: Applying data transformations (such as scaling or encoding) before splitting into training and testing sets, leading to overly optimistic model performance.
8. **Ignoring Data Imbalance**: Not accounting for class imbalance in the dataset, resulting in misleading performance metrics.
9. **Poor Outcome Visualization**: Inadequate or misleading visualizations that make it difficult to understand model behavior or errors.
10. **Feature Correlation Issues**: Ignoring correlations between features, leading to multicollinearity problems in linear models.

### Output Format:
```json
{
  "is_error": "True or False",
  "error_explanation": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
}
'''

DEPRECATE_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


### Your Task: 
1. Check if the code contains any data analysis errors.
2. If you identify an error, determine which error type it corresponds to from the list below.
3. Explain the error, including:
   - **Explanation**: Why this is an error and what issues it may cause.
   - **Expected Outcome**: How this error will affect the analysis results, such as producing misleading conclusions or performance degradation.

### List of Common Error Types:
1. **Algorithm Choice Mismatch**: Using regression algorithms for classification tasks, or vice versa.
2. **Evaluation Metric Mismatch**: Inappropriate metrics to measure performance.
3. **Handling Categorical Features Incorrectly**: Issues in encoding or misusing categorical data.
4. **Data Normalization Issue**: Lack of feature scaling when required by specific algorithms.
5. **Random State Consistency**: Not ensuring reproducible results through a fixed random state.
6. **Incorrect Interpretation of Output**: Misinterpreting model outputs or predictions.
7. **Data Leakage**: Applying transformations before the train-test split.
8. **Ignoring Data Imbalance**: Failing to address class imbalance in datasets.
9. **Poor Outcome Visualization**: Inadequate or misleading visualizations.
10. **Feature Correlation Issues**: Ignoring correlations that could cause multicollinearity problems.


Please follow the output format below:

```json
{
  "is_error": "True or False",
  "error_explanation": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
}
```  
'''

ERROR_ERASE_PROMPT = '''You are given the following incorrect data analysis code.

### Incorrect Data Analysis Code:
{{code}}

There some places in the code where errors are explicitly stated.

Your task is to only remove the explicit description of the errors in the code (mainly in comments), but leave the error code unaltered.
'''

ERROR_TYPE_PROMPT = [
    "1. **Algorithm Choice Mismatch**: Using a regression algorithm for classification tasks or a classification algorithm for regression tasks.",
    "2. **Evaluation Metric Mismatch**: Using inappropriate metrics to evaluate model performance.",
    "3. **Handling Categorical Features Incorrectly**: Misusing or incorrectly encoding categorical features.",
    "4. **Data Normalization Issue**: Not normalizing numerical features before using algorithms that are sensitive to feature scales.",
    "5. **Random State Consistency**: Not setting a consistent `random_state`, resulting in non-reproducible results.",
    "6. **Incorrect Interpretation of Output**: Misinterpreting the output of a regression model for classification or not converting outputs to an appropriate form.",
    "7. **Data Leakage**: Applying data transformations (such as scaling or encoding) before splitting into training and testing sets, leading to overly optimistic model performance.",
    "8. **Ignoring Data Imbalance**: Not accounting for class imbalance in the dataset, resulting in misleading performance metrics.",
    "9. **Poor Outcome Visualization**: Inadequate or misleading visualizations that make it difficult to understand model behavior or errors.",
    "10. **Feature Correlation Issues**: Ignoring correlations between features, leading to multicollinearity problems in linear models."]


ERROR_VERIFIER_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process. **If the code faithfully followed seemingly wrong data analysis practices explicitly stated in the Question. Deem it as correct.**
2. **Explain** any errors found, including:
   - **Explanation**: Explain why this is an error and what issues it may cause.
   - **Expected Outcome**: Explain how this error will affect the data analysis results, such as misleading outcomes, degraded performance, or incorrect interpretations.

### Output Format:
```json
{
    "is_error": "true/false",
    "error_explanation": [{
        "error_type": "Describe the type of error",
        "explanation": "Detailed explanation of why this is an error and its impact",
        "expected_outcome": "How this error will affect model performance or results",
        "suggestions": "Specific suggestions for fixing the error"
    },
    {
        "error_type": "Another error type if multiple errors exist",
        "explanation": "Explanation for the second error",
        "expected_outcome": "Expected outcome for the second error",
        "suggestions": "Suggestions for fixing the second error"
    }]
}
```

Important Notes:
1. Always provide the output in the exact JSON format specified above
2. Set "is_error" to "false" if no errors are found
3. If "is_error" is "false", provide an empty array for error_explanation
4. If "is_error" is "true", include all identified errors in the error_explanation array
5. Consider the original query requirements carefully - if the code follows the query's explicit requirements, even if they seem incorrect, consider it correct
'''

ERROR_VERIFIER_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query (Read the Question carefully, if the code followed the requirements in the question, even if you feel that incorrect data analysis practice were used, deem it as correct):
{{query}}


### Data Analysis Code:
{{code}}


### Your Task: 
1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process. **If the code faithfully followed seemingly wrong data analysis practices explicitly stated in the original query. Deem it as correct.**
2. Provide your analysis in the specified JSON format with detailed explanations for each error found.

Please provide your analysis in the following format:

```json
{
    "is_error": "true/false",
    "error_explanation": [{
        "error_type": "Describe the type of error",
        "explanation": "Detailed explanation of why this is an error and its impact",
        "expected_outcome": "How this error will affect model performance or results",
        "suggestions": "Specific suggestions for fixing the error"
    }]
}
```

Note: If multiple errors are found, include multiple objects in the error_explanation array.
If no errors are found, set "is_error" to "false" and provide an empty array for error_explanation.
'''

ERROR_EVAL_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process.
2. **Explain** any errors found, including:
   - **Explanation**: Explain why these are errors and what issues they may cause.
   - **Expected Outcome**: Explain how these errors will affect the data analysis results, such as misleading outcomes, degraded performance, or incorrect interpretations.

### Output Format:
```json
{
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why these are errors and their impact on the analysis",
    "expected_outcome": "Explain how these errors will affect model performance, accuracy, or interpretability"
}
```

Output only ONE json dict.
'''

ERROR_EVAL_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


### Your Task: 
1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process.
2. Provide your analysis in the specified JSON format with detailed explanations for each error found.

Please provide your analysis in the following format:

```json
{
    "error_type": "Specify the type of injected errors",
    "explanation": "Describe why these are errors and their impact on the analysis",
    "expected_outcome": "Explain how these errors will affect model performance, accuracy, or interpretability"
}
```

Output only ONE json dict.
'''

EVAL_PROMPT = '''You are given the following two analysis on whether a piece of code contains errors or not.

### Analysis One:
{{ground_truth}}

### Analysis Two:
{{eval_dict}}

Determine if Analysis Two points out the exact same errors as Analysis One:

- If Analysis Two identifies all the same errors (type, location, and severity) as Analysis One, score it **1**.
- If Analysis Two has partial overlap by identifying some errors correctly but misses or adds other errors, score it **0.5**.
- If Analysis Two fails to identify any errors present in Analysis One, score it **0**.

Your output format should be: SCORE[1/0.5/0]
'''

RUBBER_DUCK_EVAL_PROMPT_OLD = '''You are provided with the following analyses of errors in a piece of code:

### Ground Truth:
```json
{{ground_truth}}
```

### LLM Output:
```json
{{eval_dict}}
```


Evaluate the LLM Output against the Ground Truth separately for cause_line, effect_line, and error_message based on the following criteria:

### Evaluation Criteria:
1. Cause Line Matching (cause_line_score):
  - Score 1: The cause_line in the LLM Output exactly matches the cause_line in the Ground Truth.
  - Score 0: The cause_line in the LLM Output does not match the Ground Truth.
2. Effect Line Matching (effect_line_score):
  - Score 1: The effect_line in the LLM Output exactly matches the effect_line in the Ground Truth.
  - Score 0: The effect_line in the LLM Output does not match the Ground Truth.
3. Error Message Matching (error_message_score):
  - You will be given the full traceback and error message in the ground truth for reference, however, when giving score, only compare the error description against the LLM output, the LLM is not supposed to output the full traceback stack.
  - Score 1: The error_message in the LLM Output exactly matches the error_message (except the full traceback) in the Ground Truth.
  - Score 0.5: The error_message in the LLM Output is partially correct (e.g., captures the general idea but misses specific details or phrasing).
  - Score 0: The error_message in the LLM Output does not match the Ground Truth at all.

### Output Format:
```json 
{
    "cause_line_score": 1/0,
    "effect_line_score": 1/0,
    "error_message_score": 1/0.5/0
}
```
'''

RUBBER_DUCK_EVAL_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).
Output Format:
```json 
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output only ONE json dict in your response.
'''

RUBBER_DUCK_EVAL_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).
  
### Output Format:
```json 
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output only ONE json dict in your response.
'''

RUBBER_DUCK_EVAL_PROMPT = '''You are provided with the following analyses of errors in a piece of code:

### Ground Truth:
```json
{{ground_truth}}
```

### LLM Output:
```json
{{eval_dict}}
```

### Evaluation Task:  
Evaluate the LLM's output for code error analysis against the Ground Truth (GT) in three dimensions: **cause line**, **effect line**, and **error message**.


### Evaluation Criteria:  
1. **Cause Line Matching** (`cause_line_score`):  
   - **Score 1**: The `cause_line` in the LLM Output **exactly matches** the `cause_line` in the Ground Truth.  
   - **Score 0**: Otherwise.  

2. **Effect Line Matching** (`effect_line_score`):  
   - **Score 1**: The `effect_line` in the LLM Output **exactly matches** the `effect_line` in the Ground Truth.  
   - **Score 0**: Otherwise.  

3. **Error Type Matching** (`error_type_score`):  
   - **Score 1**: The error type in the LLM Output **exactly matches** the error type in the Ground Truth.
   - **Score 0**: Otherwise.

4. **Error Message Matching** (`error_message_score`):  
   - **Evaluation Scope**: Compare only the **error description** (ignore the full traceback or stack details).  
   - **Scoring Method**:  
     - **1.0**: The error description in the LLM Output **exactly matches** the GT (including all key details).  
     - **0.75**: The error description is **mostly correct** but lacks minor details.  
     - **0.5**: The error description is **partially correct** but contains vague or incomplete information.  
     - **0.25**: The error description is **only loosely related** to the GT.  
     - **0.0**: The error description is **completely irrelevant or incorrect**.  
   - **Justification**: The LLM must provide a brief justification for the score.  
     ```  
     "error_message_eval_reason": "<Specific justification for the score>"  
     ```  

---

### Output Format:  
```json  
{  
    "cause_line_score": 1/0,  
    "effect_line_score": 1/0,
    "error_type_score": 1/0,  
    "error_message_score": 0.0/0.25/0.5/0.75/1.0,  
    "error_message_eval_reason": "Scoring justification (in English)"  
}  
```
'''

MULTI_RUBBER_DUCK_EVAL_PROMPT = '''You are provided with a Ground Truth error analysis (as a list of *independent* error dictionaries) and an LLM Output error analysis (for a *single* detected error).

### Ground Truth Errors (List of *Independent* Error Dictionaries):
```json
{{ground_truth}}
```
*Important*: Each dictionary in `ground_truth_errors` represents a *specific and independent* error in the code. The information within each dictionary (cause line, effect line, error message, error type) is linked and describes a *single, distinct* error instance. These dictionaries are *not interchangeable*.

### LLM Output Error:
```json
{{llm_output_error}}
```

### Evaluation Task:
Evaluate the LLM's output error analysis against the Ground Truth errors.  Determine if the LLM's detected error *holistically matches* any *specific error instance* described in the Ground Truth Errors list.  A holistic match means the cause line, effect line, error message, *and error type* from the LLM's output should correspond to the *same* error instance in the Ground Truth.

### Evaluation Criteria:

For the LLM Output Error, you must compare it against *each* error dictionary in the `ground_truth_errors` list to find a *holistic match*.  A score is awarded only if the LLM's output aligns with a *single, specific error instance* from the Ground Truth.  Simply matching error types or messages across different Ground Truth error dictionaries is *not* sufficient for a high score.

1.  **Cause Line Matching** (`cause_line_score`):
    -   **Score 1**: The `cause_line` in the LLM Output **exactly matches** the `cause_line` of **at least one *specific* error instance** (i.e., one dictionary) in the `ground_truth_errors` list.
    -   **Score 0**: Otherwise.

2.  **Effect Line Matching** (`effect_line_score`):
    -   **Score 1**: The `effect_line` in the LLM Output **exactly matches** the `effect_line` of the **same *specific* error instance** (the same dictionary in `ground_truth_errors` that you matched the cause line with in step 1).
    -   **Score 0**: Otherwise.

3.  **Error Type Matching** (`error_type_score`):
    -   **Score 1**: The `error_type` in the LLM Output **exactly matches** the `error_type` of the **same *specific* error instance** (the same dictionary used in steps 1 and 2).
    -   **Score 0**: Otherwise.

4.  **Error Message Matching** (`error_message_score`):
    -   **Evaluation Scope**: Compare only the **error description**.
    -   **Scoring Method**:
        -   **1.0**: The error description in the LLM Output **exactly matches** the `error_message` of the **same *specific* error instance** (the same dictionary used in steps 1, 2, and 3).
        -   **0.75**: The error description is **mostly correct** compared to the `error_message` of the **same *specific* error instance**, but lacks minor details or has slight variations.
        -   **0.5**: The error description is **partially correct** but contains vague or incomplete information compared to the `error_message` of the **same *specific* error instance**.
        -   **0.25**: The error description is **only loosely related** to the `error_message` of the **same *specific* error instance**.
        -   **0.0**: The error description is **completely irrelevant or incorrect** compared to the `error_message` of **the same *specific* error instance** and all other error messages in `ground_truth_errors`.
    -   **Justification**: Provide a *detailed* justification for the score. *Crucially, explicitly identify which specific error instance from `ground_truth_errors` (e.g., "Ground Truth Error 1", "Ground Truth Error 2", etc.) you are comparing against and explain why you assigned the score, especially if it's not a perfect score.* If there's no holistic match with *any* error instance in `ground_truth_errors`, state that clearly in the justification.
        ```
        "error_message_eval_reason": "<Detailed justification, e.g., 'Holistically matched Ground Truth Error 1 perfectly.', 'Cause and Effect lines and Error Type matched Ground Truth Error 2, but error message was partially correct - hence 0.5 score.', 'No holistic match found with any error instance in Ground Truth Errors list.'>"
        ```

---

### Output Format:
```json
{
    "cause_line_score": 1/0,
    "effect_line_score": 1/0,
    "error_type_score": 1/0,
    "error_message_score": 0.0/0.25/0.5/0.75/1.0,
    "error_message_eval_reason": "Detailed scoring justification (in English)"
}
```
'''

MULTI_RUBBER_DUCK_EVAL_SYSTEM_PROMPT = '''You will be provided with a data analysis code. Your task is to:

1. Read the code carefully and identify all logic errors injected into the code. There will be two or more logic errors in the code.
2. For each logic error you identify:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error or where the incorrect behavior is observed.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback). Focus on the *type* of error and the *reason* if possible from the output.

Output Format:
```json
[
    {
        "cause_line": "Specify the exact line of code causing error 1",
        "effect_line": "Specify the exact line of code where error 1 is triggered",
        "error_message": "Concise error message for error 1"
    },
    {
        "cause_line": "Specify the exact line of code causing error 2",
        "effect_line": "Specify the exact line of code where error 2 is triggered",
        "error_message": "Concise error message for error 2"
    },
    ... (and so on for all identified errors)
]```
There will be more than one error in the code. BUT output only ONE json block in your response.
'''

MULTI_RUBBER_DUCK_EVAL_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


1. Read the code carefully and identify all logic errors injected into the code. There will be two or more logic errors in the code.
2. For each logic error you identify:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error or where the incorrect behavior is observed.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback). Focus on the *type* of error and the *reason* if possible from the output.

Output Format:
```json
[
    {
        "cause_line": "Specify the exact line of code causing error 1",
        "effect_line": "Specify the exact line of code where error 1 is triggered",
        "error_message": "Concise error message for error 1"
    },
    {
        "cause_line": "Specify the exact line of code causing error 2",
        "effect_line": "Specify the exact line of code where error 2 is triggered",
        "error_message": "Concise error message for error 2"
    },
    ... (and so on for all identified errors)
]```
There will be more than one error in the code. BUT output only ONE json block in your response.
'''

RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).

First, think step-by-step about the code and identify the logic error. Explain your reasoning process clearly.

After presenting your CoT reasoning, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**CoT Output:**
Your step-by-step reasoning process here

**JSON Output:**
```json
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output your CoT reasoning first, followed by the one ONLY json output in your response.'''

RUBBER_DUCK_ZERO_COT_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


You will be provided with an original query and a data analysis code. Your task is to:

1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).

First, think step-by-step about the code and identify the logic error. Explain your reasoning process clearly.

After presenting your CoT reasoning, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**CoT Output:**
Your step-by-step reasoning process here

**JSON Output:**
```json
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output your CoT reasoning first, followed by the one ONLY json output in your response.
'''

MULTI_RUBBER_DUCK_ZERO_COT_SYSTEM_PROMPT = '''You will be provided with a data analysis code. Your task is to:

1. Read the code carefully and identify all logic errors injected into the code. There will be two or more logic errors in the code.
2. For each logic error you identify:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error or where the incorrect behavior is observed.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback). Focus on the *type* of error and the *reason* if possible from the output.

First, think step-by-step through the code and identify each logic error.  Explain your reasoning process for each error clearly.

After presenting your CoT reasoning for all identified errors, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**Chain of Thought (CoT) Output:**
Your step-by-step reasoning process for error 1 here, 
Your step-by-step reasoning process for error 2 here
... (and so on for all identified errors)

**JSON Output:**
```json
[
    {
        "cause_line": "Specify the exact line of code causing error 1",
        "effect_line": "Specify the exact line of code where error 1 is triggered",
        "error_message": "Concise error message for error 1"
    },
    {
        "cause_line": "Specify the exact line of code causing error 2",
        "effect_line": "Specify the exact line of code where error 2 is triggered",
        "error_message": "Concise error message for error 2"
    },
    ... (and so on for all identified errors)
]```
There will be more than one error in the code. Output your CoT reasoning first, followed by only ONE json block in your response.'''

MULTI_RUBBER_DUCK_ZERO_COT_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


You will be provided with a data analysis code. Your task is to:

1. Read the code carefully and identify all logic errors injected into the code. There will be two or more logic errors in the code.
2. For each logic error you identify:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error or where the incorrect behavior is observed.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback). Focus on the *type* of error and the *reason* if possible from the output.

First, think step-by-step through the code and identify each logic error.  Explain your reasoning process for each error clearly.

After presenting your CoT reasoning for all identified errors, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**Chain of Thought (CoT) Output:**
Your step-by-step reasoning process for error 1 here, 
Your step-by-step reasoning process for error 2 here
... (and so on for all identified errors)

**JSON Output:**
```json
[
    {
        "cause_line": "Specify the exact line of code causing error 1",
        "effect_line": "Specify the exact line of code where error 1 is triggered",
        "error_message": "Concise error message for error 1"
    },
    {
        "cause_line": "Specify the exact line of code causing error 2",
        "effect_line": "Specify the exact line of code where error 2 is triggered",
        "error_message": "Concise error message for error 2"
    },
    ... (and so on for all identified errors)
]```
There will be more than one error in the code. Output your CoT reasoning first, followed by only ONE json block in your response.
'''

RUBBER_DUCK_ONE_COT_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1.  Read the question carefully and identify if there is a logic error injected into the code that will cause the interpreter to throw an error.
2.  For the logic error, provide a step-by-step "Chain of Thought" (CoT) reasoning that explains how you identified the error and its consequences.
3.  After the reasoning, provide the answer in a specific JSON format.

First, think step-by-step about the code. Explain your reasoning for how the logical error leads to an interpreter error. After presenting your CoT reasoning, output the answer in the JSON format.

Here is an example of the desired thinking process and output format:

### Example Query:
Apply machine learning techniques to predict the employment level in March 2020 based on the data from March 2019. Split the dataset into a 70-30 split for training and testing sets, train a simple linear regression model on the training set, and evaluate its performance on the testing set using Mean Squared Error as the evaluation metric. Additionally, visualize the outcome of the data analysis process.

### Example Data Analysis Code:
```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df = pd.read_csv('unemployement_industry.csv')
X = df['Mar.2019'].values.reshape(-1, 1)
y = df['Mar.2020'].values.reshape(-1, 1)

imputer = SimpleImputer(strategy='mean')
X = imputer.fit_transform(y) 

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"@Mean_Squared_Error[{round(mse, 2)}]")

plt.figure(figsize=(10, 6))
plt.scatter(y_test, y_pred, color='blue', alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Actual Employment Level (March 2020)')
plt.ylabel('Predicted Employment Level (March 2020)')
plt.title('Actual vs Predicted Employment Levels')
plt.savefig('plot.png')
plt.close()
```

### Example Output:

**CoT Output:**
1.  **Analyze the Goal:** The objective is to build a linear regression model to predict March 2020 employment (`y`) using March 2019 data (`X`). The code is supposed to load data, handle missing values, split, train, and evaluate the model. I must find a single logic error that causes an interpreter crash.

2.  **Scrutinize Data Imputation:** I will focus on the data preparation, specifically the handling of missing values. The relevant lines are:
    ```python
    X = df['Mar.2019'].values.reshape(-1, 1)
    y = df['Mar.2020'].values.reshape(-1, 1)
    ...
    imputer = SimpleImputer(strategy='mean')
    X = imputer.fit_transform(y) 
    ```

3.  **Identify the Core Logical Flaw:** The line `X = imputer.fit_transform(y)` is incorrect. It's supposed to handle missing values in the feature set `X` (Mar.2019 data). Instead, it performs the imputation on the target variable `y` (Mar.2020 data) and then uses the result to completely overwrite the feature variable `X`.

4.  **Trace the Error's Consequences:**
    *   **State of `X`:** After this line, the `X` variable no longer holds the March 2019 data. It now holds a "cleaned" version of the March 2020 data, where any missing values have been replaced by the mean of that column.
    *   **State of `y`:** The original `y` variable, which was loaded from the `'Mar.2020'` column, remains untouched. It was used as a *source* for the imputer but was not itself modified.
    *   **The Critical Condition:** If the original `'Mar.2020'` column contained any `NaN` values, the `y` variable will still contain these `NaN`s.
    *   **The Crash Point:** The data is then split into `X_train`, `X_test`, `y_train`, and `y_test`. If `y` contains `NaN`s, `y_train` will also contain `NaN`s. When the code reaches `model.fit(X_train, y_train)`, it attempts to train the linear regression model. Scikit-learn's `LinearRegression` model cannot process `NaN` values in the target vector (`y_train`).

5.  **Determine the Error Message and Location:** The attempt to fit a model with `NaN`s in the target variable will cause the interpreter to throw an error.
    *   **Cause Line:** `X = imputer.fit_transform(y)` is the logical error that initiates the faulty data state.
    *   **Effect Line:** `model.fit(X_train, y_train)` is where the program will crash because `y_train` contains illegal values.
    *   **Error Message:** The resulting error will be a `ValueError` indicating the presence of NaNs.

6.  **Final Conclusion:** The logic error is imputing the wrong variable and overwriting the features. This leads to the original target variable, potentially containing NaNs, being passed to the model's `fit` method, which triggers a `ValueError`.

**JSON Output:**
```json
{
    "cause_line": "X = imputer.fit_transform(y)",
    "effect_line": "model.fit(X_train, y_train)",
    "error_message": "ValueError: Input contains NaN, infinity or a value too large for dtype('float64')."
}
```
---
Now, apply this process to the following query and code. There will be only one error in the code. Output your CoT reasoning first, followed by ONLY ONE json output in your response.

**JSON Output:**
```json
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output your CoT reasoning first, followed by the one ONLY json output in your response.'''

RUBBER_DUCK_ONE_COT_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


You will be provided with an original query and a data analysis code. Your task is to:

1. Read the question carefully and identify if there are any logic error injected into the code.
2. For each logic error:
  - Locate the Cause: Specify the exact line of code that causes the issue.
  - Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
  - Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).

First, think step-by-step about the code and identify the logic error. Explain your reasoning process clearly. Follow the reasoning example in System Prompt.

After presenting your CoT reasoning, output the answer in the following JSON format. Ensure you provide both the CoT reasoning and the JSON output in your response.

Output Format:

**CoT Output:**
Your step-by-step reasoning process here

**JSON Output:**
```json
{
    "cause_line": "Specify the exact line of code causing the issue",
    "effect_line": "Specify the exact line of code where the error will be triggered",
    "error_message": "Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback)"
}
```

There will be only one error in the code. Output your CoT reasoning first, followed by the one ONLY json output in your response.
'''

RUBBER_DUCK_SELF_REFINE_SYSTEM_PROMPT = '''You are an expert AI assistant for Python code debugging in data science. Your task is to identify a single logic error in a provided code snippet.

You will operate in one of two modes, as specified by the user prompt: "Initial Analysis Mode" or "Refinement Mode".

**In both modes, your core task is to:**
1.  Read the user's query and the code carefully.
2.  Locate the Cause: Specify the exact line of code that causes the issue.
3.  Locate the Effect: Identify the line of code where the error will be triggered and the interpreter will throw an error.
4.  Error Description: Provide a concise description of the error message thrown by the Python Interpreter (not the full traceback).

**Your process should always be:**
First, think step-by-step about the code. Explain your reasoning process clearly in a "CoT Output" section.
After presenting your CoT reasoning, output the final answer in the specified JSON format.

**If the user prompt asks you to perform an "Initial Analysis":**
-   Provide your best first-pass diagnosis based on your reasoning.

**If the user prompt asks you to perform a "Refinement":**
-   You will be given a preliminary analysis. Your task is to critically review it, identify any flaws, and provide a final, corrected diagnosis. Your new CoT should reflect this refinement process.

Always output your CoT reasoning first, followed by one single JSON output in your response.
```

There will be only one error in the code. Output your CoT reasoning first, followed by the one ONLY json output in your response.'''

RUBBER_DUCK_SELF_REFINE_USER_PROMPT_STEP_1 = '''**Initial Analysis**

You are given the query and data analysis code.
### Original Query:
{{query}}


### Data Analysis Code:
{{code}}

You have been provided with an original query and a data analysis code. Your task is to perform a preliminary analysis and identify a potential logic error.

1. Read the code and the query carefully.
2. Think step-by-step to trace the code's logic and data flow.
3. Based on your reasoning, identify the likely cause of the error, the line where it would manifest, and the potential error message.

First, provide your step-by-step reasoning in a "CoT Output" section.
Then, provide your preliminary diagnosis in a "JSON Output" section.

This is your first pass, so focus on identifying the most probable issue.

**CoT Output:**
Your step-by-step reasoning process here.

**JSON Output:**
```json
{
    "cause_line": "Specify the likely line of code causing the issue",
    "effect_line": "Specify the likely line of code where the error will be triggered",
    "error_message": "Provide a concise description of the likely error message"
}
```
'''

RUBBER_DUCK_SELF_REFINE_USER_PROMPT_STEP_2 = '''**Refinement**

You are an expert code debugger. You will be given an original query, a data analysis code, and a preliminary analysis performed by another AI assistant.

Your task is to critically review the preliminary analysis and provide a final, definitive answer.

Here is the context:

**Original Query:**
{{query}}

**Buggy Code:**
```python
{{code}}
```

**Preliminary Analysis (from another AI):**
**CoT Output:**
{{initial_cot_output}}

**JSON Output:**
```json
{{initial_json_output}}
```

---

**Your Task:**

1.  **Critically review the preliminary analysis.** Does the reasoning make sense? Are there any logical gaps or alternative explanations that were missed? Is the identified cause truly the root cause?
2.  **Perform your own, more thorough step-by-step reasoning.** Build upon the preliminary analysis, correcting any mistakes you find.
3.  **Provide the final, corrected answer** in the specified JSON format. Your answer should be definitive and accurate.

First, output your new, refined step-by-step reasoning.
Then, output the final, corrected JSON.

**Refined CoT Output:**
Your new, more thorough step-by-step reasoning here.

**Final JSON Output:**
```json
{
    "cause_line": "Specify the definitive line of code causing the issue",
    "effect_line": "Specify the definitive line of code where the error will be triggered",
    "error_message": "Provide the definitive and concise error message"
}
```
'''