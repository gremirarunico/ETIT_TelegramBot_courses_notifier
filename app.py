import asyncio
import json
import hashlib
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

class App():
    def __init__(self, json_data_file, tg):
        try:
            with open(json_data_file, 'r') as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.decoder.JSONDecodeError) as error:
            with open(json_data_file, 'w') as json_file:
                courses = self.get_courses()
                data = {"courses_hash":self.compute_courses_hash(courses),"courses":courses}
                json.dump(data, json_file, indent=4)

        self.data = data
        self.telegram = tg
        self.json_data_file = json_data_file

    async def start(self):
        #await self.remember_courses()
        asyncio.create_task(self.schedule_task_everyday(7, 0, self.remember_courses))
        asyncio.create_task(self.forever_loop())

    async def remember_courses(self):
        message = ""
        today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        for course in self.data["courses"]:
            # For a single day course
            if not course["is_multy_day"]:
                date_string = course["date"]
                date = datetime.strptime(date_string, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)

                # Event is tomorrow
                if (date - today) == timedelta(days=1):
                    message += f"• TOMORROW: [{course["title"]}]({course["link"]})\n"
                # Event is today
                elif (date == today):
                    message += f"• TODAY: [{course["title"]}]({course["link"]})\n"
            # multiday course
            else:
                begin_date = datetime.strptime(course["date_from"], "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime.strptime(course["date_to"], "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
                # Multiday course start tomorrow
                if (begin_date - today) == timedelta(days=1):
                    message += f"• TOMORROW: [{course["title"]}]({course["link"]}) multiday to {course["date_to"]}\n"
                # Start today
                elif (begin_date - today) == timedelta(days=0):
                    message += f"• TODAY: [{course["title"]}]({course["link"]}) multiday to {course["date_to"]}\n"
                # Multiday course last day
                elif((end_date-today) == timedelta(days=0)):
                    message += f"• TODAY: [{course["title"]}]({course["link"]}) multiday course last day!\n"
                # Between days
                elif(begin_date < today < end_date):
                    message += f"• TODAY: [{course["title"]}]({course["link"]}) multiday course between {course["date_from"]} and {course["date_to"]}, please check if today there is a course!\n"
        # If something put header
        if message != "":
            message = "SCHEDULED COURSE in ETIT\n" + message
            await self.telegram.message_send_all_chats(message)

    async def forever_loop(self):
        while True:
            course_changed = self.are_courses_changed()
            #print(f"The course are changed?: {course_changed}")
            if course_changed:
                courses = self.get_courses()
                #print(courses)
                self.data['courses_hash'] = self.compute_courses_hash(courses)
                self.data['courses'] = courses
                self.updateJson()
                await self.courses_notify(courses)
            await asyncio.sleep(60*60)

    async def courses_notify(self, courses):
        message = f"""UPDATE in ETIT [calendar](https://phd.unibo.it/etit/en/agenda)
Founded {len(courses)} activities:\n"""
        for course in courses:
            message += f"• [{course["title"]}]({course["link"]}) "
            message += f"on {str(course["date"])}" if not course["is_multy_day"] else f"from {course["date_from"]} to {course["date_to"]}"
            message += "\n"
                             
        await self.telegram.message_send_all_chats(message)

    async def schedule_task_everyday(self, hour, minute, my_function):
        while True:
            now = datetime.now()
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now > target_time:
                target_time += timedelta(days=1)
            
            wait_time = (target_time - now).total_seconds()
            await asyncio.sleep(wait_time)
            await my_function()
            await asyncio.sleep(61)  # Sleep to ensure it doesn't run multiple times in the same minute

    def are_courses_changed(self):
        courses = self.get_courses()
        actual_hash = self.compute_courses_hash(courses)
        if(actual_hash == self.data['courses_hash']):
            return False
        else:
            return True

    def compute_courses_hash(self, valid_courses):
        json_courses = json.dumps(valid_courses)
        courses_hash = hashlib.sha256(json_courses.encode()).hexdigest()
        return(courses_hash)
    
    def get_courses(self):
        url = "https://phd.unibo.it/etit/en/agenda"

        date_format = '%d %B %Y'


        page_html = requests.get(url).text
        page_soup = BeautifulSoup(page_html, 'html.parser')
        courses_soup = page_soup.findAll(attrs={"data-umc":"agendalist"})

        future_courses = []
        for course_soup in courses_soup:
            #print(course_soup)
            a_tag_class = course_soup.get('class')
            # If current ourse and not archived
            if not ('archived' in a_tag_class):
                date_range = course_soup.find(attrs={"class":"date"}).get("class")
                if('range' in date_range):
                    is_multi_day = True

                    date_from = course_soup.find(attrs={"class":"from"}).text
                    date_from_d_m_y = date_from.split(' ')
                    date_to = course_soup.find(attrs={"class":"to"}).text
                    date_to_d_m_y = date_to.split(' ')

                    # Check it's empty
                    for i in range(3):
                        if date_from_d_m_y[i] == '':
                            date_from_d_m_y[i] = date_to_d_m_y[i]
                        if date_from_d_m_y[i] == '':
                            print("ERROR")
                    
                    date_from = datetime.strptime(' '.join(date_from_d_m_y), date_format)
                    date_to = datetime.strptime(' '.join(date_to_d_m_y), date_format)

                    date_from = str(date_from).split(' ')[0]
                    date_to = str(date_to).split(' ')[0]
                else:
                    is_multi_day = False

                    date_text = course_soup.find(attrs={"class":"date"}).text
                    date_text = date_text.strip()
                    date = datetime.strptime(date_text, date_format)
                    date = str(date).split(' ')[0]

                category = course_soup.find(attrs={"class":"category"}).text
                title = course_soup.find("h3").text
                position = course_soup.find(attrs={"class":"where"}).text
                link = course_soup.get('href')
                future_courses.append({"is_multy_day":is_multi_day,
                                    "date":("" if is_multi_day else date),
                                    "date_from":(date_from if is_multi_day else ""),
                                    "date_to":(date_to if is_multi_day else ""),
                                    "title":title,
                                    "position":position,
                                    "link":link,
                                    "category":category})
        return(future_courses)
    
    def updateJson(self):
        with open(self.json_data_file, 'w') as json_file:
            json.dump(self.data, json_file, indent=4)