import requests, os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pandas as pd
from seleniumwire import webdriver

load_dotenv()

def get_website_content(url):
    try:
        headers = {
            'Cookie': os.getenv('COOKIE')
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open('view.html', 'wb') as f:
                f.write(response.content)
            return response.content
        else:
            print("Failed to retrieve website content. Status code:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("An error occurred:", e)

def search_student_not_in_course(url, emails):
    PREFIX = "https://mastery.cs.brandeis.edu/showTheStudentInfo/summary/"
    url = PREFIX + url.split('/')[-1]
    content = get_website_content(url)
    soup = BeautifulSoup(content, 'html.parser')
    rows = soup.find('tbody').find_all('tr')
    
    # Iterate over each row and extract the email information
    all_emails = []
    for row in rows:
        email_cell = row.find_all('td')[1]  # Assuming email is always the second cell
        email = email_cell.get_text(strip=True)
        all_emails.append(email)
    not_in_students = [email for email in emails if email not in all_emails]
    
    class_name = soup.find('h1', class_="pb-2 border-bottom").text.strip()[17:]
    print("{}: {} students haven't joined this class".format(class_name, len(not_in_students)))
    for student in not_in_students:
        print("  {}".format(student))

def search_grading_questions(url):
    content = get_website_content(url)
    soup = BeautifulSoup(content, 'html.parser')
    problem_sets_heading = soup.find('b', string='Problem Sets')
    q_elements = problem_sets_heading.find_next('ul').find_all('li')
    q_list = []

    for q in q_elements:
        q_title = q.text.strip().split('\n')[0].strip()
        q_url = "https://mastery.cs.brandeis.edu/gradeProblemSet/" + q.find('a').get('href').strip().split('/')[-1]
        q_list.append({'title': q_title, 'url': q_url})
    
    return q_list

def search_not_grading_answers(url):
    content = get_website_content(url)
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find(class_="table table-bordered table-striped")

    # Extract column names from the table header
    headers = [header.text.strip() for header in table.find_all('th')]
    # Create an empty list to store the rows of data
    data = []

    # Iterate over the table rows
    for row in table.find_all('tr'):
        # Extract cell values from each row
        cells = []
        row = row.find_all('td')
        if len(row) == 0 or not row[0].text.strip().isnumeric(): continue
        for cell in row:
            cell_content = cell.text.strip()
            if cell_content == 'No TA reviews yet':
                link = cell.find('a').get('href')
                cell_content = cell_content = cell.text.strip() + ':' + link
            cells.append(cell_content)

        # Add the row to the data list
        data.append(cells)

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(data, columns=headers)
    
    return df

def interceptor(request):
    request.headers['Cookie'] = os.getenv('COOKIE')

def go_over_one_question(base_url, df):
    # Go over all students answers for one question
    for col in df.columns:
        if "P" != col[0]: continue
        need_grading = df[col].str.startswith("No TA reviews yet")
        not_finished = df[col] == "+"
        finished_grading = len(df[col]) - sum(need_grading) - sum(not_finished)
        # All finished
        if sum(need_grading) == 0 and sum(not_finished) != 0:
            print("\nQuestion: " + col)
            print(">> {} students have been graded.".format(finished_grading))
            print(">> {} students need to be graded.".format(sum(need_grading)))
            print(">> {} students haven't finished this question yet.".format(sum(not_finished)))
            for student in df['Student'][not_finished]:
                print("    {}".format(student))
            continue
        elif sum(need_grading) == 0 and sum(not_finished) == 0:
            continue
        else:
            print("Question: " + col)
            print(">> {} students have been graded.".format(finished_grading))
            print(">> {} students need to be graded.".format(sum(need_grading)))
            print(">> {} students haven't finished this question yet.".format(sum(not_finished)))
        if sum(need_grading) == 0: continue
        # Create a new instance of the Chrome driver
        driver = webdriver.Chrome()
        driver.request_interceptor = interceptor
        driver.execute_script(f'window.open("{base_url}","_blank");')
        for cell in df[col][need_grading]:
            url = 'https://mastery.cs.brandeis.edu' + cell.split(':')[1]
            # Open each URL in the list
            print(url)
            driver.execute_script(f'window.open("{url}","_blank");')
        input()
        driver.quit()

def main():
    f =  open('trackingList.txt', 'r')

    # Go over all tracking webpages
    for line in f.readlines():
        line = line.split(',')
        url = line[0].strip()
        email_file = line[1].strip() + '.txt'
        # Open the corresponding email list file
        with open(email_file, 'r') as email_f:
            emails = [row.strip() for row in email_f.readlines()]
        
        # Search which student is not in this course
        search_student_not_in_course(url, emails)
        
        # Search one tracking webpage
        question_urls = search_grading_questions(url)
        for q_url in question_urls:
            print('\nYou are grading problem set: {}'.format(q_url['title']))
            df_for_one_question = search_not_grading_answers(q_url['url'])
            df_for_one_question = df_for_one_question[df_for_one_question['Student'].isin(emails)]
            go_over_one_question(q_url['url'], df_for_one_question)
        print()
        print('----------------------------------------------------------------')

    f.close()

    print("done")

main()