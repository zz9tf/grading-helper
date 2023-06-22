import requests, os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pandas as pd
from seleniumwire import webdriver
import sys

load_dotenv()

class grading_helper:
    def __init__(self) -> None:
        self.df_course_course_block = None
        self.df_course_students = pd.DataFrame(columns=['course', 'student'])
        self.df_student_not_in = pd.DataFrame(columns=['student', 'course', 'course block'])
        self.df_course_details = pd.DataFrame(columns=['course block', 'problem set', 'problem', 'status (NotFinish/NeedGrad/Finished)'])
        self.not_finished_student = pd.DataFrame(columns=['student', 'course', 'course block', 'problem Set', 'problem'])
        self.course_df = {'course':{('probSet Name', 'probSet url'): 'DataFrame'}}

    def load_basic_info(self):
        # Load related links for the courses
        tracking_list = []
        with open('trackingList.txt', 'r') as f:
            for line in f.readlines():
                line = line.split(',')
                course = line[1].strip()
                url = line[0].strip()
                tracking_list.append({'course': course, 'url': url})
        self.df_course_course_block = pd.DataFrame(tracking_list)
        
        # Load students for the courses
        for course in self.df_course_course_block['course'].unique():
            # Open the corresponding email list file
            with open(course + '.txt', 'r') as email_f:
                self.df_course_students = pd.concat([
                    self.df_course_students,
                    pd.DataFrame([(course, row.strip()) for row in email_f.readlines()], columns=['course', 'student'])
                ], ignore_index=True)

    def get_student_not_in_course(self):
        df_student_not_in = {
            'course': [],
            'course block': [],
            'student': []
        }
        self.df_student_not_in['course'] = self.df_course_course_block['course']
        for i, row in self.df_course_course_block.iterrows():
            # Search which student is not in this course
            url = row['url']
            course = row['course']
            students = self.df_course_students['student'][self.df_course_students['course'] == row['course']]
            course_block_name, not_in_students = self.search_student_not_in_course(url, students)
            df_student_not_in['student'] += not_in_students
            df_student_not_in['course block'] += len(not_in_students)*[course_block_name]
            df_student_not_in['course'] += len(not_in_students)*[course]
        
        self.df_student_not_in = pd.DataFrame(df_student_not_in)

    def search_student_not_in_course(self, url, emails):
        PREFIX = "https://mastery.cs.brandeis.edu/showTheStudentInfo/summary/"
        url = PREFIX + url.split('/')[-1]
        content = self.get_website_content(url)
        soup = BeautifulSoup(content, 'html.parser')
        rows = soup.find('tbody').find_all('tr')
        
        # Iterate over each row and extract the email information
        all_emails = []
        for row in rows:
            email_cell = row.find_all('td')[1]  # Assuming email is always the second cell
            email = email_cell.get_text(strip=True)
            all_emails.append(email)
        not_in_students = [email for email in emails if email not in all_emails]
        
        course_name = soup.find('h1', class_="pb-2 border-bottom").text.strip()[17:]
        return course_name, not_in_students
    
    def get_website_content(self, url):
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

    def interceptor(self, request):
        request.headers['Cookie'] = os.getenv('COOKIE')
            
    def get_problem_details(self):
        course_details = {
            'course block':[], 
            'problem set': [],
            'problem': [],
            'status (NotFinish/NeedGrad/Finished)': []
        }
        
        not_finished_student = {
            'student': [], 
            'course': [], 
            'course block':[], 
            'problem set': [],
            'problem': []
        }
        
        self.course_df = {}
        for i, row in self.df_course_course_block.iterrows():
            course = row['course']
            url = row['url']
            students = self.df_course_students.loc[self.df_course_students['course'] == course, 'student']
            self.course_df[course] = {}
            
            # Search one tracking webpage
            block_title, problem_set_urls = self.search_grading_questions(url)
            for problem_set in problem_set_urls:
                problem_set_title, df_one_problem_set = self.search_not_grading_answers(problem_set['url'], students)
                self.course_df[course][(problem_set_title, problem_set['url'])] = df_one_problem_set
                for col in df_one_problem_set.columns:
                    if "P" != col[0]: continue
                    not_finished = sum(df_one_problem_set[col] == "+")
                    need_grading = sum(df_one_problem_set[col].str.startswith("No TA reviews yet"))
                    finished_grading = len(df_one_problem_set[col]) - not_finished - need_grading
                    # fill course details to dict
                    course_details['course block'].append(block_title)
                    course_details['problem set'].append(problem_set_title)
                    course_details['problem'].append(col)
                    course_details['status (NotFinish/NeedGrad/Finished)'].append(f'{not_finished}:{need_grading}:{finished_grading}')

                    not_finished_student['student'] += df_one_problem_set['Student'][df_one_problem_set[col] == "+"].to_list()
                    not_finished_student['course'] += len(df_one_problem_set['Student'][df_one_problem_set[col] == "+"])*[course]
                    not_finished_student['course block'] += len(df_one_problem_set['Student'][df_one_problem_set[col] == "+"])*[block_title]
                    not_finished_student['problem set'] += len(df_one_problem_set['Student'][df_one_problem_set[col] == "+"])*[problem_set_title]
                    not_finished_student['problem'] += len(df_one_problem_set['Student'][df_one_problem_set[col] == "+"])*[col]
                    
                
        self.df_course_details = pd.DataFrame(course_details)
        self.not_finished_student = pd.DataFrame(not_finished_student)

    def search_grading_questions(self, url):
        content = self.get_website_content(url)
        soup = BeautifulSoup(content, 'html.parser')
        problem_sets_heading = soup.find('b', string='Problem Sets')
        q_elements = problem_sets_heading.find_next('ul').find_all('li')
        q_list = []

        for q in q_elements:
            q_title = q.text.strip().split('\n')[0].strip()
            q_url = "https://mastery.cs.brandeis.edu/gradeProblemSet/" + q.find('a').get('href').strip().split('/')[-1]
            q_list.append({'title': q_title, 'url': q_url})
            
        block_title = soup.find('h1', {"class": "pb-2 border-bottom"}).text.strip()
        
        return block_title, q_list

    def search_not_grading_answers(self, url, emails):
        content = self.get_website_content(url)
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
            if len(row) == 0 \
                or not row[0].text.strip().isnumeric() \
                or not emails.str.contains(row[1].text.strip()).any(): 
                continue
            for cell in row:
                cell_content = cell.text.strip()
                if cell_content == 'No TA reviews yet':
                    link = cell.find('a').get('href')
                    cell_content = cell.text.strip() + ':' + link
                cells.append(cell_content)
            
            # Add the row to the data list
            data.append(cells)
        
        # Create a DataFrame from the extracted data
        df = pd.DataFrame(data, columns=headers)
        columns = [col for col in df.columns if col == 'Student' or col.startswith('P')]
        df = df[columns]
        
        problem_set_title = soup.find('h1', {'class': 'pb-2 border-bottom'}).text.strip()
        
        return problem_set_title, df

    def go_over_one_question(self, base_url, df):
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
                print("  {} done.".format(col))
                continue
            else:
                print("Question: " + col)
                print(">> {} students have been graded.".format(finished_grading))
                print(">> {} students need to be graded.".format(sum(need_grading)))
                print(">> {} students haven't finished this question yet.".format(sum(not_finished)))
            if sum(need_grading) == 0: continue
            # Create a new instance of the Chrome driver
            driver = webdriver.Chrome()
            driver.request_interceptor = self.interceptor
            driver.execute_script(f'window.open("{base_url}","_blank");')
            for cell in df[col][need_grading]:
                url = 'https://mastery.cs.brandeis.edu' + cell.split(':')[1]
                # Open each URL in the list
                print(url)
                driver.execute_script(f'window.open("{url}","_blank");')
            input()
            driver.quit()

    def print_course_summary(self):
        format_style = '{:^30} | {:^30} | {:^10} | {:^10}'
        print(format_style.format('course block', 'problem set', 'problem', 'status (NotFinish:NeedGrad:Finished)'))
        print('-'*106)
        
        details = self.df_course_details.groupby(['course block', 'problem set'])
        prev_group_name = None
        for group_name, group_data in details:
            if group_name[0] == prev_group_name:
                course = ''
            else:
                if prev_group_name != None:
                    print('-'*106)
                prev_group_name = group_name[0]
                course = group_name[0]
            
            group_data = group_data.reset_index(drop=True)
            print(format_style.format(
                course[:28], 
                group_name[1][:28], 
                group_data.loc[0, 'problem'], 
                group_data.loc[0, 'status (NotFinish/NeedGrad/Finished)']))
            for row_id in range(1, len(group_data)):
                print(format_style.format(
                    '', 
                    '', 
                    group_data.loc[row_id, 'problem'], 
                    group_data.loc[row_id, 'status (NotFinish/NeedGrad/Finished)']))

    def print_not_in_student(self):
        format_style = '{:^8} | {:^30} | {:^30} '
        print(format_style.format('course', 'block', 'student'))
        
        details = self.df_student_not_in.groupby(['course', 'course block'])
        prev_group_name = [None]*2
        for group_name, group_data in details:
            course = '' if group_name[0] == prev_group_name[0] else group_name[0]
            block = '' if group_name[1] == prev_group_name[1] else group_name[1]
            
            prev_group_name = group_name
            
            group_data = group_data.reset_index(drop=True)
            print(format_style.format(
                course[:30], 
                block[:30], 
                group_data.loc[0, 'student']))
            
            for row_id in range(1, len(group_data)):
                print(format_style.format(
                    '', 
                    '', 
                    group_data.loc[row_id, 'student']))
            print('-'*106)
             
    def print_not_finished_student(self):
        format_style = '{:^8} | {:^30} | {:^20} | {:^20} | {:^20}'
        print(format_style.format('course', 'course block', 'problem set', 'problem', 'student'))
        
        details = self.not_finished_student.groupby(['course', 'course block', 'problem set', 'problem'])
        prev_group_name = [None]*4
        for group_name, group_data in details:
            course = '' if group_name[0] == prev_group_name[0] else group_name[0]
            block = '' if group_name[1] == prev_group_name[1] else group_name[1]
            probSet = '' if group_name[2] == prev_group_name[2] else group_name[2]
            problem = '' if group_name[3] == prev_group_name[3] else group_name[3]
            
            prev_group_name = group_name
            
            group_data = group_data.reset_index(drop=True)
            print(format_style.format(
                course, 
                block[:30],
                probSet[:20], 
                problem[:20],
                group_data.loc[0, 'student']))
            
            for row_id in range(1, len(group_data)):
                print(format_style.format(
                    '', 
                    '', 
                    '',  
                    '', 
                    group_data.loc[row_id, 'student']))
            print('-'*106)
   
    def interface(self):
        while True:
            header = "Mastery TA helper:\n" +\
                    "1. Course info summary\n" +\
                    "2. Student not in class\n" +\
                    "3. Student didn't finished their homework\n" +\
                    "4. Grading\n" +\
                    "5. quit"
            
            print(header)
            try:
                select = int(input("What are you going to do(please input a number from 1 to 5):\n"))
                if select == 1:
                    self.print_course_summary()
                
                elif select == 2:
                    print()
                    print(self.df_student_not_in.groupby(['student']).size()
                        .reset_index(name='count').sort_values(by='count', ascending=False, ignore_index=True))
                    print()
                    self.print_not_in_student()
                    
                elif select == 3:
                    print(self.not_finished_student.groupby(['student']).size()
                        .reset_index(name='count').sort_values(by='count', ascending=False, ignore_index=True))
                    print()
                    self.print_not_finished_student()
                
                elif select == 4:
                    print('Start grading:')
                    for course_block, probSets in self.course_df.items():
                        for probSet, df in probSets.items():
                            self.go_over_one_question(probSet[1], df)
                    sys.stdin.flush()
                    sys.stdin.readline()
                
                elif select == 5:
                    print('bye ~')
                else:
                    print("please input a number from 1 to 5")
            except:
                print("please input a number from 1 to 5")
            
            if select == 5:
                exit()
            
            print()
            print('*'*106)
            print()
        
        
        
        

def main():
    print('Loading...')
    g = grading_helper()
    g.load_basic_info()
    g.get_student_not_in_course()
    g.get_problem_details()
    g.interface()

main()