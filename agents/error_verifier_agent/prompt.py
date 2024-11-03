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


INITIAL_SYSTEM_PROMPT = '''You will be provided with an original query and a data analysis code. Your task is to:

1. Read the Question carefully, determine whether the code has followed the original query requirements, if so, further identify any errors in its data analysis process. **If the code faithfully followed seemingly wrong data analysis practices explicitly stated in the Question. Deem it as correct.**
2. **Explain** the error, including:
   - **Explanation**: Explain why this is an error and what issues it may cause.
   - **Expected Outcome**: Explain how this error will affect the data analysis results, such as misleading outcomes, degraded performance, or incorrect interpretations.

### Output Format:
```json
{
  "is_error": "True or False",
  "error_explanation": [{
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  ......
  
  ]
}
```

# Note that not only one error could appear in the data analysis code, you should find all errors and list them in the json output.
'''

INITIAL_USER_PROMPT = '''You are given the following query and data analysis code.

### Original Query (Read the Question carefully, if the code followed the requirements in the question, even if you feel that incorrect data analysis practice were used, deem it as correct):
{{query}}


### Data Analysis Code:
{{code}}


### Your Task: 
1. Read the Question carefully, determine whether the code has followed the query requirements, if so, further identify any errors in its data analysis process. **If the code faithfully followed seemingly wrong data analysis practices explicitly stated in the original query. Deem it as correct. Such as using Linear regression to predict a binary outcome, because the original query asked us to do so!!!**
2. Explain the error, including:
   - **Explanation**: Why this is an error and what issues it may cause.
   - **Expected Outcome**: How this error will affect the analysis results, such as producing misleading conclusions or performance degradation.
   

Please follow the output format below:

```json
{
  "is_error": "True or False",
  "error_explanation": [{
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  ......
  
  ]
}
```

# Note that not only one error could appear in the data analysis code, you should find all errors and list them in the json output.
'''