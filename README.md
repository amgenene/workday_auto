# **Workday Automation Tool**

Automate your job application process on Workday with this script! This tool streamlines filling out applications, saving time by leveraging intelligent workflows and configurable job lists.

---

## **Table of Contents**

1. [Prerequisites](#prerequisites)
2. [How to Run](#how-to-run)
3. [System Architecture](#system-architecture)
4. [Contributing](#contributing)
5. [Future Improvements](#future-improvements)

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

Please be cognizant if user verification is required for the job you are applying to you have to do it manually and hit enter once you are done. Now as for the way it works: I'm using selenium to open the job url, then for each stage I get all of the required field questions, and their answer boxes. I'm using fuzzy search to try my best to match questions to a specific workflow be it select radio, handle multiselect, ect. If you come across an error, it's most likely that the question being asked is too different from any of ones present, and you will need to update the self.questionsToActions dictionary in workday.py to handle the new question. If you find any bugs, or have any suggestions, please feel free to fork the repo and make a pull request. I will happyly take a look into it and merge it in. Again this is a WIP and I have alot of ideas to make the User experience better, but I hope it saves you time applying to jobs!