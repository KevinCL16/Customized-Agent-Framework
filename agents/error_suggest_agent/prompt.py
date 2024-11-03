INITIAL_SYSTEM_PROMPT = '''You will receive three components:  
1. **Original Query**: A user query that contain specific **concepts** related to data analysis.  
2. **Correct Data Analysis Code**: A working code snippet designed to analyze the data according to the original query.  
3. **CSV Information**: Details about the structure, content, and sample data from the CSV file being analyzed.

Your task is to:
1. **Identify potential data analysis error types** for each concept mentioned in the **original query**, considering the code and CSV information provided. Give at least **three error types** that are commonly associated with each mentioned concept and **have a real possibility of occuring** within the query and data analysis code.

2. **Explain** why these errors could occur, based on the characteristics of the data (e.g., missing values, incorrect data types, or structural inconsistencies) and how the code addresses or overlooks these issues.

3. **Describe the impact** of each error on the expected outcome, including performance, accuracy, or interpretability.


Return your output in the following **JSON format**:

```json
{
  "concept": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  "concept": {
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  
  ......

}
'''

INITIAL_USER_PROMPT = '''### Original Query:
{{query}}


### Correct Data Analysis Code:
{{code}}


### CSV Information
{{csv_info}}

### Concepts
{{concepts}}



### Expected Output:
The expected output format is given below:
```json
{
  "concept_1": [{
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }],
  "concept_2": [{
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
  ],

  ......

}
```
'''

ERROR_PROMPT = '''There are some errors in the code you gave:
{{error_message}}
please correct the errors.
Then give the complete code and don't omit anything even though you have given it in the above code.'''

LOGICAL_SYSTEM_PROMPT = '''You will receive three components:  
1. **Original Query**: A user query that contain specific **concepts** related to data analysis.  
2. **Correct Data Analysis Code**: A working code snippet designed to analyze the data according to the original query.  
3. **CSV Information**: Details about the structure, content, and sample data from the CSV file being analyzed.

Your task is to:
1. **Add hard-to-find logical errors into the correct code** for each concept mentioned in the **original query**, considering the code and CSV information provided. DO NOT point out errors in the code, the code produces correct answers and therefore is deemed ground truth. Must add new hidden errors that are hard to find.
 Inject at least **three errors** that are possible to occur with each mentioned concept and have a real possibility of occuring within the query and data analysis code.
  Print the entire code.

2. **Explain** why these errors occurred and how the code addresses or overlooks these issues.

3. **Describe the impact** of each error on the expected outcome, including performance, accuracy, or interpretability.


Return your output in the following **JSON format**:

```json
{
  "concept_1": [{
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }],
  "concept_2": [{
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  {
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  }
  ],

  ......

}
```
'''

LOGICAL_USER_PROMPT = '''### Original Query:
{{query}}


### Correct Data Analysis Code:
{{code}}


### CSV Information
{{csv_info}}

### Concepts
{{concepts}}



### Expected Output:
The expected output format is given below:
```json
{
  "concept": {
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },
  "concept": {
    "error_code": "Print the entire code with injected error",
    "error_type": "Specify the type of injected error",
    "explanation": "Describe why this is an error and its impact on the analysis",
    "expected_outcome": "Explain how this error will affect model performance, accuracy, or interpretability"
  },

  ......

}
```
'''

