# **Workday Automation Tool**

Automate your job application process on Workday with this script! This tool streamlines filling out applications, saving time by leveraging intelligent workflows and configurable job lists.

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [How to Run](#how-to-run)
3. [System Architecture](#system-architecture)
4. [Contributing](#contributing)
5. [Future Improvements](#future-improvements)
6. [Support the project](#support-the-project)
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
Please be cognizant if user verification is required for the job you are applying to you have to do it manually and hit enter once you are done. Now as for the way it works: I'm using selenium to open the job url, then for each stage I get all of the required field questions, and their answer boxes. I'm using fuzzy search to try my best to match questions to a specific workflow be it select radio, handle multiselect, ect. If you come across an error, it's most likely that the question being asked is too different from any of ones present, and you will need to update the self.questionsToActions dictionary in workday.py to handle the new question. If you find any bugs, or have any suggestions, please feel free to fork the repo and make a pull request. I will happyly take a look into it and merge it in. Again this is a WIP and I have alot of ideas to make the User experience better, but I hope it saves you time applying to jobs!

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

## *Future Improvements**
   Enhanced User Experience: Improve the script's ability to adapt to new workflows dynamically possibly utilizing agents.
   CAPTCHA Automation: Research and implement solutions for automating CAPTCHA challenges.
   Detailed Logs: Add logging to provide more visibility into the process.
   Interactive UI: Create a graphical interface for easier configuration and execution.

## **Support the project**
If you find this script useful and want to support its development, consider donating using buy me a coffee  (https://buymeacoffee.com/healthIsWealth809 )
