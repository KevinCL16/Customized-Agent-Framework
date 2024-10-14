INITIAL_SYSTEM_PROMPT = '''You will be provided with an original query and a correct data analysis code. Your task is to:

1. Choose one **common error type** from the list below and **inject it into the provided code**. Only one type of error should be injected at a time.
2. **Generate the modified code** with the injected error.
3. **Explain** the injected error type, including:
   - **Error Type**: A brief description of the injected error type.
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
  "injected_code": "Provide the complete modified code with the injected error",
  "error_analysis": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
}
'''

INITIAL_USER_PROMPT = '''You are provided with an **original query** as well as a **correct data analysis code**. Follow the steps outlined in the system prompt to inject a common error from the list provided. 

### Original Query:
{{query}}


### Correct Data Analysis Code:
{{code}}


### Your Task:
1. Choose one common error type from the list given in the system prompt and inject it into the provided code. Inject **only one error** at a time.
2. Generate the **modified code** with the injected error.
3. Provide an **error analysis** of the injected error.

### Expected Output:
The expected output format is given below:
```json
{
  "injected_code": "Provide the complete modified code with the injected error",
  "error_analysis": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
}
```

Use this format to provide your response, ensuring a clear explanation of the injected error, its type, and the expected outcome..
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