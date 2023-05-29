from automated_selenium import BasePage
from automated_selenium import get_undetected_chrome_browser
from automated_selenium.resources.resources import Selector
from selenium.webdriver.common.by import By
from traitlets import Unicode, HasTraits, Any, default
from traitlets.config import Application
from bs4 import BeautifulSoup
from loguru import logger
from geopy.geocoders import Nominatim
import time
# import pandas as pd
# import polars as pl
from sqlalchemy.orm import Session

NOMINATUM_USER_NAME = "https://github.com/metaperl/fetlife-tools"


def am_logged_in(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    matching = soup.find_all(string="You are already signed in.")
    return len(matching)


def lat_long_of(city, state):
    time.sleep(1)
    geolocator = Nominatim(user_agent=NOMINATUM_USER_NAME)
    location = geolocator.geocode(f"{city} {state}")
    if location:
        return location.latitude, location.longitude
    else:
        return None


# class PlaceBase(HasTraits):
#     """Database of places"""
#
#     def places(self):
#         csv_file = csv.reader(open('uscities.csv', "r"))
#         return csv_file
#
#     def lat_long_of(self, city, state):
#
#         for row in self.places():
#             # if current rows 2nd value is equal to input, print that row
#             if city == row[0] and state == row[2]:
#                 logger.debug(f"found {row} for {city} and {state}")
#                 return row[6], row[7]
#         return None


class Place(HasTraits):
    name = Unicode()
    url = Unicode()
    lat_long = Any()

    def __str__(self):
        return f"{self.name} {self.url} {self.lat_long}"


class LoginResources:
    username_field = Selector(By.XPATH, "//input[@id='user_login']")
    password_field = Selector(By.XPATH, "//input[@id='user_password']")
    submit_button = Selector(By.XPATH, "//button[@type='submit']")


class MyPage(BasePage):
    def login(self, username: str, password: str):
        self.driver.get("https://fetlife.com/users/sign_in")

        if am_logged_in(self.driver.page_source):
            logger.debug("already logged in.")
            return

        logger.debug("Logging in...")
        # self.wait_until_find(LoginResources.username_field)

        # Find username field
        username_field = self.find(LoginResources.username_field)
        # Type username like human
        self.send_keys(username_field, username)

        # Find password field
        password_field = self.find(LoginResources.password_field)
        # Type password like human
        self.send_keys(password_field, password)

        # Find submit button
        submit_button = self.find(LoginResources.submit_button)
        # click on submit button
        self.click(submit_button)

        return self

    def load_places(self, region_url, region_state):
        self.driver.get(region_url)

        html_doc = self.driver.page_source

        soup = BeautifulSoup(html_doc, 'html.parser')

        main_tag = soup.find("main")

        import db
        from sqlalchemy_model import Place
        # TODO: add Indian Creek Village manually
        with Session(db.engine) as session:
            try:
                last_added = False  # city is not added to db
                for a in main_tag.find_all('a'):
                    if a.get('href').startswith('/p/'):
                        logger.debug(f"found place anchor {a}")
                        city = a.string
                        if not last_added:
                            if city == 'Indian Creek Village':
                                logger.debug("Found last added city. Will start populating database.")
                                last_added = True
                            continue
                        logger.debug(f'Populating database with {city}')
                        url = a.get('href')
                        lat_long = lat_long_of(city, region_state)
                        if lat_long:
                            session.add(Place(
                                city=city,
                                state=region_state,
                                url=url,
                                latitude=lat_long[0],
                                longitude=lat_long[1]
                            ))
                            session.commit()
                        else:
                            logger.info(f"Skipping {city} because it has no lat-long in database")
            except Exception as e:
                logger.info(f"An exception occurred: {e}. Let's save the session.")
                session.commit()


class App(Application):
    driver = Any()
    my_page = Any()
    region_url = Unicode("https://fetlife.com/p/united-states/florida/related").tag(config=True)
    region_state = Unicode("FL")
    my_city = Unicode("Pompano Beach")

    def load_places(self):
        self.my_page.load_places(self.region_url, self.region_state)

    def start(self):
        profile_name = 'my_profile'

        self.driver = get_undetected_chrome_browser(profile_name)
        self.my_page = MyPage(self.driver)

        import userpass
        self.my_page.login(userpass.username, userpass.password)
        self.load_places()


if __name__ == "__main__":
    App.launch_instance()
