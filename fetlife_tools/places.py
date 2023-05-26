from automated_selenium import BasePage
from automated_selenium import get_undetected_chrome_browser
from automated_selenium.resources.resources import Selector
from selenium.webdriver.common.by import By
from traitlets import Unicode, HasTraits, Any
from traitlets.config import Application
from bs4 import BeautifulSoup
from loguru import logger


def am_logged_in(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    matching = soup.find_all(string="You are already signed in.")
    return len(matching)


class Place(HasTraits):
    name = Unicode()
    url = Unicode()

    def __str__(self):
        return f"{self.name} {self.url}"


class LoginResources:
    # your resources as follow
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

        # Return self if you want to chain your actions as follow.
        # login_page = LoginPage(driver)
        # login_page.check_login()\
        #           .login()\
        return self

    def places(self, region_url):
        self.driver.get(region_url)

        html_doc = self.driver.page_source

        soup = BeautifulSoup(html_doc, 'html.parser')

        result = list()

        main_tag = soup.find("main")

        for a in main_tag.find_all('a'):
            if a.get('href').startswith('/p/'):
                logger.debug(f"found place anchor {a}")
                result.append(Place(name=a.string, url=a.get('href')))

        return result


class App(Application):
    driver = Any()
    my_page = Any()
    region_url = Unicode("https://fetlife.com/p/united-states/florida/related").tag(config=True)
    region_code = Unicode("FL")
    my_city = Unicode("Pompano Beach")

    def places_near_me(self):
        places = self.my_page.places(self.region_url)
        logger.debug("places = {}".format([str(p) for p in places]))

    def start(self):
        profile_name = 'my_profile'

        self.driver = get_undetected_chrome_browser(profile_name)
        self.my_page = MyPage(self.driver)

        import userpass
        self.my_page.login(userpass.username, userpass.password)
        self.places_near_me()


if __name__ == "__main__":
    App.launch_instance()
