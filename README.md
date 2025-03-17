# **Workday Automation Tool**

Automate your job application process on Workday with this script! This tool streamlines filling out applications, saving time by leveraging intelligent workflows and configurable job lists.

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [How to Run](#how-to-run)
3. [System Architecture](#system-architecture)
4. [Recent Improvements](#recent-improvements)
5. [Contributing](#contributing)
6. [Future Improvements](#future-improvements)
7. [Support the project](#support-the-project)
---

## **Prerequisites**

Before running the script, ensure you have the following installed and set up:

1. **Python (>=3.7)**  
   Download and install Python from [python.org](https://www.python.org/).

2. **Required Python Packages**  
   Install dependencies using the following command:
   ```bash
   pip install -r requirements.txt

3. **Fill in information in config/profile.yaml and config/jobs.txt**
    Make sure to fill in the required information in config/profile.yaml and list the job URLs in config/jobs.txt before running the script.

## **How to Run** 

To run the script, simply execute the following command:
```bash
python workday.py
```

inspired by https://github.com/raghuboosetty/workday

## **System Architecture**
This tool uses Selenium to automate job applications on Workday sites. The application workflow:

1. Opens the job URL and clicks the Apply button
2. Handles signup/signin based on whether you've applied to the company before
3. Uploads your resume
4. For each form page:
   - Identifies required fields and their associated input elements
   - Uses sentence embedding matching to determine the appropriate response for each question
   - Automatically fills in form fields with your predefined answers
   - Handles different input types (text, dropdown, radio buttons, checkboxes, etc.)
   - Moves to the next page until complete

If user verification is required, the program will pause and prompt you to complete verification manually.

## **Recent Improvements**

1. **Interactive Learning System**: Added an intelligent learning system that observes manual interactions when automation fails, records them, and applies the learned patterns to future questions.

2. **Smart Element Type Detection**: Automatically identifies form element types to better understand how to interact with them (text input, dropdown, radio button, etc.)

3. **Reduced StopWords**: Optimized the stopwords list to prevent removing important context from questions, improving matching accuracy.

4. **Improved Sentence Matching**: Switched from fuzzy string matching to sentence embedding comparison using the all-MiniLM-L6-v2 model, enabling more accurate mapping of questions to predefined answers.

5. **Enhanced Account Detection**: The tool now automatically detects when an email is already registered and switches to sign-in flow.

6. **More Robust DOM Traversal**: Improved the algorithm for finding related form elements by traversing the DOM structure more intelligently.

7. **Better Error Handling**: Added more robust error handling and interactive prompts for manual intervention when needed.

### **How the Learning System Works**

When the automation encounters a form field it can't automatically fill:

1. It asks you to fill the field manually
2. You enter what you filled in the field when prompted
3. The system records this interaction in `config/learned_interactions.json`
4. In future applications, the system will attempt to apply this learned mapping
5. After completing all applications, the tool suggests improvements based on what it learned

## **Contributing**
Contributions are welcome! If you encounter any bugs or have suggestions for improvement:

   1. Fork the repository.
   2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
   3. Make your changes and commit them:
   ```bash
   git commit -m "Description of changes"
   ```
   4. Push the changes to your fork:
   ```bash
      git push origin feature-name
   ```
   5. Submit a pull request.

## **Future Improvements**
   - **Complete Code Refactoring**: Finish implementing the modular architecture in the processing/ and browser/ directories
   - **Smart Question Classification**: Use machine learning to automatically categorize form fields without predefined mappings
   - **Resume Parsing**: Extract information from your resume to auto-populate more fields
   - **Browser Choice**: Add support for Firefox and other browsers
   - **Interactive UI**: Create a graphical interface for easier configuration and execution
   - **Local Data Storage**: Save application history and progress

## **Support the project**
If you find this script useful and want to support its development, consider donating using buy me a coffee  (https://buymeacoffee.com/healthIsWealth809 )
