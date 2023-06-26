# Grading Process Monitoring

This project is designed to monitor the grading process for Mastery courses as a TA. It includes scripts that scrape data from a website, analyze the grading progress, and perform actions based on the progress.

## Author

- [Zheng Zheng](https://github.com/zz9tf)

## Requirements

- Python 3.6 or higher
- Requests library
- BeautifulSoup library
- Pandas library
- SeleniumWire library
- ChromeDriver

## Installation

1. Clone the project repository:

   ```
   git clone https://github.com/your_username/grading-process-monitoring.git
   ```
2. Install the required Python packages with Python > 3.6:
    ```
    pip install -r requirements.txt
    ```

3. Download and install ChromeDriver from the official website: [ChromeDriver Downloads](https://sites.google.com/chromium.org/driver/?pli=1)

4. Set up environment variables:
    - Create a .env file in the project directory.
    - Add the following line to the .env file, replacing <cookie_value> with the actual cookie value after you login Mastery:
    ```
    COOKIE=<cookie_value>
    ```
    
    PS: You can find this with google inspect. It should be at network and find some response sources with request url like 'https://mastery.cs.brandeis.edu/something/else'. Copy and paste your cookie from the request headers to your local .env file. Sometimes, cookie may get expired, you need to refresh it when you start to use it each time.
    
## Usage
1. Modify a file called trackingList.txt in the project directory. Each line in the file represents a tracking webpage and its corresponding email list file.

   - The format of each line should be: <tracking_webpage_url>, <email_list_file_name>  
    
     Example:

     ```
     https://mastery.cs.brandeis.edu/trackingPage1, emailsList2
     https://mastery.cs.brandeis.edu/trackingPage2, emailsList1
     ```

     PS: if you save all students' emails in a file called 10a.txt, then it should be: '<tracking_webpage_url>, 10a'
     
     PS2: if you want to ask python script not to track some urls, you can add '#' at the front of them to comment them, ie. `# https://mastery.cs.brandeis.edu/trackingPage1, emailsList2`
  
2. Create email list files for each course. Each email list file should contain one email address per line. ie: [courseName.txt](https://github.com/zz9tf/grading-helper/blob/main/courseName.txt)
3. Run the main script "grading.py" to do the grading process:
    ```
    python grading.py
    ```
    The script will go over each tracking webpage and perform the following tasks:

      <img width="89" alt="image" src="https://github.com/zz9tf/grading-helper/assets/77183284/5154aca9-d1b6-4c89-8185-33f37861a5ed">
      
      After waiting for a while, you will have menu:

      <img width="430" alt="image" src="https://github.com/zz9tf/grading-helper/assets/77183284/a9f7332e-66aa-494e-b16f-b151d752bb34">
      
      - Search for students who are not in the course.
      - Search for grading questions and retrieve their URLs.
      - Analyze the grading progress for each question and open the ungraded answers in a new Chrome window.
      ![image](https://github.com/zz9tf/grading-helper/assets/77183284/78670940-8a95-4133-8eb7-41a9085a2b4d)
    The script will display information about the grading progress and open the ungraded answers for each question. You can manually grade the answers in the Chrome window.

## Contributing
Contributions to this project are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License
This project is licensed under the [MIT License](https://github.com/zz9tf/grading-helper/blob/main/LICENSE).
