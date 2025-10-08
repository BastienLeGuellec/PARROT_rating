# MetaRate: A Streamlit App for Rating Radiology Reports

This project is a Streamlit application designed for rating radiology reports. It allows multiple users to log in, rate reports for errors, and track their progress. The application is designed to be flexible, allowing different sets of reports to be assigned to different users.

## Features

*   **User Authentication:** Users can log in with a username and password.
*   **Session-based Report Rating:** Each user is presented with a specific set of reports to rate.
*   **Progress Tracking:** Users can see their progress, including the number of reports rated and the total number of reports assigned to them.
*   **Blind Rating:** The rater is not shown whether a report is an original or a modified version with an error, to ensure an unbiased rating.
*   **Admin Page:** An admin page is available to view user activity logs and the list of users.

## Installation

1.  Clone the repository.
2.  Install the required Python packages using pip:

    ```
    pip install -r requirements.txt
    ```

## Usage

To run the application, use the following command:

```
streamlit run streamlit_app.py
```

## Data

The application uses the following files and directories:

*   `users.xlsx`: An Excel file containing user information, including usernames and passwords.
*   `user_report_mapping.json`: A JSON file that maps users to specific report files. This allows for different sets of reports to be assigned to different users.
*   `reports_u1u2.jsonl`, `reports_u3u4.jsonl`, etc.: JSONL files containing the reports to be rated. Each line in the file is a JSON object representing a single report.
*   `reports_with_laterality_errors.jsonl`, `reports_with_negation_errors.jsonl`: The source files containing the original reports and the reports with introduced errors.
*   `logs/`: This directory stores the action logs for each user. The logs are saved in Excel files named after the username (e.g., `user1_action_log.xlsx`).
*   `data/`: This directory contains the images associated with the reports, organized by case number.