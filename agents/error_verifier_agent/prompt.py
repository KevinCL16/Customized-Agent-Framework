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

RUBBER_DUCK_EVAL_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the Question carefully and identify if there are any logic errors injected into the code.  

2. For each logic error:  
   - **Locate the Error**: Specify the exact line of code where the error will cause an issue.  
   - **Error Details**: Provide the error message or traceback that would be generated when executing the code.  

### Output Format:
```json
{
    "error_line": "Specify the exact line of code where the error will occur",
    "error_message": "Provide the exact error message or traceback caused by this line"
}
```

Output only ONE json dict for each error.
'''

RUBBER_DUCK_EVAL_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query:
{{query}}


### Data Analysis Code:
{{code}}


1. Read the Question carefully and identify if there are any logic errors injected into the code.  

2. For each logic error:  
   - **Locate the Error**: Specify the exact line of code where the error will cause an issue.  
   - **Error Details**: Provide the error message or traceback that would be generated when executing the code.  

### Output Format:
```json
{
    "error_line": "Specify the exact line of code where the error will occur",
    "error_message": "Provide the exact error message or traceback caused by this line"
}
```

Output only ONE json dict for each error.
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

Evaluate the LLM Output against the Ground Truth separately for `error_line` and `error_message` based on the following criteria:

#### Evaluation Criteria:

1. **Error Line Matching (`error_line_score`)**:
   - **Score 1**: The `error_line` in the LLM Output exactly matches the `error_line` in the Ground Truth.
   - **Score 0**: The `error_line` in the LLM Output does not match the Ground Truth.

2. **Error Message Matching (`error_message_score`)**:
   - **Score 1**: The `error_message` in the LLM Output exactly matches the `error_message` in the Ground Truth.
   - **Score 0.5**: The `error_message` in the LLM Output is partially correct (e.g., captures the general idea but misses specific details or phrasing).
   - **Score 0**: The `error_message` in the LLM Output does not match the Ground Truth at all.

### Output Format:
```json
{
    "error_line_score": 1/0,
    "error_message_score": 1/0.5/0
}
```
'''